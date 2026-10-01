from datetime import date, timedelta

from flask import Blueprint, render_template, request
from sqlalchemy import extract, func

from app.auth import exigir_sessao_web
from app.database import db
from app.models import Atendimento, Medico, Procedimento

bp = Blueprint("dashboard", __name__)

exigir_sessao_web(bp)

PERIODOS = ("hoje", "semana", "mes", "mes_anterior", "ano")


def _first_of_month(day):
    return day.replace(day=1)


def _intervalo_periodo(periodo, hoje):
    if periodo == "hoje":
        return hoje, hoje
    if periodo == "mes":
        return _first_of_month(hoje), hoje
    if periodo == "mes_anterior":
        fim = _first_of_month(hoje) - timedelta(days=1)
        return _first_of_month(fim), fim
    if periodo == "ano":
        return hoje.replace(month=1, day=1), hoje
    inicio = hoje - timedelta(days=hoje.weekday())
    return inicio, hoje


def _meses_entre(inicio, fim):
    meses = []
    cursor = inicio.replace(day=1)
    while cursor <= fim:
        meses.append((cursor.year, cursor.month))
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
    return meses


@bp.route("/")
def index():
    hoje = date.today()
    periodo = request.args.get("periodo", "todos")

    if periodo == "todos" or periodo == "":
        periodo = "todos"
        inicio_periodo = fim_periodo = None
    elif periodo not in PERIODOS:
        periodo = "semana"
        inicio_periodo, fim_periodo = _intervalo_periodo(periodo, hoje)
    else:
        inicio_periodo, fim_periodo = _intervalo_periodo(periodo, hoje)

    filtro_periodo = ()
    if inicio_periodo is not None:
        filtro_periodo = (
            Atendimento.data_atendimento >= inicio_periodo,
            Atendimento.data_atendimento <= fim_periodo,
        )

    total_atendimentos = (
        db.session.query(func.count(Atendimento.id))
        .filter(*filtro_periodo)
        .scalar()
        or 0
    )
    valor_total = db.session.query(
        func.coalesce(func.sum(Atendimento.valor), 0)
    ).filter(*filtro_periodo).scalar()

    # Gráfico 1: atendimentos por médico (barras)
    q_medicos = (
        db.session.query(Medico.nome, func.count(Atendimento.id))
        .join(Atendimento, Atendimento.medico_id == Medico.id)
        .group_by(Medico.id, Medico.nome)
        .order_by(func.count(Atendimento.id).desc())
    )
    if filtro_periodo:
        q_medicos = q_medicos.filter(*filtro_periodo)
    medicos_counts = q_medicos.all()
    medicos_labels = [nome for nome, _ in medicos_counts]
    medicos_valores = [round(float(count)) for _, count in medicos_counts]

    # Gráfico 2: total mensal do valor total (linha)
    #
    # Agrupamos por ano e mes como inteiros, e montamos a chave "AAAA-MM" no
    # Python. Formatar a data direto no SQL exigiria funcao diferente em cada
    # banco (strftime no SQLite, to_char no PostgreSQL); extrair os dois
    # componentes usa SQL padrao e funciona nos dois.
    ano_atendimento = extract("year", Atendimento.data_atendimento)
    mes_atendimento = extract("month", Atendimento.data_atendimento)

    q_meses = (
        db.session.query(
            ano_atendimento.label("ano"),
            mes_atendimento.label("mes_num"),
            func.coalesce(func.sum(Atendimento.valor), 0),
        )
        .group_by(ano_atendimento, mes_atendimento)
        .order_by(ano_atendimento, mes_atendimento)
    )
    if filtro_periodo:
        q_meses = q_meses.filter(*filtro_periodo)
    meses_dict = {
        f"{int(ano):04d}-{int(mes_num):02d}": valor
        for ano, mes_num, valor in q_meses.all()
    }

    if inicio_periodo is not None:
        lista_meses = _meses_entre(inicio_periodo, fim_periodo)
        if not lista_meses:
            lista_meses = [(hoje.year, hoje.month)]
    else:
        data_min = db.session.query(func.min(Atendimento.data_atendimento)).scalar()
        if data_min is None:
            lista_meses = [(hoje.year, hoje.month)]
        else:
            lista_meses = _meses_entre(data_min, hoje)
            if not lista_meses:
                lista_meses = [(hoje.year, hoje.month)]

    meses_labels = [f"{mes:02d}/{ano}" for ano, mes in lista_meses]
    meses_valores = [
        round(float(meses_dict.get(f"{ano:04d}-{mes:02d}", 0)), 2)
        for ano, mes in lista_meses
    ]

    # Gráfico 3: procedimentos x valor
    q_procs = (
        db.session.query(
            Procedimento.nome,
            func.coalesce(func.sum(Atendimento.valor), 0),
        )
        .join(Atendimento, Atendimento.procedimento_id == Procedimento.id)
        .group_by(Procedimento.id, Procedimento.nome)
        .order_by(func.coalesce(func.sum(Atendimento.valor), 0).desc())
    )
    if filtro_periodo:
        q_procs = q_procs.filter(*filtro_periodo)
    procs = q_procs.all()
    procedimentos_labels = [nome for nome, _ in procs]
    procedimentos_valores = [round(float(valor), 2) for _, valor in procs]

    return render_template(
        "dashboard.html",
        total_atendimentos=total_atendimentos,
        valor_total=float(valor_total),
        periodo=periodo,
        periodos=PERIODOS,
        inicio_periodo=inicio_periodo,
        fim_periodo=fim_periodo,
        hoje=hoje,
        medicos_labels=medicos_labels,
        medicos_valores=medicos_valores,
        meses_labels=meses_labels,
        meses_valores=meses_valores,
        procedimentos_labels=procedimentos_labels,
        procedimentos_valores=procedimentos_valores,
    )
