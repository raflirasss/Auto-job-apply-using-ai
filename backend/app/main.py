from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.api import agent, apply, auth, candidate, connections, dashboard, documents, jobs, sources, settings as settings_api
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import get_engine


def create_app(*, start_scheduler: bool | None = None) -> FastAPI:
    configure_logging()
    settings = get_settings()
    use_scheduler = settings.enable_scheduler if start_scheduler is None else start_scheduler

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        from app.services.agent.scheduler import agent_scheduler
        from app.services.apply.email_service import apply_by_email
        from app.services.apply.service import apply_job

        if use_scheduler:
            agent_scheduler.apply_fn = apply_job
            agent_scheduler.email_fn = apply_by_email
            agent_scheduler.start()
        try:
            yield
        finally:
            agent_scheduler.shutdown()

    app = FastAPI(
        title="AI Job Hunter API",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs" if settings.app_env != "production" else None,
        openapi_url="/api/openapi.json" if settings.app_env != "production" else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        db_ok = True
        try:
            with get_engine().connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_ok = False
        return {"status": "ok" if db_ok else "degraded", "database": db_ok, "version": __version__}

    app.include_router(auth.router)
    app.include_router(candidate.router)
    app.include_router(jobs.router)
    app.include_router(documents.router)
    app.include_router(settings_api.router)
    app.include_router(dashboard.router)
    app.include_router(apply.router)
    app.include_router(agent.router)
    app.include_router(sources.router)
    app.include_router(connections.router)
    return app


app = create_app()
