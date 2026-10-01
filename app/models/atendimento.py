from datetime import datetime, timezone

from app.database import db


class Atendimento(db.Model):
    __tablename__ = "atendimento"

    id = db.Column(db.Integer, primary_key=True)

    paciente_id = db.Column(db.Integer, db.ForeignKey("paciente.id"), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey("medico.id"), nullable=False)
    procedimento_id = db.Column(
        db.Integer, db.ForeignKey("procedimento.id"), nullable=False
    )

    data_atendimento = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    observacoes = db.Column(db.Text, nullable=True)
    forma_pagamento = db.Column(db.String(50), nullable=False)
    numero_parcelas = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    paciente = db.relationship("Paciente", back_populates="atendimentos")
    medico = db.relationship("Medico", back_populates="atendimentos")
    procedimento = db.relationship("Procedimento", back_populates="atendimentos")

    @property
    def valor_float(self):
        return float(self.valor) if self.valor is not None else 0.0

    def __repr__(self):
        return f"<Atendimento {self.id}: {self.data_atendimento}>"
