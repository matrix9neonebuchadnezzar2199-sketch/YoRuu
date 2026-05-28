"""RiskGuard unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from yoruu.config.settings import RiskSettings
from yoruu.execution.risk_guard import RiskGuard
from yoruu.types import Side, TradeSignal
from helpers import init_db


def _signal(size: float) -> TradeSignal:
    return TradeSignal(
        side=Side.YES,
        size_usd=size,
        edge=0.07,
        persistence=0.72,
        predicted_prob=0.88,
        market_price=0.81,
    )


def test_daily_loss_blocks_trade(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    db.update_balance_and_pnl(900.0, -35.0)
    guard = RiskGuard(RiskSettings(max_trade_size_usd=10.0, daily_loss_limit_usd=30.0), db)
    assert guard.daily_loss_exceeded() is True
    result = guard.check_pre_trade(_signal(5.0))
    assert result.ok is False
    assert result.reason == "risk_daily_loss"


def test_max_trade_size(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    guard = RiskGuard(RiskSettings(max_trade_size_usd=10.0, daily_loss_limit_usd=30.0), db)
    result = guard.check_pre_trade(_signal(15.0))
    assert result.ok is False
    assert result.reason == "risk_max_trade"


def test_remaining_budget(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    db.update_balance_and_pnl(980.0, -25.0)
    guard = RiskGuard(RiskSettings(max_trade_size_usd=10.0, daily_loss_limit_usd=30.0), db)
    assert guard.remaining_budget() == pytest.approx(5.0)
    result = guard.check_pre_trade(_signal(8.0))
    assert result.ok is False
    assert result.reason == "risk_budget"


def test_insufficient_balance(tmp_path: Path) -> None:
    db = init_db(tmp_path, balance=3.0)
    guard = RiskGuard(RiskSettings(max_trade_size_usd=10.0, daily_loss_limit_usd=30.0), db)
    result = guard.check_pre_trade(_signal(5.0))
    assert result.ok is False
    assert result.reason == "risk_balance"


def test_pre_trade_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    guard = RiskGuard(RiskSettings(max_trade_size_usd=10.0, daily_loss_limit_usd=30.0), db)
    assert guard.check_pre_trade(_signal(5.0)).ok is True
