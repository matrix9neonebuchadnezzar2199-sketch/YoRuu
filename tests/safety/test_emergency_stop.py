"""EmergencyStopController (PHASE 6 M6.5)."""

from __future__ import annotations

from pathlib import Path

from helpers import init_db
from yoruu.config.settings import PaperSettings
from yoruu.core.loop_runtime import build_trading_loop
from yoruu.config.settings import load_settings
from yoruu.execution.fill_model import FillModel
from yoruu.execution.paper_executor import OpenRequest, PaperExecutor
from yoruu.safety.invariants import InvariantChecker
from yoruu.types import Mode, Side, State


def _book():
    from yoruu.types import OrderBook

    return OrderBook(
        market="BTC_5MIN_UPDOWN",
        best_bid=0.79,
        best_ask=0.81,
        bid_size_usd=100.0,
        ask_size_usd=100.0,
        spread=0.02,
        captured_at_iso="2026-01-01T00:00:00+00:00",
        source="MOCK",
    )


def test_emergency_stop_closes_and_records(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    checker = InvariantChecker(db, initial_balance=1000.0)
    executor = PaperExecutor(
        db,
        FillModel(PaperSettings(), seed=1),
        invariant_checker=checker,
        max_trade_size_usd=10.0,
    )
    fill = executor.open(
        OpenRequest(
            market="BTC_5MIN_UPDOWN",
            side=Side.YES,
            size_usd=5.0,
            expected_price=0.81,
            book=_book(),
            mode=Mode.PAPER,
            strategy_version=1,
            edge=0.07,
            persistence=0.72,
        )
    )
    assert fill.success
    from yoruu.core.state_machine import StateMachine

    sm = StateMachine(db, invariant_checker=checker)
    if sm.current() == State.INITIALIZING:
        sm.transition(State.IDLE, "test bootstrap")
    sm.transition(State.TRADING, "test")
    sm.transition(State.MONITORING_POSITION, "test")
    from yoruu.safety.emergency_stop import EmergencyStopController

    esc = EmergencyStopController(db, sm, executor)
    result = esc.trigger(source="USER", detail="test")
    assert result.state == State.EMERGENCY_STOP
    assert db.count_open_positions() == 0
    assert db.count_emergency_stops_last_24h_unrecovered() >= 1
