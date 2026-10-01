from app.database import db
from app.models import Atendimento, Medico, Paciente, Procedimento


def _preparar_base(client):
    dados = {}
    with client.application.app_context():
        medico = Medico.query.first()
        proc = Procedimento.query.first()
        paciente = Paciente(nome="Paciente Teste")
        db.session.add(paciente)
        db.session.commit()
        dados = {
            "medico_id": medico.id,
            "procedimento_id": proc.id,
            "paciente_id": paciente.id,
            "preco_procedimento": proc.valor_float,
        }
    return dados


def _dados_validos(base, valor=None, data="2026-09-03"):
    dado = {
        "paciente_id": base["paciente_id"],
        "medico_id": base["medico_id"],
        "procedimento_id": base["procedimento_id"],
        "data_atendimento": data,
        "observacoes": "obs teste",
        "forma_pagamento": "Pix",
    }
    dado["valor"] = valor if valor is not None else str(base["preco_procedimento"]).replace(".", ",")
    return dado


def _criar_atendimento(client, dado):
    return client.post(
        "/atendimentos/novo", data=dado, follow_redirects=True
    )


def test_criar_atendimento(client):
    base = _preparar_base(client)
    res = _criar_atendimento(client, _dados_validos(base))
    assert res.status_code == 200
    with client.application.app_context():
        a = Atendimento.query.first()
        assert a is not None
        assert a.paciente_id == base["paciente_id"]
        assert a.medico_id == base["medico_id"]
        assert a.procedimento_id == base["procedimento_id"]
        assert a.forma_pagamento == "Pix"


def test_consultar_atendimento(client):
    base = _preparar_base(client)
    _criar_atendimento(client, _dados_validos(base))
    res = client.get("/atendimentos/")
    assert res.status_code == 200
    assert "Paciente Teste".encode() in res.data


def test_editar_atendimento(client):
    base = _preparar_base(client)
    _criar_atendimento(client, _dados_validos(base))
    with client.application.app_context():
        a = Atendimento.query.first()
        aid = a.id
    novo_paciente = Paciente(nome="Paciente Editado")
    with client.application.app_context():
        db.session.add(novo_paciente)
        db.session.commit()
        novo_id = novo_paciente.id
    dado = _dados_validos(base)
    dado["paciente_id"] = novo_id
    res = client.post(
        f"/atendimentos/{aid}/editar", data=dado, follow_redirects=True
    )
    assert res.status_code == 200
    with client.application.app_context():
        a = db.session.get(Atendimento, aid)
        assert a.paciente_id == novo_id


def test_excluir_atendimento(client):
    base = _preparar_base(client)
    _criar_atendimento(client, _dados_validos(base))
    with client.application.app_context():
        a = Atendimento.query.first()
        aid = a.id
    res = client.post(f"/atendimentos/{aid}/excluir", follow_redirects=True)
    assert res.status_code == 200
    with client.application.app_context():
        assert db.session.get(Atendimento, aid) is None


def test_validar_campos_obrigatorios(client):
    base = _preparar_base(client)
    dado = _dados_validos(base)
    dado["paciente_id"] = ""
    dado["medico_id"] = ""
    dado["procedimento_id"] = ""
    dado["forma_pagamento"] = ""
    res = client.post("/atendimentos/novo", data=dado, follow_redirects=True)
    assert res.status_code == 400
    with client.application.app_context():
        assert Atendimento.query.count() == 0


def test_validar_relacionamentos(client):
    base = _preparar_base(client)
    dado = _dados_validos(base)
    dado["paciente_id"] = 999999
    res = client.post("/atendimentos/novo", data=dado, follow_redirects=True)
    assert res.status_code == 400
    with client.application.app_context():
        assert Atendimento.query.count() == 0


def test_verificar_preenchimento_valor(client):
    # O valor preenchido automaticamente vem do procedimento no frontend.
    # Aqui garantimos que um valor diferente é armazenado no atendimento.
    base = _preparar_base(client)
    dado = _dados_validos(base, valor="250,00")
    _criar_atendimento(client, dado)
    with client.application.app_context():
        a = Atendimento.query.first()
        assert a.valor_float == 250.0


def test_armazenamento_valor_historico(client):
    # Mesmo que o procedimento mude de preço, o atendimento preserva o valor usado.
    base = _preparar_base(client)
    _criar_atendimento(client, _dados_validos(base, valor="250,00"))
    with client.application.app_context():
        a = Atendimento.query.first()
        aid = a.id
        proc = db.session.get(Procedimento, a.procedimento_id)
        proc.valor = 999
        db.session.commit()
        a = db.session.get(Atendimento, aid)
        assert a.valor_float == 250.0


