from app.database import db
from app.models import Medico


def _criar_medico(client, nome="Dr. Teste"):
    return client.post(
        "/medicos/novo", data={"nome": nome}, follow_redirects=True
    )


def test_criar_medico(client):
    res = _criar_medico(client)
    assert res.status_code == 200
    with client.application.app_context():
        m = Medico.query.filter_by(nome="Dr. Teste").first()
        assert m is not None


def test_consultar_medico(client):
    _criar_medico(client)
    res = client.get("/medicos/")
    assert res.status_code == 200
    assert "Dr. Teste".encode() in res.data


def test_editar_medico(client):
    _criar_medico(client)
    with client.application.app_context():
        m = Medico.query.filter_by(nome="Dr. Teste").first()
        mid = m.id
    res = client.post(
        f"/medicos/{mid}/editar",
        data={"nome": "Dr. Testão"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    with client.application.app_context():
        assert db.session.get(Medico, mid).nome == "Dr. Testão"


def test_excluir_medico(client):
    _criar_medico(client)
    with client.application.app_context():
        m = Medico.query.filter_by(nome="Dr. Teste").first()
        mid = m.id
    res = client.post(f"/medicos/{mid}/excluir", follow_redirects=True)
    assert res.status_code == 200
    with client.application.app_context():
        assert db.session.get(Medico, mid) is None
