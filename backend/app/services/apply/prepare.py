"""Shared browser steps for both modes: open, check, open form, detect, fill verified fields."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.services.apply import page_checks as pc
from app.services.apply.fields import FieldDecision, blockers, decide, filled_labels
from app.services.apply.form_detect import detect_fields, fill

NAV_TIMEOUT_MS = 30_000


@dataclass
class RunResult:
    outcome: str  # submitted | awaiting_user | stopped | failed
    stop_reason: str | None = None
    detail: str = ""
    confirmation: str | None = None
    fields_filled: list[str] = field(default_factory=list)
    fields_unresolved: list[str] = field(default_factory=list)
    screenshot: str | None = None


def shot(page, path: Path | None) -> str | None:
    """Viewport-only screenshot (not full page) to limit captured personal data."""
    if path is None:
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=False)
        return str(path)
    except Exception:
        return None


def stop(page, reason: str, detail: str, path: Path | None, **kw) -> RunResult:
    return RunResult("stopped", reason, detail, screenshot=shot(page, path), **kw)


def fail(page, reason: str, detail: str, path: Path | None, **kw) -> RunResult:
    return RunResult("failed", reason, detail, screenshot=shot(page, path), **kw)


def _open_form(page) -> None:
    """If no fillable field is visible yet, click one clear 'Apply' button."""
    if any(f.type not in {"checkbox", "radio", "file"} for f in detect_fields(page)):
        return
    btn = pc.find_button(page, pc.APPLY_BUTTON_TEXT)
    if btn is not None:
        btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT_MS)


def prepare(page, url: str, profile, files, path: Path | None) -> tuple[RunResult | None, list[str], list[str]]:
    """Returns (early_result_or_None, filled_labels, unresolved_blockers)."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    except Exception as exc:
        return fail(page, "navigation_error", f"Could not open the page: {exc.__class__.__name__}", path), [], []
    state = pc.listing_state(page)
    if state == "closed":
        return stop(page, "job_closed", "The listing says it is closed or expired.", path), [], []
    if state == "already_applied":
        return stop(page, "already_applied", "The site reports you already applied to this job.", path), [], []
    if (block := pc.blocking_state(page)) is not None:
        return stop(page, *block, path), [], []
    try:
        _open_form(page)
    except Exception as exc:
        return fail(page, "apply_button_error", f"Could not open the application form: {exc.__class__.__name__}", path), [], []
    if (block := pc.blocking_state(page)) is not None:
        return stop(page, *block, path), [], []
    fields = detect_fields(page)
    if not fields:
        return stop(page, "no_form_detected", "No application form was detected on the page.", path), [], []

    decisions: list[FieldDecision] = decide(fields, profile, files)
    done: list[FieldDecision] = []
    for d in decisions:
        if d.action in {"fill", "upload", "select"}:
            try:
                fill(page, d)
                done.append(d)
            except Exception as exc:
                d.action, d.reason = "block", f"could not fill automatically ({exc.__class__.__name__})"
    return None, filled_labels(done), blockers(decisions)
