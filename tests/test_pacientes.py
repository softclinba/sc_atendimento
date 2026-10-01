from app.database import db
from app.models import Paciente


def _criar_paciente(client, nome="Maria Silva"):
    return client.post(
        "/pacientes/novo", data={"nome": nome}, follow_redirects=True
    )


def test_criar_paciente(client):
    res = _criar_paciente(client)
    assert res.status_code == 200
    with client.application.app_context():
        p = Paciente.query.filter_by(nome="Maria Silva").first()
        assert p is not None
        assert p.nome == "Maria Silva"


def test_consultar_paciente(client):
    _criar_paciente(client)
    res = client.get("/pacientes/")
    assert res.status_code == 200
    assert "Maria Silva".encode() in res.data


def test_editar_paciente(client):
    _criar_paciente(client)
    with client.application.app_context():
        p = Paciente.query.filter_by(nome="Maria Silva").first()
        pid = p.id
    res = client.post(
        f"/pacientes/{pid}/editar",
        data={"nome": "Maria Santos"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    with client.application.app_context():
        p = db.session.get(Paciente, pid)
        assert p.nome == "Maria Santos"


def test_excluir_paciente(client):
    _criar_paciente(client)
    with client.application.app_context():
        p = Paciente.query.filter_by(nome="Maria Silva").first()
        pid = p.id
    res = client.post(
        f"/pacientes/{pid}/excluir", follow_redirects=True
    )
    assert res.status_code == 200
    with client.application.app_context():
        assert db.session.get(Paciente, pid) is None


def test_validar_nome_obrigatorio(client):
    res = client.post(
        "/pacientes/novo", data={"nome": "   "}, follow_redirects=True
    )
    assert res.status_code == 400
    with client.application.app_context():
        assert Paciente.query.count() == 0