def test_credito_exige_parcelas(client):
    base = _preparar_base(client)
    dado = _dados_validos(base)
    dado["forma_pagamento"] = "Crédito"
    res = client.post("/atendimentos/novo", data=dado, follow_redirects=True)
    assert res.status_code == 400
    with client.application.app_context():
        assert Atendimento.query.count() == 0


def test_credito_parcelas_validas(client):
    base = _preparar_base(client)
    dado = _dados_validos(base)
    dado["forma_pagamento"] = "Crédito"
    dado["numero_parcelas"] = "3"
    res = _criar_atendimento(client, dado)
    assert res.status_code == 200
    with client.application.app_context():
        a = Atendimento.query.first()
        assert a.forma_pagamento == "Crédito"
        assert a.numero_parcelas == 3


def test_credito_parcelas_fora_do_limite(client):
    base = _preparar_base(client)
    dado = _dados_validos(base)
    dado["forma_pagamento"] = "Crédito"
    dado["numero_parcelas"] = "11"
    res = client.post("/atendimentos/novo", data=dado, follow_redirects=True)
    assert res.status_code == 400


def test_debito_sem_parcelas(client):
    base = _preparar_base(client)
    dado = _dados_validos(base)
    dado["forma_pagamento"] = "Débito"
    res = _criar_atendimento(client, dado)
    assert res.status_code == 200
    with client.application.app_context():
        a = Atendimento.query.first()
        assert a.forma_pagamento == "Débito"
        assert a.numero_parcelas is None


def _app_com_csrf(tmp_path):
    """App isolado com CSRF ligado e um admin logado, para testar o token real."""
    from app import create_app
    from app.database import db
    from app.models import Usuario
    from app.seed import seed_database

    banco = tmp_path / "csrf.db"
    app = create_app(
        config_overrides={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(banco),
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret-csrf",
        }
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_database()
        usuario = Usuario(nome="Admin CSRF", email="csrf@teste.com", papel="admin", ativo=True)
        usuario.set_senha("senha12345")
        db.session.add(usuario)
        db.session.commit()
    return app


def _client_logado(app):
    """Faz login dismissing o CSRF: o proprio login exige token."""
    import re as _re

    client = app.test_client()
    html = client.get("/login").get_data(as_text=True)
    achado = _re.search(r'name="csrf_token"[^>]*value="([^"]*)"', html)
    client.post(
        "/login",
        data={
            "email": "csrf@teste.com",
            "senha": "senha12345",
            "csrf_token": achado.group(1) if achado else "",
        },
    )
    return client


def test_formulario_inclui_token_csrf(tmp_path):
    app = _app_com_csrf(tmp_path)
    with _client_logado(app) as c:
        res = c.get("/atendimentos/novo")
        assert res.status_code == 200
        assert 'name="csrf_token"' in res.get_data(as_text=True)


def test_salvar_atendimento_com_csrf(tmp_path):
    import re
    from app.database import db
    from app.models import Paciente

    app = _app_com_csrf(tmp_path)
    with app.app_context():
        from app.models import Medico, Procedimento

        m = Medico.query.first()
        pr = Procedimento.query.first()
        pa = Paciente(nome="CSRF Paciente")
        db.session.add(pa)
        db.session.commit()
        mid, pid, paid = m.id, pr.id, pa.id

    client = _client_logado(app)
    html = client.get("/atendimentos/novo").get_data(as_text=True)
    token = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', html).group(1)

    # Sem token -> 400
    r = client.post(
        "/atendimentos/novo",
        data={
            "paciente_id": paid,
            "medico_id": mid,
            "procedimento_id": pid,
            "data_atendimento": "03/09/2026",
            "valor": "250,00",
            "forma_pagamento": "Pix",
        },
    )
    assert r.status_code == 400

    # Com token válido -> salva (redirect 302)
    r = client.post(
        "/atendimentos/novo",
        data={
            "paciente_id": paid,
            "medico_id": mid,
            "procedimento_id": pid,
            "data_atendimento": "03/09/2026",
            "valor": "250,00",
            "forma_pagamento": "Pix",
            "csrf_token": token,
        },
    )
    assert r.status_code == 302
