from app.database import db
from app.models import Medico, Procedimento

# ATENÇÃO: estes valores são placeholders.
# Defina aqui os valores reais de cada procedimento.
PROCEDIMENTOS_INICIAIS = [
    {"id": 1, "nome": "Consulta Particular", "valor": 250.00},
    {"id": 2, "nome": "Lente de Contato", "valor": 600.00},
    {"id": 3, "nome": "Teste Ortóptico", "valor": 90.00},
    {"id": 4, "nome": "Exames", "valor": 300.00},
    {"id": 5, "nome": "Outros", "valor": 0},
]

MEDICOS_INICIAIS = [
    "Juliana",
    "Marcela Souza",
    "Nedy Neves",
    "Vilane Dias",
]


def seed_database():
    seed_medicos()
    seed_procedimentos()
    db.session.commit()


def seed_medicos():
    for nome in MEDICOS_INICIAIS:
        existente = Medico.query.filter_by(nome=nome).first()
        if not existente:
            db.session.add(Medico(nome=nome))


def seed_procedimentos():
    for item in PROCEDIMENTOS_INICIAIS:
        existente = Procedimento.query.filter_by(id=item["id"]).first()
        if existente:
            continue
        db.session.add(
            Procedimento(
                id=item["id"],
                nome=item["nome"],
                valor=item["valor"],
            )
        )
