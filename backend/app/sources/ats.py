"""Company career boards on Lever and Greenhouse via their documented public Job Board APIs.

GET endpoints are public by design ("Job Board data is publicly available"; Lever: "all job postings in
the published state are publicly viewable"). The owner lists company board tokens (e.g. Greenhouse
"xendit", Lever "ninjavan"); listings outside the accepted locations are dropped early.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.matching.location import location_matches
from app.sources.base import FetchContext, FetchResult, JobSourceAdapter, SourceJob
from app.sources.http import Blocked, PoliteClient
from app.sources.text import arrangement_from, clean, html_to_text, work_type_from

INDONESIA = ("indonesia", "jakarta", "tangerang", "bekasi", "depok", "bogor", "remote")


def _in_scope(location: str | None, ctx: FetchContext) -> bool:
    if not location:
        return True
    if ctx.accepted_locations and location_matches(location, ctx.accepted_locations):
        return True
    return any(k in location.lower() for k in INDONESIA)


def _ms(ts) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
    except (TypeError, ValueError):
        return None


def lever_job(company: str, p: dict) -> SourceJob:
    cats = p.get("categories") or {}
    lists = "\n".join(f"{l.get('text', '')}:\n{html_to_text(l.get('content')) or ''}" for l in p.get("lists") or [])
    desc = "\n\n".join(x for x in (p.get("descriptionPlain") or html_to_text(p.get("description")), lists,
                                   p.get("additionalPlain")) if x)
    salary = p.get("salaryRange") or {}
    unit = {"per-year-salary": "annual", "per-month-salary": "monthly", "per-week-salary": "weekly", "per-day-wage": "daily"}
    structured = (salary.get("currency") or "").upper() == "IDR" and salary.get("interval") in unit
    return SourceJob(
        source="lever", external_id=f"lever:{company}:{p['id']}", url=p.get("hostedUrl") or "",
        title=clean(p.get("text")) or "", company=company, location=cats.get("location"),
        work_arrangement={"remote": "remote", "hybrid": "hybrid", "on-site": "onsite"}.get((p.get("workplaceType") or "").lower())
        or arrangement_from(cats.get("location")),
        employment_type=work_type_from(cats.get("commitment")), description=clean(desc),
        salary_min=salary.get("min") if structured else None, salary_max=salary.get("max") if structured else None,
        salary_period=unit.get(salary.get("interval"), "monthly"),
        apply_url=p.get("applyUrl") or p.get("hostedUrl"), posted_at=_ms(p.get("createdAt")),
        notes=[f"Lever board '{company}'."],
    )


def greenhouse_job(board: str, j: dict) -> SourceJob:
    location = (j.get("location") or {}).get("name")
    updated = j.get("updated_at") or j.get("first_published")
    return SourceJob(
        source="greenhouse", external_id=f"greenhouse:{board}:{j['id']}", url=j.get("absolute_url") or "",
        title=clean(j.get("title")) or "", company=j.get("company_name") or board, location=location,
        work_arrangement=arrangement_from(location), description=html_to_text(j.get("content")),
        apply_url=j.get("absolute_url"),
        posted_at=datetime.fromisoformat(updated) if updated else None,
        notes=[f"Greenhouse board '{board}'."],
    )


class AtsAdapter(JobSourceAdapter):
    name = "ats"
    label = "Company career boards (Lever, Greenhouse)"

    def __init__(self, client_factory=PoliteClient):
        self._client_factory = client_factory

    def fetch(self, config: dict, ctx: FetchContext) -> FetchResult:
        result = FetchResult()
        lever, greenhouse = config.get("lever", []), config.get("greenhouse", [])
        if not lever and not greenhouse:
            result.notes.append("No company boards configured.")
            return result
        since = datetime.now(timezone.utc) - timedelta(days=max(ctx.lookback_days, 30))  # boards keep jobs open longer
        with self._client_factory() as http:
            for company in lever:
                try:
                    data = http.get(f"https://api.lever.co/v0/postings/{company}?mode=json").json()
                    jobs = [lever_job(company, p) for p in data if isinstance(p, dict) and p.get("id")]
                except Blocked as exc:
                    result.errors.append(f"Lever '{company}': {exc}")
                    continue
                except Exception as exc:
                    result.errors.append(f"Lever '{company}': {exc.__class__.__name__}")
                    continue
                result.jobs += [j for j in jobs if _in_scope(j.location, ctx) and (not j.posted_at or j.posted_at >= since)]
            for board in greenhouse:
                try:
                    data = http.get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true").json()
                    jobs = [greenhouse_job(board, j) for j in data.get("jobs", []) if j.get("id")]
                except Blocked as exc:
                    result.errors.append(f"Greenhouse '{board}': {exc}")
                    continue
                except Exception as exc:
                    result.errors.append(f"Greenhouse '{board}': {exc.__class__.__name__}")
                    continue
                result.jobs += [j for j in jobs if _in_scope(j.location, ctx) and (not j.posted_at or j.posted_at >= since)]
            result.requests = http.requests
        result.jobs = result.jobs[: ctx.max_items]
        return result
