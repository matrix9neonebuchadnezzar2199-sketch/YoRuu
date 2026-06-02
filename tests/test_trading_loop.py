"""TradingLoop integration (PHASE 6 M6.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import init_db, write_isolated_config
from yoruu.config.settings import load_settings
from yoruu.core.clock import VirtualClock
from yoruu.core.loop_runtime import build_trading_loop
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)
from yoruu.types import State


@pytest.fixture
def strategy_config() -> StrategyConfig:
    return StrategyConfig(
        version=1,
        parameters=StrategyParameters(
            MIN_PROB=0.55,
            MIN_EDGE=0.03,
            KELLY_FRACTION=0.65,
            PERSISTENCE_THRESHOLD=0.70,
        ),
        constraints={
            "MIN_PROB": ParameterConstraints(min=0.5, max=0.95),
            "MIN_EDGE": ParameterConstraints(min=0.01, max=0.15),
            "KELLY_FRACTION": ParameterConstraints(min=0.10, max=1.00),
            "PERSISTENCE_THRESHOLD": ParameterConstraints(min=0.50, max=0.90),
        },
    )


@pytest.mark.asyncio
async def test_trading_loop_lab_entry_and_expire(
    tmp_path: Path, strategy_config: StrategyConfig
) -> None:
    for name in ("logs", "historical", "reports"):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    cfg = write_isolated_config(tmp_path, strategy_config)
    settings = load_settings(cfg)
    db = init_db(tmp_path, balance=1000.0)
    clock = VirtualClock()
    loop = build_trading_loop(settings, db, clock=clock, interval_sec=1)
    loop._clock = clock  # noqa: SLF001

    for price in range(100, 125):
        from yoruu.types import PriceTick

        await loop.on_tick(
            PriceTick(
                source="BINANCE",
                symbol="BTCUSDT",
                price=float(price),
                ts_iso=clock.now().isoformat(),
            )
        )
        clock.advance(1.0)

    stats = await loop.run(
        max_evaluations=5,
        lab_mock_feed=False,
        connect_ws=False,
    )
    assert stats.evaluations >= 1
    if stats.entries >= 1:
        clock.advance(301.0)
        await loop.evaluate_cycle()
        assert loop._sm.current() in (State.IDLE, State.MONITORING_POSITION)  # noqa: SLF001


@pytest.mark.asyncio
async def test_trading_loop_max_evaluations(
    tmp_path: Path, strategy_config: StrategyConfig
) -> None:
    for name in ("logs", "historical", "reports"):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    cfg = write_isolated_config(tmp_path, strategy_config)
    settings = load_settings(cfg)
    db = init_db(tmp_path)
    loop = build_trading_loop(settings, db, interval_sec=1)
    stats = await loop.run(max_evaluations=3, lab_mock_feed=True, connect_ws=False)
    assert stats.evaluations == 3
