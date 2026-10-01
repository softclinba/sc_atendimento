from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user

from app.auth import MARCA_SENHA, encerrar_sessao
from app.models import Usuario

bp = Blueprint("auth", __name__)

PAPEIS_ROTULOS = {
    "admin": "Administrador",
    "atendente": "Atendente",
}


def _proximo_destino():
    destino = request.args.get("next") or request.form.get("next") or ""
    # Somente caminhos internos: evita open redirect via ?next=https://...
    if destino.startswith("/") and not destino.startswith("//"):
        return destino
    return url_for("dashboard.index")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    email = ""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""

        usuario = Usuario.query.filter_by(email=email).first()

        # Mesma mensagem para email inexistente e senha errada: nao revela
        # quais e-mails estao cadastrados no sistema.
        if usuario is None or not usuario.verificar_senha(senha):
            flash("E-mail ou senha inválidos.", "danger")
        elif not usuario.ativo:
            flash("Usuário desativado. Fale com um administrador.", "danger")
        else:
            login_user(usuario, remember=bool(request.form.get("lembrar")))
            session.permanent = True
            session[MARCA_SENHA] = usuario.senha_hash
            flash(f"Bem-vindo, {usuario.nome}!", "sucesso")
            return redirect(_proximo_destino())

    return render_template(
        "auth/login.html",
        titulo="Login",
        email=email,
        papeis=PAPEIS_ROTULOS,
    )


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    encerrar_sessao()
    flash("Sessão encerrada.", "sucesso")
    return redirect(url_for("auth.login"))


@bp.route("/trocar-senha", methods=["GET", "POST"])
@login_required
def trocar_senha():
    if request.method == "POST":
        senha_atual = request.form.get("senha_atual") or ""
        nova = request.form.get("nova_senha") or ""
        confirmacao = request.form.get("confirmar_senha") or ""

        if not current_user.verificar_senha(senha_atual):
            flash("Senha atual incorreta.", "danger")
        elif len(nova) < 8:
            flash("A nova senha deve ter no mínimo 8 caracteres.", "danger")
        elif nova != confirmacao:
            flash("A confirmação não confere com a nova senha.", "danger")
        else:
            current_user.set_senha(nova)
            # Trocar a senha derruba todos os tokens de API do usuário e
            # invalida as sessoes abertas (ver marca_senha em app/auth.py).
            current_user.revogar_token_api()
            session[MARCA_SENHA] = current_user.senha_hash
            from app.database import db

            db.session.commit()
            flash("Senha alterada com sucesso.", "sucesso")
            return redirect(url_for("auth.trocar_senha"))

    return render_template("auth/trocar_senha.html", titulo="Trocar senha")
