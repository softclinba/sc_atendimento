import csv
import io
import json

from app.database import db
from app.models import Atendimento, Medico, Paciente, Procedimento


def _preparar_base(client):
    dados = {}
    with client.application.app_context():
        medico = Medico.query.first()
        proc = Procedimento.query.filter_by(nome="Consulta Particular").first()
        if not proc:
            proc = Procedimento.query.first()
        paciente = Paciente(nome="Paciente Acentuado ãçé")
        db.session.add(paciente)
        db.session.commit()
        dados = {
            "medico_id": medico.id,
            "procedimento_id": proc.id,
            "paciente_id": paciente.id,
        }
    return dados


def _criar(client, base, data="2026-09-03", valor="250,00", pag="Pix", nome=None):
    with client.application.app_context():
        if nome:
            p = Paciente(nome=nome)
            db.session.add(p)
            db.session.commit()
            pid = p.id
        else:
            pid = base["paciente_id"]
    dado = {
        "paciente_id": pid,
        "medico_id": base["medico_id"],
        "procedimento_id": base["procedimento_id"],
        "data_atendimento": data,
        "valor": valor,
        "observacoes": "obs",
        "forma_pagamento": pag,
    }
    client.post("/atendimentos/novo", data=dado)
    return pid


def test_geracao_csv_estrutura(client):
    base = _preparar_base(client)
    _criar(client, base)
    res = client.get("/api/atendimentos/export/csv")
    assert res.status_code == 200
    conteudo = res.data.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(conteudo))
    linhas = list(reader)
    assert linhas[0][0] == "ID"
    assert linhas[0][4] == "Procedimento"
    assert len(linhas) == 2


def test_geracao_csv_acentos_utf8(client):
    base = _preparar_base(client)
    _criar(client, base, nome="João da Silva Próximo")
    res = client.get("/api/atendimentos/export/csv")
    conteudo = res.data.decode("utf-8-sig")
    assert "João da Silva Próximo" in conteudo
    assert "\ufeff" in conteudo or res.data.startswith(b"\xef\xbb\xbf")


def test_geracao_json_estrutura(client):
    base = _preparar_base(client)
    _criar(client, base)
    res = client.get("/api/atendimentos/export/json")
    assert res.status_code == 200
    dados = json.loads(res.data.decode("utf-8"))
    assert isinstance(dados, list)
    assert len(dados) == 1
    item = dados[0]
    assert "paciente" in item
    assert isinstance(item["valor"], (int, float))
    assert item["valor"] == 250.0
    assert "data_atendimento" in item


def test_exportar_todos_registros(client):
    base = _preparar_base(client)
    _criar(client, base)
    _criar(client, base, nome="Outro Paciente")
    res = client.get("/api/atendimentos/export/json")
    dados = json.loads(res.data.decode("utf-8"))
    assert len(dados) == 2


def test_exportar_respeitando_filtros(client):
    base = _preparar_base(client)
    pid1 = _criar(client, base, data="2026-09-01")
    _criar(client, base, nome="Outro Paciente", data="2026-09-05")

    # Filtrar por data
    res = client.get(
        "/api/atendimentos/export/json",
        query_string={"data_inicio": "2026-09-04", "data_fim": "2026-09-10"},
    )
    dados = json.loads(res.data.decode("utf-8"))
    assert len(dados) == 1

    # Filtrar por paciente
    res = client.get(
        "/api/atendimentos/export/json",
        query_string={"paciente_id": pid1},
    )
    dados = json.loads(res.data.decode("utf-8"))
    assert len(dados) == 1


def test_exportar_sem_registros(client):
    res = client.get("/api/atendimentos/export/json")
    dados = json.loads(res.data.decode("utf-8"))
    assert dados == []

    res = client.get("/api/atendimentos/export/csv")
    conteudo = res.data.decode("utf-8-sig")
    assert conteudo.splitlines()[0].startswith("ID")
    assert len(conteudo.splitlines()) == 1


def test_json_valor_numerico(client):
    base = _preparar_base(client)
    _criar(client, base, valor="300,75")
    res = client.get("/api/atendimentos/export/json")
    dados = json.loads(res.data.decode("utf-8"))
    assert dados[0]["valor"] == 300.75
    assert isinstance(dados[0]["valor"], float)


def test_csv_valor_numerico(client):
    base = _preparar_base(client)
    _criar(client, base, valor="300,75")
    res = client.get("/api/atendimentos/export/csv")
    conteudo = res.data.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(conteudo))
    linhas = list(reader)
    assert linhas[1][5] == "300.75"


def test_geracao_pdf_estrutura(client):
    base = _preparar_base(client)
    _criar(client, base)
    res = client.get("/api/atendimentos/export/pdf")
    assert res.status_code == 200
    assert res.data.startswith(b"%PDF")
    assert res.mimetype == "application/pdf"
    assert "attachment;" in res.headers.get("Content-Disposition", "")
    assert res.headers.get("Content-Disposition", "").endswith(".pdf")
