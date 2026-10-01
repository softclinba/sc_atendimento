import hashlib
import secrets
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db

PAPEIS = ("admin", "atendente")


class Usuario(db.Model, UserMixin):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    papel = db.Column(db.String(20), nullable=False, default="atendente")
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    # Guardamos apenas o hash do token. O valor em claro aparece uma unica
    # vez, no momento em que e gerado, e nunca e recuperado depois.
    token_hash = db.Column(db.String(64), nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        if not self.senha_hash or senha is None:
            return False
        return check_password_hash(self.senha_hash, senha)

    def gerar_token_api(self):
        token = secrets.token_urlsafe(32)
        self.token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return token

    def revogar_token_api(self):
        self.token_hash = None

    def tem_token_api(self):
        return bool(self.token_hash)

    @property
    def eh_admin(self):
        return self.papel == "admin"

    @property
    def is_active(self):
        return bool(self.ativo)

    def __repr__(self):
        return f"<Usuario {self.id}: {self.email}>"
