"""PaperExecutor integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import init_db
from yoruu.config.settings import PaperSettings
from yoruu.errors import InvariantViolationError
from yoruu.execution.fill_model import FillModel
from yoruu.execution.paper_executor import CloseRequest, OpenRequest, PaperExecutor
from yoruu.safety.invariants import InvariantChecker
from yoruu.types import CloseReason, Mode, OrderBook, Side


def _book(*, ask_size: float = 100.0, spread: float = 0.02) -> OrderBook:
    return OrderBook(
        market="BTC_5MIN_UPDOWN",
        best_bid=0.79,
        best_ask=0.81,
        bid_size_usd=100.0,
        ask_size_usd=ask_size,
        spread=spread,
        captured_at_iso="2026-01-01T00:00:00+00:00",
        source="MOCK",
    )


def _open_request(**kwargs: object) -> OpenRequest:
    defaults = {
        "market": "BTC_5MIN_UPDOWN",
        "side": Side.YES,
        "size_usd": 5.0,
        "expected_price": 0.81,
        "book": _book(),
        "mode": Mode.PAPER,
        "strategy_version": 1,
        "edge": 0.07,
        "persistence": 0.72,
    }
    defaults.update(kwargs)
    return OpenRequest(**defaults)  # type: ignore[arg-type]


def test_open_success(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    checker = InvariantChecker(db, initial_balance=1000.0)
    executor = PaperExecutor(
        db,
        FillModel(PaperSettings(), seed=1),
        invariant_checker=checker,
        max_trade_size_usd=10.0,
        daily_loss_limit=30.0,
    )
    fill = executor.open(_open_request())
    assert fill.success is True
    assert fill.trade_id is not None
    assert db.get_balance() == pytest.approx(995.0)


def test_open_rejects_wide_spread(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    executor = PaperExecutor(db, FillModel(PaperSettings(), seed=1))
    fill = executor.open(_open_request(book=_book(spread=0.50)))
    assert fill.success is False
    assert fill.error is not None
    assert fill.error.code == "E_FILL_002"


def test_open_invariant_oversize(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    checker = InvariantChecker(db, initial_balance=1000.0)
    executor = PaperExecutor(
        db,
        FillModel(PaperSettings(), seed=1),
        invariant_checker=checker,
        max_trade_size_usd=10.0,
    )
    with pytest.raises(InvariantViolationError) as exc_info:
        executor.open(_open_request(size_usd=50.0))
    assert exc_info.value.inv_id == "INV-R-01"


def test_close_round_trip(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    checker = InvariantChecker(db, initial_balance=1000.0)
    executor = PaperExecutor(
        db,
        FillModel(PaperSettings(), seed=2),
        invariant_checker=checker,
        max_trade_size_usd=10.0,
    )
    opened = executor.open(_open_request(size_usd=5.0))
    assert opened.trade_id is not None
    closed = executor.close(
        CloseRequest(
            position_id=1,
            trade_id=opened.trade_id,
            side=Side.YES,
            size_usd=5.0,
            book=_book(),
            reason=CloseReason.EXPIRATION,
        )
    )
    assert closed.success is True
    assert closed.fill_price is not None


def test_close_missing_trade(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    executor = PaperExecutor(db, FillModel(PaperSettings(), seed=1))
    fill = executor.close(
        CloseRequest(
            position_id=99,
            trade_id=99,
            side=Side.YES,
            size_usd=5.0,
            book=_book(),
            reason=CloseReason.MANUAL,
        )
    )
    assert fill.success is False
    assert fill.error is not None
    assert fill.error.code == "E_FILL_010"
