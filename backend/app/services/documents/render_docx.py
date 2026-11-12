"""DOCX rendering (python-docx). Single column, standard font, no tables/images: ATS-friendly."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app.services.documents.content import TailoredResume
from app.services.documents.templates import Template

H = {"en": {"summary": "PROFILE", "skills": "SKILLS", "exp": "WORK EXPERIENCE", "edu": "EDUCATION",
            "cert": "CERTIFICATIONS", "proj": "PROJECTS", "ach": "ACHIEVEMENTS", "lang": "Languages", "key": "Relevant skills"},
     "id": {"summary": "PROFIL", "skills": "KEAHLIAN", "exp": "PENGALAMAN KERJA", "edu": "PENDIDIKAN",
            "cert": "SERTIFIKASI", "proj": "PROYEK", "ach": "PENCAPAIAN", "lang": "Bahasa", "key": "Keahlian relevan"}}


def _rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.lstrip("#").upper())


def _base(t: Template) -> Document:
    doc = Document()
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(1.8)
        s.left_margin = s.right_margin = Cm(2.0)
    style = doc.styles["Normal"]
    style.font.name = t.docx_font
    style.element.rPr.rFonts.set(qn("w:eastAsia"), t.docx_font)
    style.font.size = Pt(10.5)
    style.paragraph_format.space_after = Pt(2)
    doc.core_properties.title = "Curriculum Vitae"
    doc.core_properties.author = ""
    return doc


def _heading(doc: Document, text: str, t: Template) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = _rgb(t.accent)
    # bottom border line
    pPr = p._p.get_or_add_pPr()
    border = pPr.makeelement(qn("w:pBdr"), {})
    bottom = border.makeelement(qn("w:bottom"), {qn("w:val"): "single", qn("w:sz"): "6", qn("w:space"): "1", qn("w:color"): t.accent.lstrip("#")})
    border.append(bottom)
    pPr.append(border)


def _left_right(doc: Document, left: str, right: str, bold: bool = False) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.tab_stops.add_tab_stop(Cm(17.0), alignment=2)  # right-aligned tab
    r = p.add_run(left)
    r.bold = bold
    if right:
        p.add_run("\t" + right).italic = True


def render_resume_docx(resume: TailoredResume, lang: str, t: Template, path: Path) -> None:
    h = H[lang]
    doc = _base(t)
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER if t.centered_header else WD_ALIGN_PARAGRAPH.LEFT
    run = title.add_run(resume.name)
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = _rgb(t.accent)
    contact = doc.add_paragraph(" | ".join(resume.contact))
    contact.alignment = title.alignment

    if resume.summary:
        _heading(doc, h["summary"], t)
        doc.add_paragraph(resume.summary)
    if resume.experience:
        _heading(doc, h["exp"], t)
        for e in resume.experience:
            _left_right(doc, e.company, e.dates, bold=True)
            _left_right(doc, e.title, e.location)
            for b in e.bullets:
                doc.add_paragraph(b, style="List Bullet")
    if resume.education:
        _heading(doc, h["edu"], t)
        for inst, degree, dates, location in resume.education:
            _left_right(doc, inst, dates, bold=True)
            _left_right(doc, degree, location)
    if resume.skill_groups or resume.languages:
        _heading(doc, h["skills"], t)
        if resume.relevant_skills:
            p = doc.add_paragraph()
            p.add_run(f"{h['key']}: ").bold = True
            p.add_run(", ".join(resume.relevant_skills))
        for cat, skills in resume.skill_groups:
            p = doc.add_paragraph()
            p.add_run(f"{cat}: ").bold = True
            p.add_run(", ".join(skills))
        if resume.languages:
            p = doc.add_paragraph()
            p.add_run(f"{h['lang']}: ").bold = True
            p.add_run(", ".join(resume.languages))
    for key, items in (("cert", resume.certifications), ("ach", resume.achievements)):
        if items:
            _heading(doc, h[key], t)
            for i in items:
                doc.add_paragraph(i, style="List Bullet")
    if resume.projects:
        _heading(doc, h["proj"], t)
        for name, desc in resume.projects:
            p = doc.add_paragraph()
            p.add_run(name).bold = True
            if desc:
                p.add_run(f" — {desc}")
    doc.save(str(path))


def render_letter_docx(name: str, contact: list[str], paragraphs: list[str], date_text: str, t: Template, path: Path) -> None:
    doc = _base(t)
    head = doc.add_paragraph()
    r = head.add_run(name)
    r.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = _rgb(t.accent)
    doc.add_paragraph(" | ".join(contact))
    doc.add_paragraph(date_text).paragraph_format.space_before = Pt(12)
    for para in paragraphs:
        p = doc.add_paragraph(para)
        p.paragraph_format.space_after = Pt(8)
    doc.save(str(path))
