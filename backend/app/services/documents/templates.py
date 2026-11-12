"""Reusable CV templates. Both are single-column and ATS-safe; they differ in styling only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    key: str
    name: str
    accent: str
    docx_font: str
    pdf_font: str
    pdf_font_bold: str
    centered_header: bool


TEMPLATES: dict[str, Template] = {
    "classic": Template("classic", "Classic", "#1F3A5F", "Calibri", "Helvetica", "Helvetica-Bold", True),
    "modern": Template("modern", "Modern", "#4338CA", "Arial", "Helvetica", "Helvetica-Bold", False),
}
DEFAULT_TEMPLATE = "classic"


def get_template(key: str | None) -> Template:
    return TEMPLATES.get(key or DEFAULT_TEMPLATE, TEMPLATES[DEFAULT_TEMPLATE])
