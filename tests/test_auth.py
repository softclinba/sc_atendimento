import re


def _token_csrf(client, url):
    html = client.get(url).get_data(as_text=True)
    achado = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', html)
    return achado.group(1) if achado else ""


# ------------------------------------------------------- Login e logout
def test_login_valido_cria_sessao(client_anonimo):
    from tests.conftest import _criar_usuario

    _criar_usuario(client_anonimo.application, "ana@teste.com", papel="admin")
    res = client_anonimo.post(
        "/login", data={"email": "ana@teste.com", "senha": "senha12345"}
    )
    assert res.status_code == 302
    assert "/login" not in res.headers["Location"]

    # A sessao vale de fato: o dashboard deixa de redirecionar.
    assert client_anonimo.get("/").status_code == 200


def test_login_email_normalizado(client_anonimo):
    from tests.conftest import _criar_usuario

    _criar_usuario(client_anonimo.application, "ana@teste.com")
    res = client_anonimo.post(
        "/login", data={"email": "  ANA@Teste.com  ", "senha": "senha12345"}
    )
    assert res.status_code == 302


def test_login_senha_errada_nao_autentica(client_anonimo):
    from tests.conftest import _criar_usuario

    _criar_usuario(client_anonimo.application, "ana@teste.com")
    client_anonimo.post(
        "/login", data={"email": "ana@teste.com", "senha": "senha-errada"}
    )
    assert client_anonimo.get("/").status_code == 302


def test_login_email_inexistente_nao_revela_quais_existem(client_anonimo):
    from tests.conftest import _criar_usuario

    _criar_usuario(client_anonimo.application, "ana@teste.com")
    res = client_anonimo.post(
        "/login", data={"email": "nao-existe@teste.com", "senha": "senha12345"}
    )
    html = res.get_data(as_text=True)
    assert "inv" in html.lower()  # mensagem generica
    assert "ana@teste.com" not in html


def test_login_usuario_inativo_bloqueado(client_anonimo):
    from tests.conftest import _criar_usuario

    _criar_usuario(client_anonimo.application, "inativo@teste.com", ativo=False)
    res = client_anonimo.post(
        "/login", data={"email": "inativo@teste.com", "senha": "senha12345"}
    )
    assert "desativado" in res.get_data(as_text=True).lower()
    assert client_anonimo.get("/").status_code == 302


def test_logout_encerra_sessao(client):
    assert client.get("/").status_code == 200
    res = client.post("/logout")
    assert res.status_code == 302
    assert client.get("/").status_code == 302


