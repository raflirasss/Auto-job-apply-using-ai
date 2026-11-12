"""Apply workflow over a Playwright `page`. Persistence lives in apply_service.py."""

from __future__ import annotations

from pathlib import Path

from app.schemas.candidate import CandidateProfileData
from app.services.apply import page_checks as pc
from app.services.apply.form_detect import validation_errors
from app.services.apply.prepare import NAV_TIMEOUT_MS, RunResult, fail, prepare, stop

__all__ = ["RunResult", "run_application"]


def run_application(page, url: str, profile: CandidateProfileData, files: dict[str, str | None], *,
                    mode: str, screenshot_path: Path | None = None, confirm_wait_ms: int = 15_000) -> RunResult:
    if mode not in {"assisted", "auto"}:
        raise ValueError("mode must be 'assisted' or 'auto'")
    early, labels, unresolved = prepare(page, url, profile, files, screenshot_path)
    if early is not None:
        return early

    if mode == "assisted":
        detail = "Verified fields were filled. Review the form in the opened browser and submit it yourself."
        if unresolved:
            detail += f" {len(unresolved)} field(s) need your input."
        return RunResult("awaiting_user", "manual_review", detail, fields_filled=labels, fields_unresolved=unresolved)

    # ---- auto mode: every rule must pass before clicking submit ----
    kw = {"fields_filled": labels}
    if unresolved:
        return stop(page, "unresolved_fields", "Required fields without a verified answer; nothing was submitted.",
                    screenshot_path, fields_unresolved=unresolved, **kw)
    if invalid := validation_errors(page):
        return stop(page, "validation_failed", "The form reports invalid fields; nothing was submitted.",
                    screenshot_path, fields_unresolved=[f"{x}: invalid" for x in invalid], **kw)
    if (block := pc.blocking_state(page)) is not None:
        return stop(page, *block, screenshot_path, **kw)
    submit = pc.find_button(page, pc.SUBMIT_BUTTON_TEXT)
    if submit is None:
        return stop(page, "no_submit_button", "No unambiguous submit button found; nothing was submitted.", screenshot_path, **kw)
    try:
        submit.click()
        page.wait_for_load_state("domcontentloaded", timeout=NAV_TIMEOUT_MS)
    except Exception as exc:
        return fail(page, "submit_error", f"Submit click failed: {exc.__class__.__name__}", screenshot_path, **kw)

    # Confirmation evidence is mandatory before claiming success.
    for _ in range(max(1, confirm_wait_ms // 500)):
        if (text := pc.confirmation_text(page)) is not None:
            return RunResult("submitted", None, "Submission confirmed by the page.", confirmation=text, **kw)
        if (block := pc.blocking_state(page)) is not None:
            return stop(page, *block, screenshot_path, **kw)
        page.wait_for_timeout(500)
    return stop(page, "no_confirmation",
                "Submit was clicked but no confirmation appeared. Status NOT set to applied; check the site manually.",
                screenshot_path, **kw)
