from datetime import date, timedelta

from app.database import db
from app.models import Atendimento, Medico, Paciente, Procedimento


def _criar_atendimento(client, base, data, valor):
    with client.application.app_context():
        a = Atendimento(
            paciente_id=base["paciente_id"],
            medico_id=base["medico_id"],
            procedimento_id=base["procedimento_id"],
            data_atendimento=data,
            valor=valor,
            forma_pagamento="Pix",
        )
        db.session.add(a)
        db.session.commit()


def _base(client):
    with client.application.app_context():
        medico = Medico.query.first()
        proc = Procedimento.query.first()
        paciente = Paciente(nome="Dash Teste")
        db.session.add(paciente)
        db.session.commit()
        return {
            "medico_id": medico.id,
            "procedimento_id": proc.id,
            "paciente_id": paciente.id,
        }


def _card_valor(html, label):
    marker = f'stat-label">{label}</div>'
    i = html.find(marker)
    assert i != -1, f"card '{label}' não encontrado"
    seg = html[i:i + 200]
    valor = seg.split("stat-value", 1)[1].split(">", 1)[1].split("<", 1)[0]
    return valor.strip()


def _valor_total_oculto(html):
    # Valor exibido por padrão (asteriscos)
    marker = 'id="valor-total-oculto">'
    i = html.find(marker)
    assert i != -1, "valor total oculto não encontrado"
    return html[i:i + 60].split(">", 1)[1].split("<", 1)[0].strip()


def _valor_total_exibido(html):
    # Valor efetivo escondido (mostrado ao clicar no ícone)
    marker = 'id="valor-total-exibido" style="display:none">'
    i = html.find(marker)
    assert i != -1, "valor total exibido não encontrado"
    return html[i:i + 100].split(">", 1)[1].split("<", 1)[0].strip()


def test_dashboard_padrao_esta_todos(client):
    base = _base(client)
    hoje = date.today()
    _criar_atendimento(client, base, hoje, 100)
    # Atendimento antigo (fora da semana, mas conta em "todos")
    _criar_atendimento(client, base, hoje - timedelta(days=200), 900)

    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Todos os cards refletem o período (todos) por padrão
    assert _card_valor(html, "TOTAL DE ATENDIMENTOS") == "2"
    assert _valor_total_oculto(html) == "••••••"
    assert _valor_total_exibido(html) == "R$ 1.000,00"


def test_dashboard_filtros_periodo_afetam_cards(client):
    base = _base(client)
    hoje = date.today()

    # Atendimento de hoje
    _criar_atendimento(client, base, hoje, 100)

    # Atendimento futuro (não deve contar em nenhum período)
    _criar_atendimento(client, base, hoje + timedelta(days=30), 500)

    # Atendimento antigo (não deve contar em "hoje" nem "semana")
    _criar_atendimento(client, base, hoje - timedelta(days=200), 900)

    # Atendimento "ontem" para validar que "hoje" exclui dias anteriores
    _criar_atendimento(client, base, hoje - timedelta(days=1), 30)

    # "hoje": somente o atendimento de hoje conta em todos os cards
    res = client.get("/?periodo=hoje")
    html = res.get_data(as_text=True)
    assert _card_valor(html, "TOTAL DE ATENDIMENTOS") == "1"
    assert _valor_total_exibido(html) == "R$ 100,00"
    # Futuro (500) e antigos (900, 30) não aparecem no período "hoje"

    # "semana": hoje (100) e ontem (30) contam; futuro e muito antigo não
    res = client.get("/?periodo=semana")
    html = res.get_data(as_text=True)
    assert _card_valor(html, "TOTAL DE ATENDIMENTOS") == "2"
    assert _valor_total_exibido(html) == "R$ 130,00"

    # Período inválido cai no padrão (semana) e ainda renderiza
    res = client.get("/?periodo=invalido")
    assert res.status_code == 200


