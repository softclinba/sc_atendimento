from app.database import db
from app.models import Procedimento


def _criar_procedimento(client, nome="Procedimento Teste", valor="150,00"):
    return client.post(
        "/procedimentos/novo",
        data={"nome": nome, "valor": valor},
        follow_redirects=True,
    )


def test_criar_procedimento(client):
    res = _criar_procedimento(client)
    assert res.status_code == 200
    with client.application.app_context():
        p = Procedimento.query.filter_by(nome="Procedimento Teste").first()
        assert p is not None
        assert p.valor_float == 150.0


def test_consultar_procedimento(client):
    _criar_procedimento(client)
    res = client.get("/procedimentos/")
    assert res.status_code == 200
    assert "Procedimento Teste".encode() in res.data


def test_editar_procedimento(client):
    _criar_procedimento(client)
    with client.application.app_context():
        p = Procedimento.query.filter_by(nome="Procedimento Teste").first()
        pid = p.id
    res = client.post(
        f"/procedimentos/{pid}/editar",
        data={"nome": "Procedimento Novo", "valor": "200,50"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    with client.application.app_context():
        p = db.session.get(Procedimento, pid)
        assert p.nome == "Procedimento Novo"
        assert p.valor_float == 200.5


def test_excluir_procedimento(client):
    _criar_procedimento(client)
    with client.application.app_context():
        p = Procedimento.query.filter_by(nome="Procedimento Teste").first()
        pid = p.id
    res = client.post(f"/procedimentos/{pid}/excluir", follow_redirects=True)
    assert res.status_code == 200
    with client.application.app_context():
        assert db.session.get(Procedimento, pid) is None


def test_validar_valor_negativo(client):
    res = client.post(
        "/procedimentos/novo",
        data={"nome": "Negativo", "valor": "-10"},
        follow_redirects=True,
    )
    assert res.status_code == 400


def test_validar_nome_obrigatorio(client):
    res = client.post(
        "/procedimentos/novo",
        data={"nome": "", "valor": "10"},
        follow_redirects=True,
    )
    assert res.status_code == 400
