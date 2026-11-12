"""Layout-aware text extraction from CV files (PDF via PyMuPDF, DOCX via python-docx).

PDF content streams often list section headings after their content, so lines are
re-ordered by their on-page position (top-to-bottom, then left-to-right).
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

ROW_TOLERANCE_PT = 2.5
SUPPORTED_MIME = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


class CVExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class Line:
    text: str
    x0: float
    y0: float
    page: int
    page_width: float
    is_bullet: bool = False
    is_bold: bool = False


@dataclass
class ExtractedCV:
    lines: list[Line]
    page_count: int
    warnings: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)


BULLET_CHARS = "•●▪■◦‣∙·-–*"


def _strip_bullet(text: str) -> tuple[str, bool]:
    stripped = text.lstrip()
    if stripped and stripped[0] in BULLET_CHARS and (len(stripped) == 1 or stripped[1] == " "):
        return stripped[1:].strip(), True
    return stripped.strip(), False


def detect_kind(filename: str, content: bytes) -> str:
    if content.startswith(b"%PDF-"):
        return "pdf"
    if content.startswith(b"PK") and filename.lower().endswith(".docx"):
        return "docx"
    raise CVExtractionError("Unsupported file type. Upload a PDF or DOCX CV.")


def extract_pdf(content: bytes) -> ExtractedCV:
    import pymupdf

    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as exc:  # pymupdf raises various internal errors
        raise CVExtractionError(f"Could not open PDF: {exc.__class__.__name__}") from exc
    if doc.needs_pass:
        raise CVExtractionError("PDF is password-protected. Upload an unlocked copy.")

    lines: list[Line] = []
    for page_no, page in enumerate(doc):
        raw: list[tuple[float, float, str, bool]] = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for ln in block["lines"]:
                spans = [s for s in ln["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = " ".join("".join(s["text"] for s in ln["spans"]).split())
                bold = all((s.get("flags", 0) & 16) or "bold" in s.get("font", "").lower() for s in spans)
                raw.append((spans[0]["bbox"][1], spans[0]["bbox"][0], text, bold))
        raw.sort(key=lambda r: (r[0], r[1]))
        rows: list[list[tuple[float, float, str, bool]]] = []
        for item in raw:
            if rows and abs(item[0] - rows[-1][0][0]) <= ROW_TOLERANCE_PT:
                rows[-1].append(item)
            else:
                rows.append([item])
        for row in rows:
            for y, x, text, bold in sorted(row, key=lambda r: r[1]):
                clean, bullet = _strip_bullet(text)
                if clean:
                    lines.append(Line(clean, x, y, page_no, page.rect.width, bullet, bold))

    result = ExtractedCV(lines=lines, page_count=doc.page_count)
    if sum(len(line.text) for line in lines) < 200:
        result.warnings.append(
            "Very little text was found. The PDF may be a scanned image; OCR is not supported, "
            "so please upload a text-based PDF or DOCX."
        )
    return result


def extract_docx(content: bytes) -> ExtractedCV:
    import docx

    try:
        document = docx.Document(io.BytesIO(content))
    except Exception as exc:
        raise CVExtractionError(f"Could not open DOCX: {exc.__class__.__name__}") from exc

    page_width = 600.0
    lines: list[Line] = []
    y = 0.0

    def add_paragraph(par) -> None:
        nonlocal y
        text = par.text.strip()
        if not text:
            return
        style = (par.style.name or "").lower() if par.style is not None else ""
        indent = par.paragraph_format.left_indent
        indented = "list" in style or (indent is not None and indent.pt > 5)
        bold = bool(par.runs) and all(r.bold for r in par.runs if r.text.strip())
        parts = [p.strip() for p in par.text.split("\t") if p.strip()]
        y += 10
        first, bullet = _strip_bullet(parts[0])
        lines.append(Line(first, 60.0 if indented or bullet else 40.0, y, 0, page_width, bullet or indented, bold))
        for extra in parts[1:]:  # tab-separated right column (dates / locations)
            lines.append(Line(extra, 450.0, y, 0, page_width, False, False))

    for par in document.paragraphs:
        add_paragraph(par)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for par in cell.paragraphs:
                    add_paragraph(par)

    result = ExtractedCV(lines=lines, page_count=1)
    if sum(len(line.text) for line in lines) < 200:
        result.warnings.append("Very little text was found in the DOCX file.")
    result.warnings.append("DOCX layout information is limited; review the extracted profile carefully.")
    return result


def extract_cv(filename: str, content: bytes) -> tuple[str, ExtractedCV]:
    kind = detect_kind(filename, content)
    return kind, (extract_pdf(content) if kind == "pdf" else extract_docx(content))
