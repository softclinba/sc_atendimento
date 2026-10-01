import os
import re
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.database import db


def _criar_usuario(app, email, senha="senha12345", papel="atendente", ativo=True):
    from app.models import Usuario

    with app.app_context():
        usuario = Usuario(nome=email.split("@")[0].title(), email=email, papel=papel, ativo=ativo)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        return usuario.id


def _token_csrf(client, url):
    html = client.get(url).get_data(as_text=True)
    achado = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', html)
    return achado.group(1) if achado else None


@pytest.fixture()
def app(tmp_path):
    banco = tmp_path / "test.db"
    app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(banco),
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        from app.seed import seed_database

        seed_database()
    yield app


@pytest.fixture()
def client(app):
    """Cliente com sessao de admin.

    E o padrao dos testes existentes: as rotas web e de /api exigem
    autenticacao, entao a maioria dos testes precisa de um usuario logado.
    Para verificar o comportamento sem sessao, use client_anonimo.
    """
    _criar_usuario(app, "admin@teste.com", papel="admin")
    client = app.test_client()
    client.post(
        "/login",
        data={"email": "admin@teste.com", "senha": "senha12345"},
        follow_redirects=False,
    )
    return client


@pytest.fixture()
def client_anonimo(app):
    """Cliente sem sessao, para testar os bloqueios de acesso."""
    return app.test_client()


@pytest.fixture()
def client_atendente(app):
    """Cliente com sessao iniciada como atendente (sem privilegios de admin)."""
    _criar_usuario(app, "atendente@teste.com", papel="atendente")
    client = app.test_client()
    client.post(
        "/login",
        data={"email": "atendente@teste.com", "senha": "senha12345"},
        follow_redirects=False,
    )
    return client


@pytest.fixture()
def client_api(app):
    """Cliente com header Authorization: Bearer de um admin."""
    from app.auth import _digest

    usuario_id = _criar_usuario(app, "api@teste.com", papel="admin")
    with app.app_context():
        from app.models import Usuario

        usuario = db.session.get(Usuario, usuario_id)
        token = usuario.gerar_token_api()
        db.session.commit()

    client = app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client


@pytest.fixture()
def token_api(app):
    """Token de API em texto claro, para testes de curl."""
    from app.auth import _digest

    usuario_id = _criar_usuario(app, "api@teste.com", papel="admin")
    with app.app_context():
        from app.models import Usuario

        usuario = db.session.get(Usuario, usuario_id)
        token = usuario.gerar_token_api()
        db.session.commit()
        return token


@pytest.fixture()
def seeded(app):
    from app.models import Medico, Procedimento

    with app.app_context():
        return {
            "medico": Medico.query.first(),
            "procedimento": Procedimento.query.first(),
        }
