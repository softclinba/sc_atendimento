import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass


# Chave usada apenas em desenvolvimento. ProductionConfig recusa esse valor.
CHAVE_DESENVOLVIMENTO = "chave-de-desenvolvimento-nao-use-em-producao"


def _criar_instancia():
    diretorio = BASE_DIR / "instance"
    diretorio.mkdir(exist_ok=True, parents=True)
    return diretorio


def _montar_uri_banco():
    """Normaliza a DATABASE_URL para drivers obsoletos do SQLAlchemy.

    O.driver //postgres ou postgres2 e aceito pelo SQLAlchemy 1.3, mas o 2.x
    exige +psycopg2 explicito. Convertemos aqui para a mensagem de erro na
    instalacao ser sobre a variavel, e nao sobre o driver.
    """
    uri = os.environ.get("DATABASE_URL")
    if not uri:
        return None

    for prefixo_antigo, prefixo_novo in (
        ("postgresql://", "postgresql+psycopg2://"),
        ("postgres://", "postgresql+psycopg2://"),
        ("mysql://", "mysql+pymysql://"),
    ):
        if uri.startswith(prefixo_antigo):
            return prefixo_novo + uri[len(prefixo_antigo) :]
    return uri


class Config:
    ENV = "development"
    DEBUG = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "sim")

    SECRET_KEY = os.environ.get("SECRET_KEY") or CHAVE_DESENVOLVIMENTO

    BASE_DIR = BASE_DIR
    _instance_dir = _criar_instancia()

    SQLALCHEMY_DATABASE_URI = _montar_uri_banco() or (
        "sqlite:///" + str(_instance_dir / "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FORMAS_PAGAMENTO = ["Dinheiro", "Pix", "Crédito", "Débito"]
    MAX_PARCELAS = 10

    # Sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = True

    PREFERRED_URL_SCHEME = "http"

    # Login
    LOGIN_VIEW = "auth.login"
    LOGIN_MESSAGE = "Faça login para acessar o sistema."
    LOGIN_MESSAGE_CATEGORY = "aviso"


def _exigir_secret_key():
    """Falha imediatamente se a aplicação for subir em produção sem chave real.

    Avaliada no momento da importação deste módulo: um deploy sem SECRET_KEY
    para aqui, em vez de gerar sessões assinadas com um valor previsível.
    """
    chave = os.environ.get("SECRET_KEY")
    if not chave or chave == CHAVE_DESENVOLVIMENTO:
        raise RuntimeError(
            "SECRET_KEY não configurada. Defina a variável de ambiente "
            "SECRET_KEY com um valor aleatório e secreto antes de iniciar "
            "em produção. Exemplo: python -c \"import secrets; "
            "print(secrets.token_hex(32))\""
        )
    return chave


class ProductionConfig(Config):
    """Ativada com FLASK_ENV=production.

    Alem do cookie seguro e do esquema https, exige SECRET_KEY valida. A
    checagem acontece em create_app, e nao na definicao desta classe, para
    que importar o modulo continue possivel em dev e nos testes.
    """

    ENV = "production"
    DEBUG = False

    PREFERRED_URL_SCHEME = "https"

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


def resolver_configuracao():
    if os.environ.get("FLASK_ENV", "").lower() == "production":
        return ProductionConfig
    return Config