def test_dashboard_sem_atendimentos(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    # Sem atendimentos, todos os cards ficam zerados
    assert _card_valor(html, "TOTAL DE ATENDIMENTOS") == "0"
    assert _valor_total_oculto(html) == "••••••"
    assert _valor_total_exibido(html) == "R$ 0,00"


def test_dashboard_mes_anterior_e_ano(client):
    base = _base(client)
    hoje = date.today()

    # Atendimento de hoje
    _criar_atendimento(client, base, hoje, 100)

    # Atendimento no mês anterior: último dia do mês anterior
    fim_mes_ant = date(hoje.year, hoje.month, 1) - timedelta(days=1)
    _criar_atendimento(client, base, fim_mes_ant, 50)

    # Atendimento no ano corrente (ex.: início do ano)
    _criar_atendimento(client, base, date(hoje.year, 1, 15), 20)

    # "mes_anterior": apenas o atendimento do mês anterior conta
    res = client.get("/?periodo=mes_anterior")
    html = res.get_data(as_text=True)
    assert _card_valor(html, "TOTAL DE ATENDIMENTOS") == "1"
    assert _valor_total_exibido(html) == "R$ 50,00"

    # "ano": atendimentos de hoje, mês anterior e este ano contam; só exclui futuros/anteriores ao ano
    res = client.get("/?periodo=ano")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    # hoje(100) + mês anterior(50) + início do ano(20)
    assert _card_valor(html, "TOTAL DE ATENDIMENTOS") == "3"
    assert _valor_total_exibido(html) == "R$ 170,00"


def _serie_mensal(html):
    """Le o par (rotulo, valor) da serie mensal do grafico de linha."""
    import re

    # O template emite JSON via tojson dentro do grafico mensal:
    #   labels: ["01/2026", "02/2026"],   ...   data: [150.0, 200.0]
    bloco = re.search(
        r"labels:\s*(\[[^\]]*\d{2}/\d{4}[^\]]*\]).*?data:\s*(\[[^\]]*\])",
        html,
        re.S,
    )
    assert bloco, "serie mensal nao encontrada no HTML do dashboard"
    rotulos = re.findall(r"\d{2}/\d{4}", bloco.group(1))
    valores = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", bloco.group(2))]
    return dict(zip(rotulos, valores))


def test_dashboard_agrupa_mes_por_extract_nao_por_strftime(client):
    """O agrupamento mensal nao pode depender de funcao exclusiva do SQLite.

    strftime() nao existe no PostgreSQL. Usamos extract(), que o SQLAlchemy
    traduz para a sintaxe de cada banco. Este teste roda em SQLite, mas falha
    se alguem voltar a usar strftime, que so apareceria como erro em producao.
    """
    base = _base(client)
    _criar_atendimento(client, base, date(2026, 1, 10), 100)
    _criar_atendimento(client, base, date(2026, 1, 20), 50)
    _criar_atendimento(client, base, date(2026, 2, 5), 200)

    res = client.get("/?periodo=ano")
    html = res.get_data(as_text=True)
    assert res.status_code == 200

    serie = _serie_mensal(html)
    # Janeiro: 100 + 50 = 150, somados no mesmo mes.
    assert serie.get("01/2026") == 150.0
    assert serie.get("02/2026") == 200.0


def test_nenhuma_consulta_sql_usa_strftime():
    """strftime() e funcao de SQLite; numa consulta, quebra o PostgreSQL.

    O alerta vale para SQL, nao para Python: datetime.strftime() em codigo
    Python e portavel e aparece legitimamente em atendimentos.py e exportacao.
    """
    import pathlib

    raiz = pathlib.Path(__file__).resolve().parent.parent / "app"
    for arquivo in raiz.rglob("*.py"):
        codigo = arquivo.read_text(encoding="utf-8")
        # func.strftime e a forma de chamar funcao do banco via SQLAlchemy.
        assert "func.strftime" not in codigo, (
            f"{arquivo.relative_to(raiz)} chama func.strftime, que so existe no SQLite"
        )
