from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.auth import exigir_admin, exigir_sessao_web
from app.database import db
from app.models import Atendimento, Procedimento

bp = Blueprint("procedimentos", __name__, url_prefix="/procedimentos")

exigir_sessao_web(bp)


def _parse_valor(valor):
    if valor is None or valor == "":
        raise ValueError
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    texto = texto.replace(".", "").replace(",", ".")
    return Decimal(texto)


@bp.route("/")
def lista():
    busca = request.args.get("q", "").strip()
    query = Procedimento.query
    if busca:
        query = query.filter(Procedimento.nome.ilike(f"%{busca}%"))
    procedimentos = query.order_by(Procedimento.nome).all()
    return render_template(
        "procedimentos/lista.html", procedimentos=procedimentos, busca=busca
    )


@bp.route("/novo", methods=["GET", "POST"])
@exigir_admin
def novo():
    if request.method == "POST":
        try:
            valores_validos = _validar_e_criar()
        except ValueError as e:
            flash(str(e), "erro")
            return render_template(
                "procedimentos/formulario.html", procedimento=None
            ), 400
        db.session.add(valores_validos)
        db.session.commit()
        flash("Cadastro realizado com sucesso.", "sucesso")
        return redirect(url_for("procedimentos.lista"))
    return render_template("procedimentos/formulario.html", procedimento=None)


def _validar_e_criar():
    nome = request.form.get("nome", "").strip()
    if not nome:
        raise ValueError("O nome do procedimento é obrigatório.")
    try:
        valor = _parse_valor(request.form.get("valor"))
    except (ValueError, InvalidOperation):
        raise ValueError("Informe um valor válido para o procedimento.")
    if valor < 0:
        raise ValueError("O valor não pode ser negativo.")
    return Procedimento(nome=nome, valor=valor)


@bp.route("/<int:procedimento_id>/editar", methods=["GET", "POST"])
@exigir_admin
def editar(procedimento_id):
    procedimento = db.session.get(Procedimento, procedimento_id)
    if not procedimento:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("procedimentos.lista"))
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("O nome do procedimento é obrigatório.", "erro")
            return render_template(
                "procedimentos/formulario.html", procedimento=procedimento
            ), 400
        try:
            valor = _parse_valor(request.form.get("valor"))
        except (ValueError, InvalidOperation):
            flash("Informe um valor válido para o procedimento.", "erro")
            return render_template(
                "procedimentos/formulario.html", procedimento=procedimento
            ), 400
        if valor < 0:
            flash("O valor não pode ser negativo.", "erro")
            return render_template(
                "procedimentos/formulario.html", procedimento=procedimento
            ), 400
        procedimento.nome = nome
        procedimento.valor = valor
        db.session.commit()
        flash("Alteração realizada com sucesso.", "sucesso")
        return redirect(url_for("procedimentos.lista"))
    return render_template(
        "procedimentos/formulario.html", procedimento=procedimento
    )


@bp.route("/<int:procedimento_id>/excluir", methods=["POST"])
@exigir_admin
def excluir(procedimento_id):
    procedimento = db.session.get(Procedimento, procedimento_id)
    if not procedimento:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("procedimentos.lista"))

    tem_atendimentos = (
        db.session.query(Atendimento.id)
        .filter(Atendimento.procedimento_id == procedimento_id)
        .first()
    )
    if tem_atendimentos:
        flash(
            "Não é possível excluir este procedimento porque existem atendimentos relacionados.",
            "erro",
        )
        return redirect(url_for("procedimentos.lista"))

    db.session.delete(procedimento)
    db.session.commit()
    flash("Exclusão realizada com sucesso.", "sucesso")
    return redirect(url_for("procedimentos.lista"))
