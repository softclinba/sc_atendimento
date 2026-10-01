from datetime import datetime, timezone

from app.database import db


class Procedimento(db.Model):
    __tablename__ = "procedimento"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    atendimentos = db.relationship(
        "Atendimento", back_populates="procedimento", passive_deletes=True
    )

    @property
    def valor_float(self):
        return float(self.valor) if self.valor is not None else 0.0

    def __repr__(self):
        return f"<Procedimento {self.id}: {self.nome}>"
