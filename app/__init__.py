import os

import click
from flask import Flask, jsonify, render_template, request
from flask_login import current_user
from flask_migrate import Migrate  # pyright: ignore[reportMissingImports]
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from app.config import resolver_configuracao
from app.database import db

static_folder = os.path.join(os.path.dirname(__file__), "static")
template_folder = os.path.join(os.path.dirname(__file__), "templates")

csrf = CSRFProtect()
migrate = Migrate()


def create_app(config_class=None, config_overrides=None):
    if config_class is None:
        config_class = resolver_configuracao()

    app = Flask(
        __name__,
        static_folder=static_folder,
        template_folder=template_folder,
    )
    app.config.from_object(config_class)

    if app.config.get("ENV") == "production":
        from app.config import _exigir_secret_key

        # Trava o deploy: sem chave real nao sobe nenhuma sessao valida.
        app.config["SECRET_KEY"] = _exigir_secret_key()

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    migrate.init_app(app, db, compare_type=True)
    csrf.init_app(app)

    from app.auth import registrar_login

    registrar_login(app)

    # Importar o pacote registra todos os modelos no SQLAlchemy, o que e
    # necessario para o Alembic enxergar as tabelas.
    from app.models import Usuario  # noqa: F401

    from app.routes import (
        api,
        atendimentos,
        auth,
        dashboard,
        medicos,
        pacientes,
        procedimentos,
        usuarios,
    )

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(pacientes.bp)
    app.register_blueprint(medicos.bp)
    app.register_blueprint(procedimentos.bp)
    app.register_blueprint(atendimentos.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(usuarios.bp)

    # A API e autenticada por token (Authorization: Bearer) ou por sessao.
    # Como nao usa cookie para autenticacao, fica fora do CSRF de formulario.
    # O cookie de sessao usa SameSite=Lax, que ja impede o envio em POST
    # originado por outro site.
    for regra in app.url_map.iter_rules():
        if regra.endpoint.startswith("api."):
            csrf.exempt(app.view_functions[regra.endpoint])

    from app.context_processors import _register_context_processors

    _register_context_processors(app)

    @app.template_filter("brl")
    def brl(value):
        if value is None:
            value = 0
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @app.template_filter("brnum")
    def brnum(value):
        if value is None:
            value = 0
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @app.template_filter("brdate")
    def brdate(value):
        if value is None:
            return ""
        return value.strftime("%d/%m/%Y")

    @app.errorhandler(404)
    def not_found(e):
        return (
            render_template(
                "erros.html", titulo="Página não encontrada",
                codigo=404, mensagem="O registro ou página solicitado não foi encontrado.",
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return (
            render_template(
                "erros.html", titulo="Erro interno",
                codigo=500, mensagem="Ocorreu um erro interno. Tente novamente em instantes.",
            ),
            500,
        )

    _registrar_comandos(app)

    return app


def _registrar_comandos(app):
    @app.cli.command("seed")
    def comando_seed():
        """Popula medicos e procedimentos iniciais (idempotente)."""
        from app.seed import seed_database

        seed_database()
        click.echo("Seed aplicado.")

    @app.cli.command("criar-usuario")
    @click.option("--nome", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--senha", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option(
        "--papel", type=click.Choice(["admin", "atendente"]), default="admin", show_default=True
    )
    def comando_criar_usuario(nome, email, senha, papel):
        """Cria um usuario do sistema."""
        from app.models import Usuario

        email = email.strip().lower()
        if Usuario.query.filter_by(email=email).first():
            click.echo(f"Erro: ja existe um usuario com o e-mail {email}.")
            raise SystemExit(1)
        if len(senha) < 8:
            click.echo("Erro: a senha deve ter no minimo 8 caracteres.")
            raise SystemExit(1)

        usuario = Usuario(nome=nome.strip(), email=email, papel=papel, ativo=True)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuario {email} criado com perfil {papel}.")
