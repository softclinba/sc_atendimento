import csv
import io
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.atendimento_service import listar_atendimentos_filtrados


def _dados_exportacao(atendimentos):
    dados = []
    for a in atendimentos:
        dados.append(
            {
                "id": a.id,
                "data_atendimento": a.data_atendimento.isoformat(),
                "paciente": a.paciente.nome if a.paciente else "",
                "medico": a.medico.nome if a.medico else "",
                "procedimento": (
                    a.procedimento.nome if a.procedimento else ""
                ),
                "valor": a.valor_float,
                "forma_pagamento": a.forma_pagamento,
                "numero_parcelas": a.numero_parcelas,
                "observacoes": a.observacoes or "",
            }
        )
    return dados


def gerar_csv(atendimentos):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "ID",
            "Data de Atendimento",
            "Paciente",
            "Médico",
            "Procedimento",
            "Valor",
            "Forma de Pagamento",
            "Número de Parcelas",
            "Observações",
        ]
    )
    for a in atendimentos:
        writer.writerow(
            [
                a.id,
                a.data_atendimento.isoformat(),
                a.paciente.nome if a.paciente else "",
                a.medico.nome if a.medico else "",
                a.procedimento.nome if a.procedimento else "",
                f"{a.valor_float:.2f}",
                a.forma_pagamento,
                a.numero_parcelas or "",
                (a.observacoes or "").replace("\n", " "),
            ]
        )
    # UTF-8 with BOM para compatibilidade com Excel
    conteudo = buffer.getvalue()
    return "\ufeff" + conteudo


def gerar_json(atendimentos):
    dados = _dados_exportacao(atendimentos)
    return json.dumps(dados, ensure_ascii=False, indent=4)


def gerar_csv_bytes(atendimentos):
    csv_str = gerar_csv(atendimentos)
    return csv_str.encode("utf-8")


def gerar_json_bytes(atendimentos):
    return gerar_json(atendimentos).encode("utf-8")


def nome_arquivo(extensao):
    return f"atendimentos_{datetime.now().strftime('%Y-%m-%d')}.{extensao}"


def exportar_csv(request_args):
    atendimentos = listar_atendimentos_filtrados(request_args).order_by(
        "data_atendimento"
    ).all()
    return gerar_csv_bytes(atendimentos), nome_arquivo("csv")


def exportar_json(request_args):
    atendimentos = listar_atendimentos_filtrados(request_args).order_by(
        "data_atendimento"
    ).all()
    return gerar_json_bytes(atendimentos), nome_arquivo("json")


def _registrar_fonte():
    pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(
        TTFont("ArialBold", r"C:\Windows\Fonts\arialbd.ttf")
    )


def _renderizar_pdf(atendimentos):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="Atendimentos",
        author="SOFT Clínica",
    )

    _registrar_fonte()

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "Titulo", parent=estilos["Title"], fontName="ArialBold", fontSize=16
    )
    corpo = ParagraphStyle(
        "Corpo",
        parent=estilos["Normal"],
        fontName="Arial",
        fontSize=9,
        leading=11,
    )
    cab_desalinhado = ParagraphStyle(
        "CabDesalinhado",
        parent=corpo,
        fontName="ArialBold",
        textColor=colors.white,
    )
    cab_alin_dir = ParagraphStyle(
        "CabDir",
        parent=cab_desalinhado,
        alignment=2,
    )
    cab_centro = ParagraphStyle(
        "CabCentro",
        parent=cab_desalinhado,
        alignment=1,
    )
    cel_dir = ParagraphStyle(
        "CelDir",
        parent=corpo,
        alignment=2,
    )
    cel_centro = ParagraphStyle(
        "CelCentro",
        parent=corpo,
        alignment=1,
    )

    historico = []

    def rodapé(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Arial", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(
            doc_.pagesize[0] / 2, 6 * mm, f"SOFT Clínica — Página {doc_.page}"
        )
        canvas.restoreState()

    total_geral = sum(a.valor_float for a in atendimentos)

    dados = [[
        Paragraph("Data", cab_desalinhado),
        Paragraph("Paciente", cab_desalinhado),
        Paragraph("Médico", cab_desalinhado),
        Paragraph("Procedimento", cab_desalinhado),
        Paragraph("Valor", cab_alin_dir),
        Paragraph("Pagamento", cab_desalinhado),
        Paragraph("Parcelas", cab_centro),
    ]]
    for a in atendimentos:
        dados.append([
            Paragraph(a.data_atendimento.strftime("%d/%m/%Y"), corpo),
            Paragraph(a.paciente.nome if a.paciente else "", corpo),
            Paragraph(a.medico.nome if a.medico else "", corpo),
            Paragraph(a.procedimento.nome if a.procedimento else "", corpo),
            Paragraph(f"R$ {a.valor_float:,.2f}".replace(",", "X").replace(
                ".", ",").replace("X", "."), cel_dir),
            Paragraph(a.forma_pagamento, corpo),
            Paragraph(f"{a.numero_parcelas}x" if a.numero_parcelas else "", cel_centro),
        ])
    dados.append([
        Paragraph("Total", cab_desalinhado),
        Paragraph("", corpo),
        Paragraph("", corpo),
        Paragraph("", corpo),
        Paragraph(
            f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace(
                "X", "."),
            cel_dir,
        ),
        Paragraph("", corpo),
        Paragraph("", corpo),
    ])

    larguras = [24 * mm, 52 * mm, 48 * mm, 58 * mm, 30 * mm, 32 * mm, 22 * mm]
    tabela = Table(dados, colWidths=larguras, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f7a6a")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#eef5f3")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d9ece8")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c7c4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    historico.append(Spacer(1, 4 * mm))
    historico.append(Paragraph("Relatório de Atendimentos", titulo))
    historico.append(Spacer(1, 2 * mm))
    historico.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} — "
        f"{len(atendimentos)} atendimento(s)",
        corpo,
    ))
    historico.append(Spacer(1, 4 * mm))
    historico.append(tabela)

    doc.build(historico, onFirstPage=rodapé, onLaterPages=rodapé)
    return buffer.getvalue()


def gerar_pdf_bytes(atendimentos):
    return _renderizar_pdf(atendimentos)


def exportar_pdf(request_args):
    atendimentos = listar_atendimentos_filtrados(request_args).order_by(
        "data_atendimento"
    ).all()
    return gerar_pdf_bytes(atendimentos), nome_arquivo("pdf")
