"""Settings persistence: DB is the source of truth, config/*.json are seed defaults and
are re-written on every save so the files always mirror the dashboard state."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import AppSetting
from app.schemas.settings import Preferences, SchedulerConfig, SourcesConfig

log = logging.getLogger(__name__)
M = TypeVar("M", bound=BaseModel)

SETTING_FILES: dict[str, tuple[str, type[BaseModel]]] = {
    "preferences": ("preferences.json", Preferences),
    "sources": ("sources.json", SourcesConfig),
    "scheduler": ("scheduler.json", SchedulerConfig),
}


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _load_file(settings: Settings, key: str) -> dict | None:
    filename, _ = SETTING_FILES[key]
    path = settings.config_dir / filename
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_setting(db: Session, settings: Settings, key: str) -> BaseModel:
    _, model = SETTING_FILES[key]
    row = db.get(AppSetting, key)
    if row is not None:
        try:
            return model.model_validate(row.value)
        except ValidationError:
            if key != "sources":
                raise
            # Saved in the old (pre-RSS/Telegram) format: migrate to config/sources.json or defaults.
            value = _file_or_default(settings, key, model)
            row.value = value.model_dump(mode="json")
            db.commit()
            return value
    raw = _load_file(settings, key)
    if raw is None and key == "preferences":
        raise RuntimeError("config/preferences.json is missing")
    value = _file_or_default(settings, key, model)
    db.add(AppSetting(key=key, value=value.model_dump(mode="json")))
    db.commit()
    return value


def _file_or_default(settings: Settings, key: str, model: type[BaseModel]) -> BaseModel:
    raw = _load_file(settings, key)
    if raw is None:
        return model.model_validate({})
    try:
        return model.model_validate(raw)
    except ValidationError:
        if key != "sources":
            raise
        return model()


def save_setting(db: Session, settings: Settings, key: str, value: BaseModel) -> BaseModel:
    filename, model = SETTING_FILES[key]
    validated = model.model_validate(value.model_dump())
    data = validated.model_dump(mode="json")
    row = db.get(AppSetting, key)
    if row is None:
        db.add(AppSetting(key=key, value=data))
    else:
        row.value = data
    db.commit()
    try:
        atomic_write_json(settings.config_dir / filename, data)
    except OSError as exc:  # DB remains authoritative
        log.warning("Could not mirror %s to disk: %s", filename, exc.__class__.__name__)
    return validated
