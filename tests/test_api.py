import os
from datetime import date

from app.database import db
from app.models import Atendimento, Medico, Paciente, Procedimento


def _criar_paciente_api(client, nome="Ana API"):
    return client.post("/api/pacientes", json={"nome": nome})


def _criar_medico_api(client, nome="Dr. API"):
    return client.post("/api/medicos", json={"nome": nome})


def _criar_procedimento_api(client, nome="Proc API", valor="120,50"):
    return client.post(
        "/api/procedimentos", json={"nome": nome, "valor": valor}
    )


def _preparar_entidades(client):
    """Retorna dict com paciente, medico e procedimento criados via API."""
    rp = _criar_paciente_api(client)
    rm = _criar_medico_api(client)
    rpr = _criar_procedimento_api(client)
    return {
        "paciente_id": rp.get_json()["id"],
        "medico_id": rm.get_json()["id"],
        "procedimento_id": rpr.get_json()["id"],
    }


# ------------------------------------------------------------------ Pacientes
def test_api_paciente_crud(client):
    # POST
    r = client.post("/api/pacientes", json={"nome": "Maria"})
    assert r.status_code == 201
    pid = r.get_json()["id"]

    # GET /api/pacientes
    assert client.get("/api/pacientes").status_code == 200

    # GET /api/pacientes/<id>
    r = client.get(f"/api/pacientes/{pid}")
    assert r.status_code == 200
    assert r.get_json()["nome"] == "Maria"

    # PUT
    r = client.put(f"/api/pacientes/{pid}", json={"nome": "Maria Silva"})
    assert r.status_code == 200
    assert r.get_json()["nome"] == "Maria Silva"

    # DELETE
    assert client.delete(f"/api/pacientes/{pid}").status_code == 204
    assert client.get(f"/api/pacientes/{pid}").status_code == 404


def test_api_paciente_nome_obrigatorio(client):
    r = client.post("/api/pacientes", json={"nome": "  "})
    assert r.status_code == 400


def test_api_paciente_404(client):
    assert client.get("/api/pacientes/99999").status_code == 404
    assert client.put("/api/pacientes/99999", json={"nome": "x"}).status_code == 404
    assert client.delete("/api/pacientes/99999").status_code == 404


def test_api_paciente_delete_bloqueado(client):
    ent = _preparar_entidades(client)
    db_dados = {}
    with client.application.app_context():
        a = Atendimento(
            paciente_id=ent["paciente_id"],
            medico_id=ent["medico_id"],
            procedimento_id=ent["procedimento_id"],
            data_atendimento=date(2026, 9, 3),
            valor=250,
            forma_pagamento="Pix",
        )
        db.session.add(a)
        db.session.commit()
    r = client.delete(f"/api/pacientes/{ent['paciente_id']}")
    assert r.status_code == 409


# --------------------------------------------------------------------- Medicos
def test_api_medico_crud(client):
    r = client.post("/api/medicos", json={"nome": "Dr. X"})
    assert r.status_code == 201
    mid = r.get_json()["id"]

    assert client.get("/api/medicos").status_code == 200
    assert client.get(f"/api/medicos/{mid}").status_code == 200

    r = client.put(f"/api/medicos/{mid}", json={"nome": "Dr. Y"})
    assert r.status_code == 200
    assert r.get_json()["nome"] == "Dr. Y"

    assert client.delete(f"/api/medicos/{mid}").status_code == 204
    assert client.get(f"/api/medicos/{mid}").status_code == 404


def test_api_medico_nome_obrigatorio(client):
    assert client.post("/api/medicos", json={"nome": ""}).status_code == 400


