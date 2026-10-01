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
from app.models import Atendimento, Medico

bp = Blueprint("medicos", __name__, url_prefix="/medicos")

exigir_sessao_web(bp)


@bp.route("/")
def lista():
    busca = request.args.get("q", "").strip()
    query = Medico.query
    if busca:
        query = query.filter(Medico.nome.ilike(f"%{busca}%"))
    medicos = query.order_by(Medico.nome).all()
    return render_template("medicos/lista.html", medicos=medicos, busca=busca)


@bp.route("/novo", methods=["GET", "POST"])
@exigir_admin
def novo():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("O nome do médico é obrigatório.", "erro")
            return render_template("medicos/formulario.html", medico=None), 400
        medico = Medico(nome=nome)
        db.session.add(medico)
        db.session.commit()
        flash("Cadastro realizado com sucesso.", "sucesso")
        return redirect(url_for("medicos.lista"))
    return render_template("medicos/formulario.html", medico=None)


@bp.route("/<int:medico_id>/editar", methods=["GET", "POST"])
@exigir_admin
def editar(medico_id):
    medico = db.session.get(Medico, medico_id)
    if not medico:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("medicos.lista"))
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("O nome do médico é obrigatório.", "erro")
            return render_template("medicos/formulario.html", medico=medico), 400
        medico.nome = nome
        db.session.commit()
        flash("Alteração realizada com sucesso.", "sucesso")
        return redirect(url_for("medicos.lista"))
    return render_template("medicos/formulario.html", medico=medico)


@bp.route("/<int:medico_id>/excluir", methods=["POST"])
@exigir_admin
def excluir(medico_id):
    medico = db.session.get(Medico, medico_id)
    if not medico:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("medicos.lista"))

    tem_atendimentos = (
        db.session.query(Atendimento.id)
        .filter(Atendimento.medico_id == medico_id)
        .first()
    )
    if tem_atendimentos:
        flash(
            "Não é possível excluir este médico porque existem atendimentos relacionados.",
            "erro",
        )
        return redirect(url_for("medicos.lista"))

    db.session.delete(medico)
    db.session.commit()
    flash("Exclusão realizada com sucesso.", "sucesso")
    return redirect(url_for("medicos.lista"))
