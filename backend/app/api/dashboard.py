from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_auth
from app.db.session import get_db
from app.services import stats

router = APIRouter(prefix="/api", tags=["dashboard"], dependencies=[Depends(require_auth)])


@router.get("/dashboard/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    return stats.overview(db)
