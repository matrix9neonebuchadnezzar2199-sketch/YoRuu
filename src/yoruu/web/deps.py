"""FastAPI dependencies."""

from __future__ import annotations

from pathlib import Path

from yoruu.config.settings import AppSettings, load_settings
from yoruu.data.database import Database
from yoruu.api.sse.bus import ValidatingEventBus
from yoruu.web.event_bus import MemoryEventBus

_settings: AppSettings | None = None
_event_bus = ValidatingEventBus(MemoryEventBus())


def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = load_settings(Path("config/yoruu.yaml"))
    return _settings


def get_db() -> Database:
    settings = get_settings()
    db = Database(settings.paths.db)
    db.initialize_schema()
    return db


def get_event_bus() -> ValidatingEventBus:
    return _event_bus
