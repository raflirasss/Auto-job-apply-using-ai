"""Deterministic job matching engine (Phase 3).

Scores, hard filters and recommendations are computed by code only. An optional LLM
may *explain* a result afterwards (see app.services.ai_explainer) but never changes it.
"""

from app.services.matching.engine import ENGINE_VERSION, WEIGHTS, evaluate  # noqa: F401
