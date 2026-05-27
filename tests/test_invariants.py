"""Invariant checker tests (ch16 / ch23)."""

import pytest

from yoruu.data.database import Database
from yoruu.errors import InvariantViolationError
from yoruu.safety.invariants import InvariantChecker
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)
from yoruu.types import Mode, State


def _strategy(version: int = 1) -> StrategyConfig:
    return StrategyConfig(
        version=version,
        parameters=StrategyParameters(
            MIN_PROB=0.87,
            MIN_EDGE=0.06,
            KELLY_FRACTION=0.65,
            PERSISTENCE_THRESHOLD=0.70,
        ),
        constraints={
            "MIN_PROB": ParameterConstraints(min=0.8, max=0.95),
        },
    )


def test_inv_r01_blocks_oversized_trade(tmp_path) -> None:
    db = Database(tmp_path / "db.sqlite")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=Mode.PAPER,
        balance=1000.0,
        daily_loss_limit=30.0,
        strategy_version=1,
    )
    checker = InvariantChecker(db, initial_balance=1000.0)
    with pytest.raises(InvariantViolationError) as exc_info:
        checker.check_pre_trade(size_usd=100.0, max_trade_size=10.0)
    assert exc_info.value.inv_id == "INV-R-01"


def test_inv_d03_version_mismatch(tmp_path) -> None:
    db = Database(tmp_path / "db.sqlite")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=Mode.PAPER,
        balance=1000.0,
        daily_loss_limit=30.0,
        strategy_version=1,
    )
    checker = InvariantChecker(db, initial_balance=1000.0)
    strategy = _strategy(version=2)
    with pytest.raises(InvariantViolationError) as exc_info:
        checker.check_startup(strategy, strategy_path_version=2)
    assert exc_info.value.inv_id == "INV-D-03"


def test_inv_s02_emergency_blocks_trading(tmp_path) -> None:
    db = Database(tmp_path / "db.sqlite")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=Mode.PAPER,
        balance=1000.0,
        daily_loss_limit=30.0,
        strategy_version=1,
    )
    db.set_state(State.EMERGENCY_STOP)
    checker = InvariantChecker(db, initial_balance=1000.0)
    with pytest.raises(InvariantViolationError):
        checker.check_pre_trade(size_usd=5.0, max_trade_size=10.0)