# ------------------------------------------------------------- Procedimentos
def test_api_procedimento_crud(client):
    r = client.post("/api/procedimentos", json={"nome": "Consulta", "valor": "150,00"})
    assert r.status_code == 201
    pid = r.get_json()["id"]
    assert r.get_json()["valor"] == 150.0

    assert client.get("/api/procedimentos").status_code == 200
    assert client.get(f"/api/procedimentos/{pid}").status_code == 200

    r = client.put(f"/api/procedimentos/{pid}", json={"nome": "Consulta VIP", "valor": "200"})
    assert r.status_code == 200
    assert r.get_json()["nome"] == "Consulta VIP"
    assert r.get_json()["valor"] == 200.0

    assert client.delete(f"/api/procedimentos/{pid}").status_code == 204
    assert client.get(f"/api/procedimentos/{pid}").status_code == 404


def test_api_procedimento_validacao(client):
    assert client.post("/api/procedimentos", json={"nome": "", "valor": "10"}).status_code == 400
    assert client.post("/api/procedimentos", json={"nome": "X", "valor": "-5"}).status_code == 400


# -------------------------------------------------------------- Atendimentos
def _dados_atendimento(ent):
    return {
        "paciente_id": ent["paciente_id"],
        "medico_id": ent["medico_id"],
        "procedimento_id": ent["procedimento_id"],
        "data_atendimento": "2026-09-03",
        "valor": "250,00",
        "forma_pagamento": "Pix",
        "observacoes": "obs",
    }


def test_api_atendimento_crud(client):
    ent = _preparar_entidades(client)
    r = client.post("/api/atendimentos", json=_dados_atendimento(ent))
    assert r.status_code == 201
    aid = r.get_json()["id"]

    assert client.get("/api/atendimentos").status_code == 200
    r = client.get(f"/api/atendimentos/{aid}")
    assert r.status_code == 200
    assert r.get_json()["valor"] == 250.0

    dados = _dados_atendimento(ent)
    dados["valor"] = "300,00"
    r = client.put(f"/api/atendimentos/{aid}", json=dados)
    assert r.status_code == 200
    assert r.get_json()["valor"] == 300.0

    assert client.delete(f"/api/atendimentos/{aid}").status_code == 204
    assert client.get(f"/api/atendimentos/{aid}").status_code == 404


def test_api_atendimento_validacao(client):
    ent = _preparar_entidades(client)
    dados = _dados_atendimento(ent)
    dados["valor"] = "-1"
    assert client.post("/api/atendimentos", json=dados).status_code == 400

    dados = _dados_atendimento(ent)
    dados["paciente_id"] = 999999
    assert client.post("/api/atendimentos", json=dados).status_code == 400


def test_api_atendimento_credito_parcelas(client):
    ent = _preparar_entidades(client)

    # Crédito sem parcela -> 400
    dados = _dados_atendimento(ent)
    dados["forma_pagamento"] = "Crédito"
    assert client.post("/api/atendimentos", json=dados).status_code == 400

    # Crédito com parcela inválida (0 / 11) -> 400
    dados = _dados_atendimento(ent)
    dados["forma_pagamento"] = "Crédito"
    dados["numero_parcelas"] = 0
    assert client.post("/api/atendimentos", json=dados).status_code == 400

    dados = _dados_atendimento(ent)
    dados["forma_pagamento"] = "Crédito"
    dados["numero_parcelas"] = 11
    assert client.post("/api/atendimentos", json=dados).status_code == 400

    # Crédito válido com 3 parcelas
    dados = _dados_atendimento(ent)
    dados["forma_pagamento"] = "Crédito"
    dados["numero_parcelas"] = 3
    r = client.post("/api/atendimentos", json=dados)
    assert r.status_code == 201
    assert r.get_json()["numero_parcelas"] == 3
    assert r.get_json()["forma_pagamento"] == "Crédito"

    # Débito não exige parcela e numero_parcelas vira None
    dados = _dados_atendimento(ent)
    dados["forma_pagamento"] = "Débito"
    r2 = client.post("/api/atendimentos", json=dados)
    assert r2.status_code == 201
    assert r2.get_json()["numero_parcelas"] is None
