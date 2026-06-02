"""FastAPI dependencies."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from pathlib import Path

from fastapi import Depends

from yoruu.api.sse.bus import ValidatingEventBus
from yoruu.config.settings import AppSettings, load_settings
from yoruu.core.loop_runtime import build_trading_loop
from yoruu.core.trading_loop import TradingLoop
from yoruu.data.database import Database
from yoruu.execution.principal_service import PrincipalService
from yoruu.infra.fx_provider import FxRateProvider
from yoruu.infra.ohlc_provider import OhlcProvider
from yoruu.safety.invariants import InvariantChecker
from yoruu.web.event_bus import MemoryEventBus

logger = logging.getLogger(__name__)

_settings: AppSettings | None = None
_event_bus = ValidatingEventBus(MemoryEventBus())
_fx_provider: FxRateProvider | None = None
_ohlc_provider: OhlcProvider | None = None
_trading_loop: TradingLoop | None = None
_loop_task: asyncio.Task | None = None


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


def get_trading_loop() -> TradingLoop | None:
    return _trading_loop


def set_trading_loop(loop: TradingLoop | None) -> None:
    global _trading_loop
    _trading_loop = loop


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


def get_ohlc_provider() -> OhlcProvider:
    global _ohlc_provider
    if _ohlc_provider is None:
        _ohlc_provider = OhlcProvider()
    return _ohlc_provider


def _is_lab_websocket(settings: AppSettings) -> bool:
    return "example.invalid" in settings.websocket.binance_url


async def start_trading_loop(settings: AppSettings) -> asyncio.Task:
    """Background task: shared OhlcProvider + TradingLoop (M6.2)."""

    global _loop_task, _trading_loop, _ohlc_provider
    db = Database(settings.paths.db)
    db.initialize_schema()
    ohlc = get_ohlc_provider()
    loop = build_trading_loop(settings, db, ohlc=ohlc, event_bus=_event_bus)
    set_trading_loop(loop)
    lab = _is_lab_websocket(settings)
    _loop_task = asyncio.create_task(
        loop.run(lab_mock_feed=lab, connect_ws=not lab),
        name="yoruu-trading-loop",
    )
    logger.info("trading_loop_started", extra={"lab_mock_feed": lab})
    return _loop_task


async def shutdown_trading_loop(task: asyncio.Task | None) -> None:
    global _loop_task, _trading_loop
    if _trading_loop is not None:
        _trading_loop.request_stop()
    if task is not None:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    set_trading_loop(None)
    _loop_task = None
