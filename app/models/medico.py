from datetime import datetime, timezone

from app.database import db


class Medico(db.Model):
    __tablename__ = "medico"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    atendimentos = db.relationship(
        "Atendimento", back_populates="medico", passive_deletes=True
    )

    def __repr__(self):
        return f"<Medico {self.id}: {self.nome}>"