# ------------------------------------------- Bloqueio de rotas sem sessao
def test_rota_web_sem_sessao_redireciona_para_login(client_anonimo):
    res = client_anonimo.get("/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_lista_de_pacientes_sem_sessao_redireciona(client_anonimo):
    assert client_anonimo.get("/pacientes/").status_code == 302


def test_pagina_de_login_e_acessivel_sem_sessao(client_anonimo):
    res = client_anonimo.get("/login")
    assert res.status_code == 200
    assert 'name="csrf_token"' in res.get_data(as_text=True)


def test_next_externo_nao_vira_redirect(client_anonimo):
    from tests.conftest import _criar_usuario

    _criar_usuario(client_anonimo.application, "ana@teste.com")
    res = client_anonimo.post(
        "/login",
        data={
            "email": "ana@teste.com",
            "senha": "senha12345",
            "next": "https://site-malicioso.example",
        },
    )
    assert "site-malicioso.example" not in res.headers["Location"]


# ------------------------------------------------------------------- API
def test_api_sem_token_devolve_401(client_anonimo):
    res = client_anonimo.get("/api/pacientes")
    assert res.status_code == 401
    assert "erro" in res.get_json()


def test_api_com_token_valido_responde_200(client_api):
    res = client_api.get("/api/pacientes")
    assert res.status_code == 200


def test_api_com_token_invalido_devolve_401(client_anonimo):
    res = client_anonimo.get(
        "/api/pacientes", headers={"Authorization": "Bearer token-falso"}
    )
    assert res.status_code == 401


def test_api_com_sessao_responde_200(client):
    res = client.get("/api/pacientes")
    assert res.status_code == 200


def test_api_saude_nao_exige_autenticacao(client_anonimo):
    res = client_anonimo.get("/api/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_token_de_usuario_desativado_deixa_de_valer(client_anonimo, app):
    from app.database import db
    from app.models import Usuario
    from tests.conftest import _criar_usuario

    usuario_id = _criar_usuario(app, "api@teste.com")
    with app.app_context():
        usuario = db.session.get(Usuario, usuario_id)
        token = usuario.gerar_token_api()
        db.session.commit()

    assert client_anonimo.get(
        "/api/pacientes", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 200

    with app.app_context():
        db.session.get(Usuario, usuario_id).ativo = False
        db.session.commit()

    assert client_anonimo.get(
        "/api/pacientes", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 401


def test_token_revogado_deixa_de_valer(app, client_anonimo):
    from app.database import db
    from app.models import Usuario
    from tests.conftest import _criar_usuario

    usuario_id = _criar_usuario(app, "api@teste.com")
    with app.app_context():
        usuario = db.session.get(Usuario, usuario_id)
        token = usuario.gerar_token_api()
        db.session.commit()

    with app.app_context():
        db.session.get(Usuario, usuario_id).revogar_token_api()
        db.session.commit()

    assert client_anonimo.get(
        "/api/pacientes", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 401


def test_token_e_uma_soa_vez_por_geracao(app):
    from app.database import db
    from app.models import Usuario
    from tests.conftest import _criar_usuario

    usuario_id = _criar_usuario(app, "api@teste.com")
    with app.app_context():
        usuario = db.session.get(Usuario, usuario_id)
        primeiro = usuario.gerar_token_api()
        db.session.commit()

    with app.app_context():
        usuario = db.session.get(Usuario, usuario_id)
        segundo = usuario.gerar_token_api()
        db.session.commit()

    assert primeiro != segundo
    # O valor em claro nunca e guardado: so o digest.
    with app.app_context():
        usuario = db.session.get(Usuario, usuario_id)
        assert usuario.token_hash not in (primeiro, segundo)
        assert len(usuario.token_hash) == 64


# --------------------------------------------------------------- Perfis
def test_atendente_nao_cria_medico_na_web(client_atendente, app):
    """Na web, a negacao redireciona para o dashboard com aviso."""
    from app.database import db
    from app.models import Medico

    res = client_atendente.post("/medicos/novo", data={"nome": "Dr. Novo"})
    assert res.status_code == 302
    assert "/medicos/novo" not in res.headers["Location"]

    with app.app_context():
        assert Medico.query.filter_by(nome="Dr. Novo").first() is None


def test_atendente_nao_cria_procedimento_na_web(client_atendente, app):
    from app.database import db
    from app.models import Procedimento

    res = client_atendente.post(
        "/procedimentos/novo", data={"nome": "Proc", "valor": "100,00"}
    )
    assert res.status_code == 302

    with app.app_context():
        assert Procedimento.query.filter_by(nome="Proc").first() is None


def test_atendente_consulta_medicos(client_atendente):
    assert client_atendente.get("/medicos/").status_code == 200


def test_atendente_cadastra_paciente(client_atendente):
    res = client_atendente.post("/pacientes/novo", data={"nome": "Paciente Ok"})
    assert res.status_code == 302


def test_atendente_cadastra_atendimento(client_atendente, app):
    from app.database import db
    from app.models import Medico, Paciente, Procedimento

    with app.app_context():
        m = Medico.query.first()
        pr = Procedimento.query.first()
        pa = Paciente(nome="Para Atendimento")
        db.session.add(pa)
        db.session.commit()
        mid, pid, paid = m.id, pr.id, pa.id

    res = client_atendente.post(
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
    assert res.status_code == 302


def test_atendente_recebe_403_na_api(client_atendente):
    res = client_atendente.post("/api/medicos", json={"nome": "Dr. X"})
    assert res.status_code == 403
    assert "erro" in res.get_json()


def test_atendente_pode_ler_api(client_atendente):
    assert client_atendente.get("/api/medicos").status_code == 200


def test_admin_cria_medico_na_web(client):
    res = client.post("/medicos/novo", data={"nome": "Dr. Admin"})
    assert res.status_code == 302


# ------------------------------- Usuarios: area restrita a admin (regressao)
# Estas rotas ficam sob o before_request do blueprint usuarios. Um guarda
# vazio ali liberaria a area administrativa inteira para qualquer visitante,
# sem quebrar nenhum outro teste da suite.


def test_anonimo_nao_acessa_lista_de_usuarios(client_anonimo):
    res = client_anonimo.get("/usuarios/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_anonimo_nao_acessa_formulario_de_novo_usuario(client_anonimo):
    assert client_anonimo.get("/usuarios/novo").status_code == 302


def test_anonimo_nao_acessa_edicao_de_usuario(client_anonimo):
    assert client_anonimo.get("/usuarios/1/editar").status_code == 302


def test_anonimo_nao_cria_usuario(client_anonimo, app):
    from app.database import db
    from app.models import Usuario

    res = client_anonimo.post(
        "/usuarios/novo",
        data={"nome": "Intruso", "email": "intruso@teste.com", "papel": "admin"},
    )
    assert res.status_code == 302

    with app.app_context():
        assert Usuario.query.filter_by(email="intruso@teste.com").first() is None


def test_anonimo_nao_exclui_usuario(client_anonimo, app):
    from app.database import db
    from app.models import Usuario
    from tests.conftest import _criar_usuario

    alvo = _criar_usuario(app, "alvo@teste.com")
    assert client_anonimo.post(f"/usuarios/{alvo}/excluir").status_code == 302

    with app.app_context():
        assert db.session.get(Usuario, alvo) is not None


def test_anonimo_nao_gera_token_de_api(client_anonimo, app):
    from app.database import db
    from app.models import Usuario
    from tests.conftest import _criar_usuario

    alvo = _criar_usuario(app, "alvo@teste.com")
    assert client_anonimo.post(
        f"/usuarios/{alvo}/token", data={"acao": "gerar"}
    ).status_code == 302

    with app.app_context():
        assert db.session.get(Usuario, alvo).token_hash is None


def test_atendente_nao_acessa_area_de_usuarios(client_atendente):
    assert client_atendente.get("/usuarios/").status_code == 302
    assert client_atendente.get("/usuarios/novo").status_code == 302


def test_atendente_nao_cria_usuario_admin(client_atendente, app):
    from app.database import db
    from app.models import Usuario

    res = client_atendente.post(
        "/usuarios/novo",
        data={"nome": "Escalado", "email": "escalado@teste.com", "papel": "admin"},
    )
    assert res.status_code == 302

    with app.app_context():
        assert Usuario.query.filter_by(email="escalado@teste.com").first() is None


def test_admin_acessa_area_de_usuarios(client):
    assert client.get("/usuarios/").status_code == 200
    assert client.get("/usuarios/novo").status_code == 200


def test_nenhuma_rota_de_usuarios_escapa_do_guard(client_anonimo, app):
    """Varre todas as rotas do blueprint e exige que nenhuma responda sem login.

    Cobre rotas futuras: se alguem criar /usuarios/xyz sem pensar na
    permissao, este teste falha mesmo que a rota nova nao tenha caso proprio.
    """
    rotas = [
        str(regra)
        for regra in app.url_map.iter_rules()
        if regra.endpoint.startswith("usuarios.")
        # <usuario_id> e variavel de caminho, nao um id real.
        and "<int:usuario_id>" not in str(regra)
    ]
    assert rotas, "esperava encontrar rotas do blueprint usuarios"

    for rota in rotas:
        res = client_anonimo.get(rota)
        assert res.status_code in (301, 302, 401, 403, 405), (
            f"{rota} respondeu {res.status_code} para visitante anonimo"
        )


# -------------------------------------------------------- Troca de senha
def test_trocar_senha_valida(client, app):
    from app.database import db
    from app.models import Usuario

    res = client.post(
        "/trocar-senha",
        data={
            "senha_atual": "senha12345",
            "nova_senha": "nova-senha-123",
            "confirmar_senha": "nova-senha-123",
        },
    )
    assert res.status_code == 302

    with app.app_context():
        assert db.session.get(Usuario, 1).verificar_senha("nova-senha-123")


def test_trocar_senha_exige_senha_atual_correta(client):
    res = client.post(
        "/trocar-senha",
        data={
            "senha_atual": "errada",
            "nova_senha": "nova-senha-123",
            "confirmar_senha": "nova-senha-123",
        },
    )
    assert "atual incorreta" in res.get_data(as_text=True)


def test_trocar_senha_exige_confirmacao(client):
    res = client.post(
        "/trocar-senha",
        data={
            "senha_atual": "senha12345",
            "nova_senha": "nova-senha-123",
            "confirmar_senha": "outra-coisa",
        },
    )
    assert "confirma" in res.get_data(as_text=True).lower()


def test_trocar_senha_exige_tamanho_minimo(client):
    res = client.post(
        "/trocar-senha",
        data={
            "senha_atual": "senha12345",
            "nova_senha": "curta",
            "confirmar_senha": "curta",
        },
    )
    assert "8 caracteres" in res.get_data(as_text=True)


def test_trocar_senha_invalida_sessoes_anteriores(app, client_anonimo):
    """A senha antiga deixa de funcionar em qualquer sessao."""
    from tests.conftest import _criar_usuario

    _criar_usuario(app, "ana@teste.com")
    client_anonimo.post(
        "/login", data={"email": "ana@teste.com", "senha": "senha12345"}
    )
    assert client_anonimo.get("/").status_code == 200

    client_anonimo.post(
        "/trocar-senha",
        data={
            "senha_atual": "senha12345",
            "nova_senha": "nova-senha-123",
            "confirmar_senha": "nova-senha-123",
        },
    )

    # Uma sessao nova com a senha antiga e recusada.
    outro = app.test_client()
    res = outro.post(
        "/login", data={"email": "ana@teste.com", "senha": "senha12345"}
    )
    assert "inválidos" in res.get_data(as_text=True)

    # Com a nova senha, entra.
    terceiro = app.test_client()
    terceiro.post(
        "/login", data={"email": "ana@teste.com", "senha": "nova-senha-123"}
    )
    assert terceiro.get("/").status_code == 200


def test_trocar_senha_revoga_token_api(app, client):
    from app.database import db
    from app.models import Usuario
    from tests.conftest import _criar_usuario

    usuario_id = _criar_usuario(app, "api@teste.com")
    with app.app_context():
        usuario = db.session.get(Usuario, usuario_id)
        token = usuario.gerar_token_api()
        db.session.commit()

    autenticado = app.test_client()
    autenticado.post(
        "/login", data={"email": "api@teste.com", "senha": "senha12345"}
    )
    autenticado.post(
        "/trocar-senha",
        data={
            "senha_atual": "senha12345",
            "nova_senha": "nova-senha-123",
            "confirmar_senha": "nova-senha-123",
        },
    )

    assert app.test_client().get(
        "/api/pacientes", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 401


def test_senha_nunca_aparece_em_resposta(client, app):
    from app.models import Usuario

    with app.app_context():
        usuario = Usuario.query.first()
        assert usuario.senha_hash
        assert "senha12345" not in usuario.senha_hash
    # Nem no HTML das telas de usuario.
    assert "senha12345" not in client.get("/usuarios/").get_data(as_text=True)
