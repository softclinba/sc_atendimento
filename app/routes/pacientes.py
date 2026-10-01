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
from app.models import Atendimento, Paciente

bp = Blueprint("pacientes", __name__, url_prefix="/pacientes")

exigir_sessao_web(bp)


@bp.route("/")
def lista():
    busca = request.args.get("q", "").strip()
    query = Paciente.query
    if busca:
        query = query.filter(Paciente.nome.ilike(f"%{busca}%"))
    pacientes = query.order_by(Paciente.nome).all()
    return render_template(
        "pacientes/lista.html", pacientes=pacientes, busca=busca
    )


@bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("O nome do paciente é obrigatório.", "erro")
            return render_template("pacientes/formulario.html", paciente=None), 400
        paciente = Paciente(nome=nome)
        db.session.add(paciente)
        db.session.commit()
        flash("Cadastro realizado com sucesso.", "sucesso")
        return redirect(url_for("pacientes.lista"))
    return render_template("pacientes/formulario.html", paciente=None)


@bp.route("/<int:paciente_id>/editar", methods=["GET", "POST"])
def editar(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)
    if not paciente:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("pacientes.lista"))
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("O nome do paciente é obrigatório.", "erro")
            return (
                render_template(
                    "pacientes/formulario.html", paciente=paciente
                ),
                400,
            )
        paciente.nome = nome
        db.session.commit()
        flash("Alteração realizada com sucesso.", "sucesso")
        return redirect(url_for("pacientes.lista"))
    return render_template("pacientes/formulario.html", paciente=paciente)


@bp.route("/<int:paciente_id>/excluir", methods=["POST"])
def excluir(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)
    if not paciente:
        flash("Registro não encontrado.", "erro")
        return redirect(url_for("pacientes.lista"))

    tem_atendimentos = (
        db.session.query(Atendimento.id)
        .filter(Atendimento.paciente_id == paciente_id)
        .first()
    )
    if tem_atendimentos:
        flash(
            "Não é possível excluir este paciente porque existem atendimentos relacionados.",
            "erro",
        )
        return redirect(url_for("pacientes.lista"))

    db.session.delete(paciente)
    db.session.commit()
    flash("Exclusão realizada com sucesso.", "sucesso")
    return redirect(url_for("pacientes.lista"))

