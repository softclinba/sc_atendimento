from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, Response, jsonify, request

from app.auth import exigir_admin, exigir_token_api
from app.database import db
from app.models import Atendimento, Medico, Paciente, Procedimento
from app.services.atendimento_service import listar_atendimentos_filtrados
from app.services.exportacao import (
    exportar_csv as _exportar_csv,
    exportar_json as _exportar_json,
    exportar_pdf as _exportar_pdf,
)

bp = Blueprint("api", __name__, url_prefix="/api")

# Toda a API exige autenticacao por token (Authorization: Bearer) ou por
# sessao de navegador. A unica excecao e /api/health, usada por monitoracao.
exigir_token_api(bp, endpoint_livre="api.health")


def _erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


@bp.route("/health", methods=["GET"])
def health():
    """Verificacao de disponibilidade. Nao exige autenticacao."""
    return jsonify({"status": "ok"})


def _regex_valor(valor):
    if valor is None or valor == "":
        return None
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(texto)
    except (ValueError, InvalidOperation):
        return None


def _parse_data(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------- Pacientes
@bp.route("/pacientes", methods=["GET"])
def listar_pacientes():
    busca = request.args.get("q", "").strip()
    query = Paciente.query
    if busca:
        query = query.filter(Paciente.nome.ilike(f"%{busca}%"))
    pacientes = query.order_by(Paciente.nome).all()
    return jsonify([{"id": p.id, "nome": p.nome} for p in pacientes])


@bp.route("/pacientes", methods=["POST"])
def criar_paciente():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return _erro("nome obrigatório")
    paciente = Paciente(nome=nome)
    db.session.add(paciente)
    db.session.commit()
    return jsonify({"id": paciente.id, "nome": paciente.nome}), 201


@bp.route("/pacientes/<int:paciente_id>", methods=["GET"])
def obter_paciente(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)
    if not paciente:
        return _erro("Paciente não encontrado.", 404)
    return jsonify({"id": paciente.id, "nome": paciente.nome})


@bp.route("/pacientes/<int:paciente_id>", methods=["PUT"])
def atualizar_paciente(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)
    if not paciente:
        return _erro("Paciente não encontrado.", 404)
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return _erro("nome obrigatório")
    paciente.nome = nome
    db.session.commit()
    return jsonify({"id": paciente.id, "nome": paciente.nome})


@bp.route("/pacientes/<int:paciente_id>", methods=["DELETE"])
def excluir_paciente(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)
    if not paciente:
        return _erro("Paciente não encontrado.", 404)
    tem_atendimentos = (
        db.session.query(Atendimento.id)
        .filter(Atendimento.paciente_id == paciente_id)
        .first()
    )
    if tem_atendimentos:
        return _erro(
            "Não é possível excluir o paciente porque existem atendimentos relacionados.",
            409,
        )
    db.session.delete(paciente)
    db.session.commit()
    return "", 204


# ------------------------------------------------------------------- Medicos
@bp.route("/medicos", methods=["GET"])
def listar_medicos():
    busca = request.args.get("q", "").strip()
    query = Medico.query
    if busca:
        query = query.filter(Medico.nome.ilike(f"%{busca}%"))
    medicos = query.order_by(Medico.nome).all()
    return jsonify([{"id": m.id, "nome": m.nome} for m in medicos])


@bp.route("/medicos", methods=["POST"])
@exigir_admin
def criar_medico():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return _erro("nome obrigatório")
    medico = Medico(nome=nome)
    db.session.add(medico)
    db.session.commit()
    return jsonify({"id": medico.id, "nome": medico.nome}), 201


@bp.route("/medicos/<int:medico_id>", methods=["GET"])
def obter_medico(medico_id):
    medico = db.session.get(Medico, medico_id)
    if not medico:
        return _erro("Médico não encontrado.", 404)
    return jsonify({"id": medico.id, "nome": medico.nome})


@bp.route("/medicos/<int:medico_id>", methods=["PUT"])
@exigir_admin
def atualizar_medico(medico_id):
    medico = db.session.get(Medico, medico_id)
    if not medico:
        return _erro("Médico não encontrado.", 404)
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return _erro("nome obrigatório")
    medico.nome = nome
    db.session.commit()
    return jsonify({"id": medico.id, "nome": medico.nome})


@bp.route("/medicos/<int:medico_id>", methods=["DELETE"])
@exigir_admin
def excluir_medico(medico_id):
    medico = db.session.get(Medico, medico_id)
    if not medico:
        return _erro("Médico não encontrado.", 404)
    tem_atendimentos = (
        db.session.query(Atendimento.id)
        .filter(Atendimento.medico_id == medico_id)
        .first()
    )
    if tem_atendimentos:
        return _erro(
            "Não é possível excluir o médico porque existem atendimentos relacionados.",
            409,
        )
    db.session.delete(medico)
    db.session.commit()
    return "", 204


# ------------------------------------------------------------- Procedimentos
def _serializar_procedimento(p):
    return {"id": p.id, "nome": p.nome, "valor": p.valor_float}


@bp.route("/procedimentos", methods=["GET"])
def listar_procedimentos():
    busca = request.args.get("q", "").strip()
    query = Procedimento.query
    if busca:
        query = query.filter(Procedimento.nome.ilike(f"%{busca}%"))
    procedimentos = query.order_by(Procedimento.nome).all()
    return jsonify([_serializar_procedimento(p) for p in procedimentos])


def _validar_procedimento_dados():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return None, _erro("nome obrigatório")
    valor = _regex_valor(dados.get("valor"))
    if valor is None:
        return None, _erro("valor obrigatório")
    if valor < 0:
        return None, _erro("valor não pode ser negativo")
    return {"nome": nome, "valor": valor}, None


@bp.route("/procedimentos", methods=["POST"])
@exigir_admin
def criar_procedimento():
    dados, erro = _validar_procedimento_dados()
    if erro:
        return erro
    procedimento = Procedimento(nome=dados["nome"], valor=dados["valor"])
    db.session.add(procedimento)
    db.session.commit()
    return jsonify(_serializar_procedimento(procedimento)), 201


@bp.route("/procedimentos/<int:procedimento_id>", methods=["GET"])
def obter_procedimento(procedimento_id):
    procedimento = db.session.get(Procedimento, procedimento_id)
    if not procedimento:
        return _erro("Procedimento não encontrado.", 404)
    return jsonify(_serializar_procedimento(procedimento))


@bp.route("/procedimentos/<int:procedimento_id>", methods=["PUT"])
@exigir_admin
def atualizar_procedimento(procedimento_id):
    procedimento = db.session.get(Procedimento, procedimento_id)
    if not procedimento:
        return _erro("Procedimento não encontrado.", 404)
    dados, erro = _validar_procedimento_dados()
    if erro:
        return erro
    procedimento.nome = dados["nome"]
    procedimento.valor = dados["valor"]
    db.session.commit()
    return jsonify(_serializar_procedimento(procedimento))


@bp.route("/procedimentos/<int:procedimento_id>", methods=["DELETE"])
@exigir_admin
def excluir_procedimento(procedimento_id):
    procedimento = db.session.get(Procedimento, procedimento_id)
    if not procedimento:
        return _erro("Procedimento não encontrado.", 404)
    tem_atendimentos = (
        db.session.query(Atendimento.id)
        .filter(Atendimento.procedimento_id == procedimento_id)
        .first()
    )
    if tem_atendimentos:
        return _erro(
            "Não é possível excluir o procedimento porque existem atendimentos relacionados.",
            409,
        )
    db.session.delete(procedimento)
    db.session.commit()
    return "", 204


# -------------------------------------------------------------- Atendimentos
def _serializar_atendimento(a):
    return {
        "id": a.id,
        "data_atendimento": a.data_atendimento.isoformat(),
        "paciente": a.paciente.nome if a.paciente else None,
        "medico": a.medico.nome if a.medico else None,
        "procedimento": a.procedimento.nome if a.procedimento else None,
        "valor": a.valor_float,
        "forma_pagamento": a.forma_pagamento,
        "numero_parcelas": a.numero_parcelas,
        "observacoes": a.observacoes,
    }


def _validar_atendimento_dados(permite_parcial=False):
    dados = request.get_json(silent=True) or {}
    erros = []

    for campo in ("paciente_id", "medico_id", "procedimento_id"):
        valor = dados.get(campo)
        modelo = {
            "paciente_id": Paciente,
            "medico_id": Medico,
            "procedimento_id": Procedimento,
        }[campo]
        if not valor or not db.session.get(modelo, valor):
            erros.append(f"{campo} inválido")

    data = _parse_data(dados.get("data_atendimento"))
    if not data:
        erros.append("data_atendimento inválida")

    valor = dados.get("valor")
    valor_dec = _regex_valor(valor) if valor is not None else None
    if valor_dec is None:
        erros.append("valor obrigatório")
    elif valor_dec < 0:
        erros.append("valor não pode ser negativo")

    forma = (dados.get("forma_pagamento") or "").strip()
    from flask import current_app

    if not forma or forma not in current_app.config["FORMAS_PAGAMENTO"]:
        erros.append("forma_pagamento inválida")

    numero_parcelas = dados.get("numero_parcelas")
    if forma == "Crédito":
        if not numero_parcelas:
            erros.append("numero_parcelas obrigatório para crédito")
        elif not isinstance(numero_parcelas, int) or not (
            1 <= numero_parcelas <= current_app.config["MAX_PARCELAS"]
        ):
            erros.append(
                "numero_parcelas deve ser inteiro entre 1 e "
                f"{current_app.config['MAX_PARCELAS']}"
            )
    else:
        numero_parcelas = None

    observacoes = dados.get("observacoes") or ""

    return {
        "paciente_id": dados.get("paciente_id"),
        "medico_id": dados.get("medico_id"),
        "procedimento_id": dados.get("procedimento_id"),
        "data_atendimento": data,
        "valor": valor_dec,
        "forma_pagamento": forma,
        "numero_parcelas": numero_parcelas,
        "observacoes": observacoes,
        "erros": erros,
    }


@bp.route("/atendimentos", methods=["GET"])
def listar_atendimentos():
    query = listar_atendimentos_filtrados(request.args)
    atendimentos = query.order_by(
        Atendimento.data_atendimento.desc(), Atendimento.id.desc()
    ).all()
    return jsonify([_serializar_atendimento(a) for a in atendimentos])


@bp.route("/atendimentos", methods=["POST"])
def criar_atendimento():
    dados = _validar_atendimento_dados()
    if dados["erros"]:
        return _erro(", ".join(dados["erros"]))
    atendimento = Atendimento(
        paciente_id=dados["paciente_id"],
        medico_id=dados["medico_id"],
        procedimento_id=dados["procedimento_id"],
        data_atendimento=dados["data_atendimento"],
        valor=dados["valor"],
        observacoes=dados["observacoes"] or None,
        forma_pagamento=dados["forma_pagamento"],
        numero_parcelas=dados["numero_parcelas"],
    )
    db.session.add(atendimento)
    db.session.commit()
    return jsonify(_serializar_atendimento(atendimento)), 201


@bp.route("/atendimentos/<int:atendimento_id>", methods=["GET"])
def obter_atendimento(atendimento_id):
    atendimento = db.session.get(Atendimento, atendimento_id)
    if not atendimento:
        return _erro("Atendimento não encontrado.", 404)
    return jsonify(_serializar_atendimento(atendimento))


@bp.route("/atendimentos/<int:atendimento_id>", methods=["PUT"])
def atualizar_atendimento(atendimento_id):
    atendimento = db.session.get(Atendimento, atendimento_id)
    if not atendimento:
        return _erro("Atendimento não encontrado.", 404)
    dados = _validar_atendimento_dados()
    if dados["erros"]:
        return _erro(", ".join(dados["erros"]))
    atendimento.paciente_id = dados["paciente_id"]
    atendimento.medico_id = dados["medico_id"]
    atendimento.procedimento_id = dados["procedimento_id"]
    atendimento.data_atendimento = dados["data_atendimento"]
    atendimento.valor = dados["valor"]
    atendimento.observacoes = dados["observacoes"] or None
    atendimento.forma_pagamento = dados["forma_pagamento"]
    atendimento.numero_parcelas = dados["numero_parcelas"]
    db.session.commit()
    return jsonify(_serializar_atendimento(atendimento))


@bp.route("/atendimentos/<int:atendimento_id>", methods=["DELETE"])
def excluir_atendimento(atendimento_id):
    atendimento = db.session.get(Atendimento, atendimento_id)
    if not atendimento:
        return _erro("Atendimento não encontrado.", 404)
    db.session.delete(atendimento)
    db.session.commit()
    return "", 204


# ------------------------------------------------------------ Exportação
@bp.route("/atendimentos/export/csv", methods=["GET"])
def exportar_csv():
    conteudo, arquivo = _exportar_csv(request.args)
    return Response(
        conteudo,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={arquivo}",
        },
    )


@bp.route("/atendimentos/export/json", methods=["GET"])
def exportar_json():
    conteudo, arquivo = _exportar_json(request.args)
    return Response(
        conteudo,
        mimetype="application/json; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={arquivo}",
        },
    )


@bp.route("/atendimentos/export/pdf", methods=["GET"])
def exportar_pdf():
    conteudo, arquivo = _exportar_pdf(request.args)
    return Response(
        conteudo,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={arquivo}",
        },
    )
