"""Optional LLM explanation of an existing match result.

The LLM receives the engine's result and anonymised profile facts (no name, email, phone,
website, or domicile) and returns prose only. Its output is stored as text and never
parsed back into scores, filters or recommendations.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.schemas.candidate import CandidateProfileData
from app.services.ai_config import ResolvedAIConfig

log = logging.getLogger(__name__)
TIMEOUT_SECONDS = 45
MAX_DESCRIPTION_CHARS = 6000

SYSTEM_PROMPT = (
    "You explain job-match results to a job seeker. The score, hard-filter results and "
    "recommendation were computed by a deterministic engine and are final: never change, "
    "dispute or re-score them. Use only facts present in the input; never invent skills, "
    "experience or qualifications. Write 3-6 short sentences in plain English: why the job "
    "fits or not, the most important gaps, and what to verify on the listing."
)


class AIExplanationError(RuntimeError):
    pass


def anonymised_profile(profile: CandidateProfileData) -> dict:
    return {
        "summary": profile.summary,
        "education": [e.model_dump(include={"degree", "field_of_study", "end_date", "is_expected"}) for e in profile.education],
        "experience": [e.model_dump(include={"title", "start_date", "end_date", "responsibilities"}) for e in profile.experience],
        "skills": [g.model_dump() for g in profile.skills],
        "languages": [lang.model_dump() for lang in profile.languages],
    }


def build_messages(job, result: dict, profile: CandidateProfileData) -> list[dict]:
    payload = {
        "job": {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": (job.description or "")[:MAX_DESCRIPTION_CHARS],
        },
        "engine_result": {k: result[k] for k in (
            "score", "components", "matching_skills", "missing_skills", "relevant_experience",
            "concerns", "hard_filter_failures", "recommendation",
        )},
        "candidate": anonymised_profile(profile),
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def explain(job, result: dict, profile: CandidateProfileData, cfg: ResolvedAIConfig, client: httpx.Client | None = None) -> str:
    """Call an OpenAI-compatible /chat/completions endpoint. Raises AIExplanationError on failure."""
    if not cfg.configured:
        raise AIExplanationError("AI provider is not configured (base URL, model and API key are required).")
    url = cfg.base_url.rstrip("/") + "/chat/completions"
    body = {"model": cfg.model, "messages": build_messages(job, result, profile), "temperature": 0.2, "max_tokens": 400}
    own_client = client is None
    client = client or httpx.Client(timeout=TIMEOUT_SECONDS)
    try:
        response = client.post(url, json=body, headers={"Authorization": f"Bearer {cfg.api_key}"})
    except httpx.HTTPError as exc:
        raise AIExplanationError(f"AI request failed: {exc.__class__.__name__}") from exc
    finally:
        if own_client:
            client.close()
    if response.status_code != 200:
        raise AIExplanationError(f"AI provider returned HTTP {response.status_code}.")
    try:
        text = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AIExplanationError("AI provider returned an unexpected response format.") from exc
    if not isinstance(text, str) or not text.strip():
        raise AIExplanationError("AI provider returned an empty explanation.")
    return text.strip()[:4000]
