"""PDF rendering (ReportLab Platypus). Real selectable text, single column: ATS-friendly."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.documents.content import TailoredResume
from app.services.documents.render_docx import H
from app.services.documents.templates import Template


def _clean(text: str) -> str:
    """Escape XML and drop characters the standard PDF fonts cannot encode (cp1252)."""
    safe = "".join(ch if ch in "\n\t" or ch.encode("cp1252", errors="ignore") else "" for ch in text)
    return escape(safe).replace("\n", "<br/>")


def _styles(t: Template) -> dict[str, ParagraphStyle]:
    accent = HexColor(t.accent)
    base = ParagraphStyle("base", fontName=t.pdf_font, fontSize=10, leading=13.5)
    return {
        "base": base,
        "name": ParagraphStyle("name", parent=base, fontName=t.pdf_font_bold, fontSize=18, leading=22, textColor=accent,
                               alignment=TA_CENTER if t.centered_header else TA_LEFT),
        "contact": ParagraphStyle("contact", parent=base, fontSize=9.5, alignment=TA_CENTER if t.centered_header else TA_LEFT),
        "h": ParagraphStyle("h", parent=base, fontName=t.pdf_font_bold, fontSize=11, textColor=accent, spaceBefore=9, spaceAfter=1),
        "bold": ParagraphStyle("bold", parent=base, fontName=t.pdf_font_bold),
        "right": ParagraphStyle("right", parent=base, fontName=t.pdf_font + "-Oblique" if t.pdf_font == "Helvetica" else t.pdf_font, alignment=2),
        "para": ParagraphStyle("para", parent=base, fontSize=10.5, leading=15, spaceAfter=8),
    }


def _heading(story: list, text: str, s: dict, t: Template) -> None:
    story.append(Paragraph(_clean(text), s["h"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor(t.accent), spaceAfter=4))


def _row(left: str, right: str, s: dict, bold: bool) -> Table:
    tbl = Table([[Paragraph(_clean(left), s["bold"] if bold else s["base"]), Paragraph(_clean(right), s["right"])]],
                colWidths=[11.5 * cm, 5.5 * cm])
    tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0)]))
    return tbl


def _bullets(items: list[str], s: dict) -> ListFlowable:
    return ListFlowable([ListItem(Paragraph(_clean(i), s["base"]), leftIndent=12) for i in items],
                        bulletType="bullet", start="•", leftIndent=12, bulletFontSize=8)


def _doc(path: Path, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm,
                             bottomMargin=1.6 * cm, title=title, author="", subject="", creator="")


def render_resume_pdf(resume: TailoredResume, lang: str, t: Template, path: Path) -> None:
    h, s = H[lang], _styles(t)
    story: list = [Paragraph(_clean(resume.name), s["name"]), Paragraph(_clean(" | ".join(resume.contact)), s["contact"])]
    if resume.summary:
        _heading(story, h["summary"], s, t)
        story.append(Paragraph(_clean(resume.summary), s["base"]))
    if resume.experience:
        _heading(story, h["exp"], s, t)
        for e in resume.experience:
            story += [_row(e.company, e.dates, s, True), _row(e.title, e.location, s, False)]
            if e.bullets:
                story.append(_bullets(e.bullets, s))
            story.append(Spacer(1, 5))
    if resume.education:
        _heading(story, h["edu"], s, t)
        for inst, degree, dates, location in resume.education:
            story += [_row(inst, dates, s, True), _row(degree, location, s, False)]
    if resume.skill_groups or resume.languages:
        _heading(story, h["skills"], s, t)
        lines = ([(h["key"], resume.relevant_skills)] if resume.relevant_skills else []) + resume.skill_groups
        if resume.languages:
            lines.append((h["lang"], resume.languages))
        for cat, items in lines:
            story.append(Paragraph(f"<b>{_clean(cat)}:</b> {_clean(', '.join(items))}", s["base"]))
    for key, items in (("cert", resume.certifications), ("ach", resume.achievements)):
        if items:
            _heading(story, h[key], s, t)
            story.append(_bullets(items, s))
    if resume.projects:
        _heading(story, h["proj"], s, t)
        for name, desc in resume.projects:
            story.append(Paragraph(f"<b>{_clean(name)}</b>" + (f" — {_clean(desc)}" if desc else ""), s["base"]))
    _doc(path, "Curriculum Vitae").build(story)


def render_letter_pdf(name: str, contact: list[str], paragraphs: list[str], date_text: str, t: Template, path: Path) -> None:
    s = _styles(t)
    left_name = ParagraphStyle("ln", parent=s["name"], fontSize=14, leading=18, alignment=TA_LEFT)
    story: list = [Paragraph(_clean(name), left_name), Paragraph(_clean(" | ".join(contact)), s["base"]), Spacer(1, 14),
                   Paragraph(_clean(date_text), s["para"])]
    story += [Paragraph(_clean(p), s["para"]) for p in paragraphs]
    _doc(path, "Cover Letter").build(story)
