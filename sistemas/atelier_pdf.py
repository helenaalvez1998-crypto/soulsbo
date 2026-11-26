"""Geração de PDF do pacote de criação do Ateliê."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
import re


def _inline_markup(line: str) -> str:
    value = escape(line)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", value)
    value = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", value)
    return value


def _append_text(story, text: str, styles) -> None:
    from reportlab.platypus import Paragraph, Spacer

    for raw_line in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        if line in {"---", "***", "___"}:
            story.append(Spacer(1, 5))
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            story.append(Paragraph(_inline_markup(heading.group(2)), styles[f"Heading{level}"]))
            story.append(Spacer(1, 3))
            continue
        if line.startswith(("- ", "* ")):
            line = "• " + line[2:]
        story.append(Paragraph(_inline_markup(line), styles["BodyTextCustom"]))
        story.append(Spacer(1, 2.5))


def gerar_pdf_atelie(prompt_fixo: str, analise_artisitica: str, referencia_path: str | Path, card_name: str) -> bytes:
    """Gera PDF em ordem: prompt fixo, análise da carta e imagem de referência."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage

    ref_path = Path(referencia_path)
    if not ref_path.is_file():
        raise FileNotFoundError("Imagem de referência visual não encontrada.")
    if not prompt_fixo.strip() or not analise_artisitica.strip():
        raise ValueError("O prompt fixo e a análise artística são obrigatórios para gerar o PDF.")

    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4,
        rightMargin=19 * mm, leftMargin=19 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Narabot - Pacote de criação - {card_name}",
        author="Narabot",
        subject="Prompt fixo, análise artística e referência visual da facção",
    )
    base = getSampleStyleSheet()
    styles = {
        "TitleCustom": ParagraphStyle(
            "TitleCustom", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=18, leading=22, textColor=colors.HexColor("#18243a"),
            alignment=TA_LEFT, spaceAfter=7 * mm,
        ),
        "Heading1": ParagraphStyle(
            "Heading1Custom", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=15, leading=19, textColor=colors.HexColor("#18243a"),
            spaceBefore=4 * mm, spaceAfter=3 * mm,
        ),
        "Heading2": ParagraphStyle(
            "Heading2Custom", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=12, leading=15, textColor=colors.HexColor("#263b58"),
            spaceBefore=3 * mm, spaceAfter=2 * mm,
        ),
        "Heading3": ParagraphStyle(
            "Heading3Custom", parent=base["Heading3"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=13, textColor=colors.HexColor("#344761"),
            spaceBefore=2 * mm, spaceAfter=1.5 * mm,
        ),
        "BodyTextCustom": ParagraphStyle(
            "BodyTextCustom", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9.2, leading=13, textColor=colors.HexColor("#20242b"),
            alignment=TA_LEFT, splitLongWords=True,
        ),
        "Caption": ParagraphStyle(
            "CaptionCustom", parent=base["BodyText"], fontName="Helvetica-Oblique",
            fontSize=8.5, leading=11, textColor=colors.HexColor("#586274"), alignment=TA_CENTER,
        ),
    }

    story = []
    story.append(Paragraph("PROMPT FIXO", styles["TitleCustom"]))
    _append_text(story, prompt_fixo, styles)

    story.append(PageBreak())
    story.append(Paragraph("ANÁLISE ARTÍSTICA (PT) - INFORMAÇÕES DA CARTA", styles["TitleCustom"]))
    story.append(Paragraph(f"Carta: {_inline_markup(card_name)}", styles["BodyTextCustom"]))
    story.append(Spacer(1, 4 * mm))
    _append_text(story, analise_artisitica, styles)

    story.append(PageBreak())
    story.append(Paragraph("REFERÊNCIA VISUAL DA FACÇÃO", styles["TitleCustom"]))
    image = RLImage(str(ref_path))
    max_width = A4[0] - 38 * mm
    max_height = A4[1] - 55 * mm
    scale = min(max_width / image.imageWidth, max_height / image.imageHeight)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    image.hAlign = "CENTER"
    story.append(image)

    def draw_page(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d7dce4"))
        canvas.setLineWidth(0.5)
        canvas.line(19 * mm, 13 * mm, A4[0] - 19 * mm, 13 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawString(19 * mm, 8 * mm, "Narabot - Pacote para criação de carta")
        canvas.drawRightString(A4[0] - 19 * mm, 8 * mm, f"Página {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return output.getvalue()
