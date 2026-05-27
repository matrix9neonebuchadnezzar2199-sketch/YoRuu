"""State machine tests."""

import pytest

from yoruu.core.state_machine import StateMachine
from yoruu.data.database import Database
from yoruu.errors import StateViolationError
from yoruu.types import Mode, State


def test_idle_to_trading(tmp_path) -> None:
    db = Database(tmp_path / "test.db")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=Mode.PAPER,
        balance=1000.0,
        daily_loss_limit=30.0,
        strategy_version=1,
    )
    sm = StateMachine(db)
    sm.transition(State.IDLE, "init")
    tr = sm.transition(State.TRADING, "5m boundary")
    assert tr.to_state == State.TRADING
    db.close()


def test_invalid_transition(tmp_path) -> None:
    db = Database(tmp_path / "test.db")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=Mode.PAPER,
        balance=1000.0,
        daily_loss_limit=30.0,
        strategy_version=1,
    )
    sm = StateMachine(db)
    sm.transition(State.IDLE, "init")
    with pytest.raises(StateViolationError):
        sm.transition(State.BACKTEST, "invalid from IDLE")
    db.close()
