from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.auth import exigir_sessao_web
from app.database import db
from app.models import Atendimento, Medico, Paciente, Procedimento
from app.services.atendimento_service import (
    listar_atendimentos_filtrados,
    obter_atendimento_ou_404,
)

bp = Blueprint("atendimentos", __name__, url_prefix="/atendimentos")

exigir_sessao_web(bp)


def _parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_valor(value):
    if value is None or value == "":
        raise ValueError
    texto = str(value).strip().replace("R$", "").replace(" ", "")
    texto = texto.replace(".", "").replace(",", ".")
    return Decimal(texto)


def _coletar_formulario(edicao=False):
    paciente_id = request.form.get("paciente_id", type=int)
    medico_id = request.form.get("medico_id", type=int)
    procedimento_id = request.form.get("procedimento_id", type=int)
    data_atendimento = _parse_date(request.form.get("data_atendimento"))
    forma_pagamento = request.form.get("forma_pagamento", "").strip()
    observacoes = request.form.get("observacoes", "").strip()
    numero_parcelas = request.form.get("numero_parcelas", type=int)

    try:
        valor = _parse_valor(request.form.get("valor"))
    except (ValueError, InvalidOperation):
        valor = None

    return {
        "paciente_id": paciente_id,
        "medico_id": medico_id,
        "procedimento_id": procedimento_id,
        "data_atendimento": data_atendimento,
        "valor": valor,
        "observacoes": observacoes,
        "forma_pagamento": forma_pagamento,
        "numero_parcelas": numero_parcelas if forma_pagamento == "Crédito" else None,
        "_edicao": edicao,
    }


def _validar_dados(dados):
    erros = []
    form = request.form

    if not dados["paciente_id"] or not db.session.get(
        Paciente, dados["paciente_id"]
    ):
        erros.append("Selecione um paciente válido.")
    if not dados["medico_id"] or not db.session.get(Medico, dados["medico_id"]):
        erros.append("Selecione um médico válido.")
    if not dados["procedimento_id"] or not db.session.get(
        Procedimento, dados["procedimento_id"]
    ):
        erros.append("Selecione um procedimento válido.")
    if not dados["data_atendimento"]:
        erros.append("Informe a data de atendimento.")
    if dados["valor"] is None:
        erros.append("Informe um valor válido.")
    elif dados["valor"] < 0:
        erros.append("O valor não pode ser negativo.")
    if not dados["forma_pagamento"]:
        erros.append("Selecione a forma de pagamento.")
    elif dados["forma_pagamento"] not in app_config_formas():
        erros.append("Forma de pagamento inválida.")
    elif dados["forma_pagamento"] == "Crédito":
        if not dados["numero_parcelas"]:
            erros.append("Informe o número de parcelas.")
        elif not (1 <= dados["numero_parcelas"] <= app_config_max_parcelas()):
            erros.append(
                f"O número de parcelas deve estar entre 1 e {app_config_max_parcelas()}."
            )

    return erros


def app_config_formas():
    from flask import current_app

    return current_app.config["FORMAS_PAGAMENTO"]


def app_config_max_parcelas():
    from flask import current_app

    return current_app.config["MAX_PARCELAS"]


@bp.route("/")
def lista():
    query = listar_atendimentos_filtrados(request.args)
    atendimentos = query.order_by(
        Atendimento.data_atendimento.desc(), Atendimento.id.desc()
    ).all()

    pacientes = Paciente.query.order_by(Paciente.nome).all()
    medicos = Medico.query.order_by(Medico.nome).all()
    procedimentos = Procedimento.query.order_by(Procedimento.nome).all()

    total = sum(a.valor_float for a in atendimentos)

    def _data_br(value):
        if not value:
            return ""
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return str(value)

    filtros = {
        "paciente_id": request.args.get("paciente_id", type=int) or "",
        "medico_id": request.args.get("medico_id", type=int) or "",
        "procedimento_id": request.args.get("procedimento_id", type=int) or "",
        "forma_pagamento": request.args.get("forma_pagamento", "") or "",
        "data_inicio": _data_br(request.args.get("data_inicio", "")),
        "data_fim": _data_br(request.args.get("data_fim", "")),
        "q": request.args.get("q", "") or "",
    }

    return render_template(
        "atendimentos/lista.html",
        atendimentos=atendimentos,
        pacientes=pacientes,
        medicos=medicos,
        procedimentos=procedimentos,
        filtros=filtros,
        total=total,
    )


@bp.route("/novo", methods=["GET", "POST"])
def novo():
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    medicos = Medico.query.order_by(Medico.nome).all()
    procedimentos = Procedimento.query.order_by(Procedimento.nome).all()

    if request.method == "POST":
        dados = _coletar_formulario()
        erros = _validar_dados(dados)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template(
                "atendimentos/formulario.html",
                atendimento=None,
                pacientes=pacientes,
                medicos=medicos,
                procedimentos=procedimentos,
                form=dados,
            ), 400

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
        flash("Cadastro realizado com sucesso.", "sucesso")
        return redirect(url_for("atendimentos.lista"))

    return render_template(
        "atendimentos/formulario.html",
        atendimento=None,
        pacientes=pacientes,
        medicos=medicos,
        procedimentos=procedimentos,
        form=None,
        hoje_br=date.today().strftime("%d/%m/%Y"),
    )


@bp.route("/<int:atendimento_id>")
def detalhes(atendimento_id):
    atendimento = obter_atendimento_ou_404(atendimento_id)
    if not atendimento:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("atendimentos.lista"))
    return render_template(
        "atendimentos/detalhes.html", atendimento=atendimento
    )


@bp.route("/<int:atendimento_id>/editar", methods=["GET", "POST"])
def editar(atendimento_id):
    atendimento = obter_atendimento_ou_404(atendimento_id)
    if not atendimento:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("atendimentos.lista"))

    pacientes = Paciente.query.order_by(Paciente.nome).all()
    medicos = Medico.query.order_by(Medico.nome).all()
    procedimentos = Procedimento.query.order_by(Procedimento.nome).all()

    if request.method == "POST":
        dados = _coletar_formulario(edicao=True)
        erros = _validar_dados(dados)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template(
                "atendimentos/formulario.html",
                atendimento=None,
                pacientes=pacientes,
                medicos=medicos,
                procedimentos=procedimentos,
                form=dados,
                editando=True,
                editar_id=atendimento_id,
            ), 400

        atendimento.paciente_id = dados["paciente_id"]
        atendimento.medico_id = dados["medico_id"]
        atendimento.procedimento_id = dados["procedimento_id"]
        atendimento.data_atendimento = dados["data_atendimento"]
        atendimento.valor = dados["valor"]
        atendimento.observacoes = dados["observacoes"] or None
        atendimento.forma_pagamento = dados["forma_pagamento"]
        atendimento.numero_parcelas = dados["numero_parcelas"]
        db.session.commit()
        flash("Alteração realizada com sucesso.", "sucesso")
        return redirect(url_for("atendimentos.lista"))

    return render_template(
        "atendimentos/formulario.html",
        atendimento=atendimento,
        pacientes=pacientes,
        medicos=medicos,
        procedimentos=procedimentos,
        form=None,
        editando=True,
        editar_id=atendimento_id,
    )


@bp.route("/<int:atendimento_id>/excluir", methods=["POST"])
def excluir(atendimento_id):
    atendimento = obter_atendimento_ou_404(atendimento_id)
    if not atendimento:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("atendimentos.lista"))
    db.session.delete(atendimento)
    db.session.commit()
    flash("Exclusão realizada com sucesso.", "sucesso")
    return redirect(url_for("atendimentos.lista"))
