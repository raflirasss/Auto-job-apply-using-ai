"""Classify a detected form field: sensitive / legal / salary history / mapped fact / unknown."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class FormField:
    """One input detected on a page (built by the browser layer)."""

    selector: str
    label: str
    tag: str  # input | textarea | select
    type: str  # text, email, tel, file, checkbox, radio, number, url, date, select-one, textarea...
    name: str = ""
    required: bool = False
    options: list[str] = field(default_factory=list)  # visible option texts for <select>/radio groups


def _p(*parts: str) -> re.Pattern[str]:
    return re.compile("|".join(parts))


SENSITIVE = _p(
    r"\bnik\b", r"ktp", r"nomor induk", r"national id", r"passport", r"paspor", r"npwp", r"tax id", r"bpjs",
    r"\bbank\b", r"rekening", r"account number", r"religion", r"agama", r"marital", r"status pernikahan", r"ethnic",
    r"\bsuku\b", r"blood", r"golongan darah", r"disab", r"health", r"kesehatan", r"maiden", r"ibu kandung",
    r"date of birth", r"tanggal lahir", r"birth ?date", r"\bdob\b", r"place of birth", r"tempat lahir", r"gender",
    r"jenis kelamin", r"height", r"tinggi badan", r"weight", r"berat badan", r"\bphoto\b", r"\bfoto\b",
    r"password", r"kata sandi", r"\botp\b", r"verification code", r"kode verifikasi",
)
LEGAL = _p(
    r"\bi (hereby )?(agree|declare|certify|confirm|consent|acknowledge)", r"\bterms\b", r"syarat", r"privacy", r"privasi",
    r"consent", r"persetujuan", r"declar", r"pernyataan", r"menyatakan", r"setuju", r"\bagree", r"criminal", r"pidana",
    r"background check", r"accurate and complete", r"benar dan lengkap",
)
SALARY_HISTORY = _p(r"current salary", r"gaji (saat ini|terakhir|sekarang)", r"last salary", r"previous salary", r"salary history")

# Order matters: specific questions first, generic contact fields last.
MAPPINGS: list[tuple[str, re.Pattern[str]]] = [
    ("work_authorization", _p(r"right to work", r"legally (allowed|authori[sz]ed)", r"work permit", r"izin kerja", r"authori[sz]ed to work")),
    ("relocate", _p(r"relocat", r"pindah domisili", r"bersedia (di)?tempatkan")),
    ("expected_salary", _p(r"expected salary", r"salary expectation", r"gaji (yang )?diharapkan", r"ekspektasi gaji", r"desired salary")),
    ("availability", _p(r"start date", r"available to start", r"availability", r"tanggal mulai", r"notice period", r"bisa mulai")),
    ("resume", _p(r"\bcv\b", r"resume", r"curriculum", r"riwayat hidup")),
    ("cover_letter", _p(r"cover letter", r"surat lamaran", r"motivation letter", r"application letter")),
    ("website", _p(r"portfolio", r"website", r"personal site")),
    ("location", _p(r"domisili", r"current location", r"\bcity\b", r"\bkota\b", r"where do you live", r"\blokasi\b")),
    ("email", _p(r"e-?mail", r"surel")),
    ("phone", _p(r"phone", r"mobile", r"telepon", r"\btelp\b", r"\bhp\b", r"handphone", r"whatsapp")),
    ("first_name", _p(r"first name", r"given name", r"nama depan")),
    ("last_name", _p(r"last name", r"surname", r"family name", r"nama belakang")),
    ("full_name", _p(r"full ?name", r"nama lengkap", r"your name", r"^name$", r"^nama$")),
]
QUESTION = re.compile(r"\?|\b(why|how|what|describe|explain|tell us|ceritakan|jelaskan|mengapa|bagaimana|apa)\b")


def _match(text: str, f: FormField) -> str | None:
    for key, pattern in MAPPINGS:
        if pattern.search(text) and (key in {"resume", "cover_letter"}) == (f.type == "file"):
            return key
    return None


def classify(f: FormField) -> tuple[str, str | None]:
    """Return (category, key). category: sensitive | legal | salary_history | mapped | unknown.

    The visible label decides; the HTML `name` attribute is only consulted when there is no label.
    """
    label = f.label.lower().strip()
    text = label or f.name.lower().replace("_", " ").replace("-", " ").strip()
    if f.type == "password" or SENSITIVE.search(text):
        return "sensitive", None
    if f.type in {"checkbox", "radio"} and LEGAL.search(text):
        return "legal", None
    if SALARY_HISTORY.search(text):
        return "salary_history", None
    key = _match(text, f)
    # Free-text questions ("Why do you want ...?") are never treated as contact fields.
    if key in {"email", "phone", "first_name", "last_name", "full_name", "location", "website"} and QUESTION.search(text) \
            and f.type in {"textarea", "text"} and len(text) > 40:
        key = None
    if key:
        return "mapped", key
    if f.type == "file":
        return "mapped", "resume"  # a lone unlabeled upload on an application form is the CV
    return "unknown", None
