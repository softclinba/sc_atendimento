import hashlib

from flask import jsonify, request, session
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    logout_user,
)
from functools import wraps

from app.database import db
from app.models import Usuario

login_manager = LoginManager()

# Chave de sessao que guarda uma copia do hash da senha no momento do login.
# Se a senha mudar, a copia deixa de bater e as sessoes antigas caem sozinhas.
MARCA_SENHA = "marca_senha"


def _digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@login_manager.user_loader
def carregar_usuario(user_id):
    try:
        usuario = db.session.get(Usuario, int(user_id))
    except (TypeError, ValueError):
        return None
    if usuario is None or not usuario.ativo:
        return None
    marca = session.get(MARCA_SENHA)
    if marca is not None and marca != usuario.senha_hash:
        session.pop(MARCA_SENHA, None)
        return None
    return usuario


@login_manager.request_loader
def carregar_usuario_token_api(request):
    """Autentica chamadas de API por token, sem depender de cookie de sessao.

    O token concede exatamente os mesmos poderes que o login do usuario, entao
    deve ser tratado como uma senha: pessoal e revogavel.
    """
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        return None
    token = cabecalho[7:].strip()
    if not token:
        return None
    return Usuario.query.filter_by(token_hash=_digest(token), ativo=True).first()


def exigir_api_token(fn):
    """Protege um endpoint de /api. Devolve 401 em JSON, nunca redirect."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"erro": "Autenticação necessária."}), 401
        return fn(*args, **kwargs)
    return wrapper


def exigir_admin(fn):
    """Exige perfil admin. Em rotas de /api responde 403 em JSON."""
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.eh_admin:
            if request.path.startswith("/api/"):
                return jsonify({"erro": "Permissão insuficiente."}), 403
            return _sem_permissao()
        return fn(*args, **kwargs)
    return wrapper


def _sem_permissao():
    from flask import flash, redirect, url_for

    flash("Você não tem permissão para acessar esta área.", "danger")
    return redirect(url_for("dashboard.index"))


def registrar_login(app):
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def nao_autenticado():
        if request.path.startswith("/api/"):
            return jsonify({"erro": "Autenticação necessária."}), 401
        return redirect_para_login()

    return login_manager


def redirect_para_login():
    from flask import flash, redirect, url_for

    flash("Faça login para acessar o sistema.", "aviso")
    return redirect(url_for("auth.login"))


def encerrar_sessao():
    logout_user()
    session.pop(MARCA_SENHA, None)


def exigir_sessao_web(bp):
    """Exige sessao autenticada em todas as rotas de um blueprint web.

    Registrado no modulo do blueprint, e nao em create_app: blueprints sao
    singletons de modulo, e o Flask recusa altera-los depois do registro.
    """
    @bp.before_request
    def _guarda():
        if not current_user.is_authenticated:
            return redirect_para_login()
        return None

    return _guarda


def exigir_token_api(bp, endpoint_livre=None):
    """Exige autenticacao (token ou sessao) em todas as rotas de /api.

    endpoint_livre identifica a rota que responde sem autenticacao, usada
    pela verificacao de disponibilidade.
    """
    @bp.before_request
    def _guarda():
        if endpoint_livre is not None and request.endpoint == endpoint_livre:
            return None
        if not current_user.is_authenticated:
            return jsonify({"erro": "Autenticação necessária."}), 401
        return None

    return _guarda


__all__ = [
    "MARCA_SENHA",
    "current_user",
    "encerrar_sessao",
    "exigir_admin",
    "exigir_api_token",
    "exigir_sessao_web",
    "exigir_token_api",
    "login_manager",
    "login_required",
    "registrar_login",
]
