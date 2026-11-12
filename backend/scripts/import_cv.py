"""CLI: import a CV file into the candidate profile (same logic as dashboard upload).

Usage: python -m scripts.import_cv "path/to/cv.pdf"
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.services.candidate_service import import_cv


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"File not found: {path}")
        return 1
    with get_sessionmaker()() as db:
        cv, profile, duplicate, warnings = import_cv(db, get_settings(), path.name, path.read_bytes())
    print(f"CV stored: id={cv.id} sha256={cv.sha256[:12]} duplicate={duplicate}")
    print(f"Profile version {profile.version} (unconfirmed draft)")
    missing = profile.data.get("missing_information", [])
    print(f"Open questions: {len(missing)} ({sum(1 for m in missing if m['critical'])} critical)")
    for w in warnings:
        print(f"WARNING: {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
