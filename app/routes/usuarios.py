from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from app.auth import exigir_admin
from app.database import db
from app.models import PAPEIS, Usuario

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

PAPEIS_ROTULOS = {
    "admin": "Administrador",
    "atendente": "Atendente",
}

CHAVE_TOKEN_EXIBIDO = "token_exibido"


def _contar_admins_ativos(exceto_id=None):
    query = Usuario.query.filter_by(papel="admin", ativo=True)
    if exceto_id is not None:
        query = query.filter(Usuario.id != exceto_id)
    return query.count()


def _email_em_uso(email, exceto_id=None):
    query = Usuario.query.filter_by(email=email)
    if exceto_id is not None:
        query = query.filter(Usuario.id != excuto_id)
    return query.first()


@bp.before_request
@exigir_admin
def _bloquear_sem_admin():
    """Aplica exigir_admin a todas as rotas deste blueprint de uma vez.

    Cada rota ficaria sem guarda se alguem forget este decorator: o blueprint
    inteiro e area administrativa, entao a verificacao fica aqui, uma vez so.
    As rotas abaixo ainda nao repetem o decorator, porque exigir_admin ja
    garante sessao e perfil admin em qualquer uma delas.
    """
    return None


@bp.route("/")
def index():
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    token_gerado = session.pop(CHAVE_TOKEN_EXIBIDO, None)
    return render_template(
        "usuarios/lista.html",
        titulo="Usuários",
        usuarios=usuarios,
        papeis=PAPEIS_ROTULOS,
        token_gerado=token_gerado,
    )


@bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        papel = (request.form.get("papel") or "atendente").strip()
        senha = request.form.get("senha") or ""

        erro = None
        if not nome:
            erro = "Informe o nome."
        elif not email:
            erro = "Informe o e-mail."
        elif _email_em_uso(email):
            erro = "Já existe um usuário com este e-mail."
        elif papel not in PAPEIS:
            erro = "Perfil inválido."
        elif len(senha) < 8:
            erro = "A senha deve ter no mínimo 8 caracteres."

        if erro:
            flash(erro, "danger")
            return render_template(
                "usuarios/formulario.html",
                titulo="Novo usuário",
                usuario=None,
                papeis=PAPEIS_ROTULOS,
                valores={"nome": nome, "email": email, "papel": papel},
            )

        usuario = Usuario(nome=nome, email=email, papel=papel, ativo=True)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        flash("Usuário cadastrado com sucesso.", "sucesso")
        return redirect(url_for("usuarios.index"))

    return render_template(
        "usuarios/formulario.html",
        titulo="Novo usuário",
        usuario=None,
        papeis=PAPEIS_ROTULOS,
        valores={"nome": "", "email": "", "papel": "atendente"},
    )


@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
def editar(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)

    if request.method == "POST":
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        papel = (request.form.get("papel") or usuario.papel).strip()
        ativo = request.form.get("ativo") == "1"

        erro = None
        if not nome:
            erro = "Informe o nome."
        elif not email:
            erro = "Informe o e-mail."
        elif _email_em_uso(email, exceto_id=usuario.id):
            erro = "Já existe um usuário com este e-mail."
        elif papel not in PAPEIS:
            erro = "Perfil inválido."
        elif (
            usuario.id == current_user.id
            and not ativo
        ):
            erro = "Você não pode desativar o próprio usuário."
        elif (
            usuario.eh_admin
            and (papel != "admin" or not ativo)
            and _contar_admins_ativos(exceto_id=usuario.id) == 0
        ):
            erro = "É preciso manter ao menos um administrador ativo."

        if erro:
            flash(erro, "danger")
        else:
            usuario.nome = nome
            usuario.email = email
            usuario.papel = papel
            usuario.ativo = ativo
            db.session.commit()
            flash("Usuário alterado com sucesso.", "sucesso")
            return redirect(url_for("usuarios.index"))

    return render_template(
        "usuarios/formulario.html",
        titulo="Editar usuário",
        usuario=usuario,
        papeis=PAPEIS_ROTULOS,
        valores={"nome": usuario.nome, "email": usuario.email, "papel": usuario.papel},
    )


@bp.route("/<int:usuario_id>/excluir", methods=["POST"])
def excluir(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)

    if usuario.id == current_user.id:
        flash("Você não pode excluir o próprio usuário.", "danger")
    elif usuario.eh_admin and _contar_admins_ativos(exceto_id=usuario.id) == 0:
        flash("É preciso manter ao menos um administrador ativo.", "danger")
    else:
        db.session.delete(usuario)
        db.session.commit()
        flash("Usuário excluído com sucesso.", "sucesso")

    return redirect(url_for("usuarios.index"))


@bp.route("/<int:usuario_id>/senha", methods=["POST"])
def redefinir_senha(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    nova = request.form.get("nova_senha") or ""

    if len(nova) < 8:
        flash("A senha deve ter no mínimo 8 caracteres.", "danger")
    else:
        usuario.set_senha(nova)
        usuario.revogar_token_api()
        db.session.commit()
        flash(
            f"Senha de {usuario.nome} redefinida. As sessões abertas e o token de API foram invalidados.",
            "sucesso",
        )

    return redirect(url_for("usuarios.index"))


@bp.route("/<int:usuario_id>/token", methods=["POST"])
def gerenciar_token(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    acao = request.form.get("acao") or "gerar"

    if acao == "revogar":
        usuario.revogar_token_api()
        db.session.commit()
        flash(f"Token de API de {usuario.nome} revogado.", "sucesso")
    else:
        token = usuario.gerar_token_api()
        db.session.commit()
        session[CHAVE_TOKEN_EXIBIDO] = token
        flash(
            f"Token de API de {usuario.nome} gerado. Copie agora: não será exibido novamente.",
            "sucesso",
        )

    return redirect(url_for("usuarios.index"))
