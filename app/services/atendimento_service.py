from datetime import datetime

from app.database import db
from app.models import Atendimento, Medico, Paciente, Procedimento


def montar_consulta_filtros(
    paciente_id=None,
    medico_id=None,
    procedimento_id=None,
    forma_pagamento=None,
    data_inicio=None,
    data_fim=None,
):
    query = db.session.query(Atendimento)

    if paciente_id:
        query = query.filter(Atendimento.paciente_id == paciente_id)
    if medico_id:
        query = query.filter(Atendimento.medico_id == medico_id)
    if procedimento_id:
        query = query.filter(Atendimento.procedimento_id == procedimento_id)
    if forma_pagamento:
        query = query.filter(Atendimento.forma_pagamento == forma_pagamento)
    if data_inicio:
        di = _parse_date(data_inicio)
        if di:
            query = query.filter(Atendimento.data_atendimento >= di)
    if data_fim:
        df = _parse_date(data_fim)
        if df:
            query = query.filter(Atendimento.data_atendimento <= df)

    return query


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def listar_atendimentos_filtrados(request_args):
    return montar_consulta_filtros(
        paciente_id=request_args.get("paciente_id", type=int) or None,
        medico_id=request_args.get("medico_id", type=int) or None,
        procedimento_id=request_args.get("procedimento_id", type=int) or None,
        forma_pagamento=request_args.get("forma_pagamento") or None,
        data_inicio=request_args.get("data_inicio") or None,
        data_fim=request_args.get("data_fim") or None,
    )


def obter_atendimento_ou_404(atendimento_id):
    return db.session.get(Atendimento, atendimento_id)


def criar_atendimento(dados):
    atendimento = Atendimento(
        paciente_id=dados["paciente_id"],
        medico_id=dados["medico_id"],
        procedimento_id=dados["procedimento_id"],
        data_atendimento=dados["data_atendimento"],
        valor=dados["valor"],
        observacoes=dados.get("observacoes") or None,
        forma_pagamento=dados["forma_pagamento"],
    )
    db.session.add(atendimento)
    return atendimento


def atualizar_atendimento(atendimento, dados):
    atendimento.paciente_id = dados["paciente_id"]
    atendimento.medico_id = dados["medico_id"]
    atendimento.procedimento_id = dados["procedimento_id"]
    atendimento.data_atendimento = dados["data_atendimento"]
    atendimento.valor = dados["valor"]
    atendimento.observacoes = dados.get("observacoes") or None
    atendimento.forma_pagamento = dados["forma_pagamento"]
    return atendimento
