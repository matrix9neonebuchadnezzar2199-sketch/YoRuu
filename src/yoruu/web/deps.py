"""FastAPI dependencies."""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends

from yoruu.api.sse.bus import ValidatingEventBus
from yoruu.config.settings import AppSettings, load_settings
from yoruu.data.database import Database
from yoruu.execution.principal_service import PrincipalService
from yoruu.infra.fx_provider import FxRateProvider
from yoruu.safety.invariants import InvariantChecker
from yoruu.web.event_bus import MemoryEventBus

_settings: AppSettings | None = None
_event_bus = ValidatingEventBus(MemoryEventBus())
_fx_provider: FxRateProvider | None = None


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


def get_principal_service(db: Database = Depends(get_db)) -> PrincipalService:
    """PrincipalService with invariant checks (M4.4/M4.5)."""

    settings = get_settings()
    invariants = InvariantChecker(
        db,
        initial_principal=settings.resolved_initial_principal,
    )
    return PrincipalService(
        db,
        max_deposit_per_tx=settings.principal.max_deposit_per_tx,
        max_withdraw_per_tx=settings.principal.max_withdraw_per_tx,
        require_confirm_on_withdraw=settings.principal.require_confirm_on_withdraw,
        invariant_checker=invariants,
    )


def get_fx_provider() -> FxRateProvider:
    global _fx_provider
    if _fx_provider is None:
        _fx_provider = FxRateProvider(get_settings().display.fx)
    return _fx_provider
