"""Per-invariant unit tests (ch16 §16.2–16.5, 19 INV-*)."""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import init_db
from yoruu.data.database import Database
from yoruu.errors import InvariantViolationError
from yoruu.safety.invariants import INV_D06_TOLERANCE_USD, InvariantChecker, InvariantViolation
from yoruu.strategy.models import StrategyParameters
from yoruu.types import Mode, Side, State


def _checker(db: Database, *, initial: float = 1000.0) -> InvariantChecker:
    return InvariantChecker(db, initial_balance=initial)


# --- INV-S (5) ---


def test_inv_s01_ok_single_row(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert _checker(db).inv_s01_single_bot_state() is None


def test_inv_s01_violation_no_row(tmp_path: Path) -> None:
    db = Database(tmp_path / "empty.sqlite")
    db.initialize_schema()
    v = _checker(db).inv_s01_single_bot_state()
    assert v is not None
    assert v.inv_id == "INV-S-01"
    assert v.severity == "CRITICAL"


def test_inv_s02_emergency_blocks_trading(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    db.set_state(State.EMERGENCY_STOP)
    v = _checker(db).inv_s02_emergency_blocks_trading()
    assert v is not None
    assert v.severity == "ERROR"


def test_inv_s02_no_trading_from_emergency(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    v = _checker(db).inv_s02_no_trading_from_emergency(
        State.EMERGENCY_STOP,
        State.TRADING,
    )
    assert v is not None
    assert v.inv_id == "INV-S-02"


def test_inv_s02_transition_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert (
        _checker(db).inv_s02_no_trading_from_emergency(State.IDLE, State.TRADING) is None
    )


def test_inv_s03_shutdown_terminal(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    v = _checker(db).inv_s03_shutdown_terminal(State.SHUTDOWN, State.IDLE)
    assert v is not None
    assert v.inv_id == "INV-S-03"


def test_inv_s03_shutdown_stays(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert _checker(db).inv_s03_shutdown_terminal(State.SHUTDOWN, State.SHUTDOWN) is None


def test_inv_s04_ok_when_not_nightly(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert (
        _checker(db).inv_s04_no_mode_change_during_nightly(State.IDLE, State.TRADING) is None
    )


def test_inv_s04_nightly_may_return_to_idle(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert (
        _checker(db).inv_s04_no_mode_change_during_nightly(
            State.NIGHTLY_REVIEW, State.IDLE
        )
        is None
    )


def test_inv_s04_nightly_blocks_trading_transition(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    v = _checker(db).inv_s04_no_mode_change_during_nightly(
        State.NIGHTLY_REVIEW,
        State.TRADING,
    )
    assert v is not None
    assert v.inv_id == "INV-S-04"


def test_inv_s05_backtest_wrong_state(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    db.set_state(State.TRADING)
    v = _checker(db).inv_s05_backtest_uses_separate_flow(Mode.BACKTEST)
    assert v is not None
    assert v.inv_id == "INV-S-05"


def test_inv_s05_backtest_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    db.set_state(State.BACKTEST)
    assert _checker(db).inv_s05_backtest_uses_separate_flow(Mode.BACKTEST) is None


# --- INV-D (6) ---


def test_inv_d01_mode_match_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path, mode=Mode.PAPER)
    assert _checker(db).inv_d01_open_positions_mode_match() is None


def test_inv_d01_mode_mismatch(tmp_path: Path) -> None:
    db = init_db(tmp_path, mode=Mode.PAPER)
    db.insert_trade_open(
        market="BTC_5MIN_UPDOWN",
        side=Side.YES.value,
        size_usd=5.0,
        entry_price=0.62,
        mode=Mode.LIVE,
        strategy_version=1,
        edge=0.07,
        persistence=0.72,
        opened_at="2026-05-27T14:32:00+00:00",
        expires_at="2026-05-27T14:37:00+00:00",
    )
    db.commit()
    v = _checker(db).inv_d01_open_positions_mode_match()
    assert v is not None
    assert v.inv_id == "INV-D-01"


def test_inv_d01_no_open_positions_boundary(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert db.count_open_positions() == 0
    assert _checker(db).inv_d01_open_positions_mode_match() is None


def test_inv_d03_file_version_mismatch(tmp_path: Path, strategy_config) -> None:
    db = init_db(tmp_path, strategy_version=1)
    v = _checker(db).inv_d03_strategy_version(strategy_config, strategy_path_version=2)
    assert v is not None
    assert "file" in v.message


def test_inv_d03_version_mismatch_file(tmp_path: Path, strategy_config) -> None:
    db = init_db(tmp_path, strategy_version=1)
    strategy = strategy_config.model_copy(update={"version": 2})
    v = _checker(db).inv_d03_strategy_version(strategy, 2)
    assert v is not None
    assert v.severity == "CRITICAL"


def test_inv_d03_version_ok(tmp_path: Path, strategy_config) -> None:
    db = init_db(tmp_path, strategy_version=1)
    assert _checker(db).inv_d03_strategy_version(strategy_config, 1) is None


def test_inv_d04_stub_returns_none(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert _checker(db).inv_d04_strategy_apply_has_version_row() is None


def test_inv_d05_stub_returns_none(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert _checker(db).inv_d05_live_trades_paper_only_executor() is None


def test_inv_d06_conservation_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path, balance=990.0)
    trade_id = db.insert_trade_open(
        market="BTC_5MIN_UPDOWN",
        side=Side.YES.value,
        size_usd=10.0,
        entry_price=0.62,
        mode=Mode.PAPER,
        strategy_version=1,
        edge=0.07,
        persistence=0.72,
        opened_at="2026-05-27T14:32:00+00:00",
        expires_at="2026-05-27T14:37:00+00:00",
    )
    db.commit()
    assert _checker(db, initial=1000.0).inv_d06_balance_conservation() is None
    assert trade_id >= 1


def test_inv_d06_violation_exceeds_tolerance(tmp_path: Path) -> None:
    db = init_db(tmp_path, balance=989.96)
    db.insert_trade_open(
        market="BTC_5MIN_UPDOWN",
        side=Side.YES.value,
        size_usd=10.0,
        entry_price=0.62,
        mode=Mode.PAPER,
        strategy_version=1,
        edge=0.07,
        persistence=0.72,
        opened_at="2026-05-27T14:32:00+00:00",
        expires_at="2026-05-27T14:37:00+00:00",
    )
    db.commit()
    v = _checker(db, initial=1000.0).inv_d06_balance_conservation()
    assert v is not None
    assert v.inv_id == "INV-D-06"
    assert v.severity == "ERROR"


def test_inv_d06_boundary_exactly_tolerance(tmp_path: Path) -> None:
    """abs(diff) == 0.02 must not violate (strict >)."""

    initial = 1000.0
    balance = 1000.0 - 10.0 - INV_D06_TOLERANCE_USD
    db = init_db(tmp_path, balance=balance)
    db.insert_trade_open(
        market="BTC_5MIN_UPDOWN",
        side=Side.YES.value,
        size_usd=10.0,
        entry_price=0.62,
        mode=Mode.PAPER,
        strategy_version=1,
        edge=0.07,
        persistence=0.72,
        opened_at="2026-05-27T14:32:00+00:00",
        expires_at="2026-05-27T14:37:00+00:00",
    )
    db.commit()
    assert _checker(db, initial=initial).inv_d06_balance_conservation() is None


def test_inv_d06_skipped_without_initial_balance(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert InvariantChecker(db, initial_balance=None).inv_d06_balance_conservation() is None


def test_check_pre_transition_bundle(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    checker = _checker(db)
    with pytest.raises(InvariantViolationError):
        checker.check_pre_transition(State.EMERGENCY_STOP, State.TRADING)


def test_check_pre_trade_daily_loss(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    db.update_balance_and_pnl(900.0, -35.0)
    checker = _checker(db, initial=1000.0)
    with pytest.raises(InvariantViolationError) as exc_info:
        checker.check_pre_trade(size_usd=5.0, max_trade_size=10.0, daily_loss_limit=30.0)
    assert exc_info.value.inv_id == "INV-R-02"


def test_check_post_close_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path, balance=990.0)
    db.insert_trade_open(
        market="BTC_5MIN_UPDOWN",
        side=Side.YES.value,
        size_usd=10.0,
        entry_price=0.62,
        mode=Mode.PAPER,
        strategy_version=1,
        edge=0.07,
        persistence=0.72,
        opened_at="2026-05-27T14:32:00+00:00",
        expires_at="2026-05-27T14:37:00+00:00",
    )
    db.commit()
    _checker(db, initial=1000.0).check_post_close()


def test_check_five_minute_boundary_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    _checker(db).check_five_minute_boundary(boundary_key="k1", entered=False)


def test_inv_d06_raises_via_check_post_open(tmp_path: Path) -> None:
    db = init_db(tmp_path, balance=500.0)
    checker = _checker(db, initial=1000.0)
    with pytest.raises(InvariantViolationError) as exc_info:
        checker.check_post_open(size_usd=10.0)
    assert exc_info.value.inv_id == "INV-D-06"


# --- INV-R (5) ---


def test_inv_r01_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert _checker(db).inv_r01_max_trade_size(5.0, 10.0) is None


def test_inv_r01_violation(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    v = _checker(db).inv_r01_max_trade_size(15.0, 10.0)
    assert v is not None
    assert v.severity == "ERROR"


def test_inv_r02_daily_loss(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    db.update_balance_and_pnl(900.0, -35.0)
    v = _checker(db).inv_r02_daily_loss_limit(30.0)
    assert v is not None
    assert v.severity == "CRITICAL"


def test_inv_r02_within_limit(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    db.update_balance_and_pnl(980.0, -10.0)
    assert _checker(db).inv_r02_daily_loss_limit(30.0) is None


def test_inv_r03_constraints_ok(tmp_path: Path, strategy_config) -> None:
    db = init_db(tmp_path)
    assert _checker(db).inv_r03_parameters_in_constraints(strategy_config) is None


def test_inv_r03_constraints_violation(tmp_path: Path, strategy_config) -> None:
    db = init_db(tmp_path)
    bad = strategy_config.model_copy(
        update={
            "parameters": StrategyParameters(
                MIN_PROB=0.50,
                MIN_EDGE=0.06,
                KELLY_FRACTION=0.65,
                PERSISTENCE_THRESHOLD=0.70,
            )
        }
    )
    v = _checker(db).inv_r03_parameters_in_constraints(bad)
    assert v is not None
    assert v.inv_id == "INV-R-03"


def test_inv_r04_negative_size(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    v = _checker(db).inv_r04_non_negative_size(-1.0)
    assert v is not None


def test_inv_r04_zero_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert _checker(db).inv_r04_non_negative_size(0.0) is None


def test_inv_r05_duplicate_boundary(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    checker = _checker(db)
    checker.record_entry_boundary("2026-05-27T14:35:00")
    v = checker.inv_r05_single_entry_per_boundary("2026-05-27T14:35:00", entered=True)
    assert v is not None
    assert v.inv_id == "INV-R-05"


def test_inv_r05_first_entry_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    assert _checker(db).inv_r05_single_entry_per_boundary("2026-05-27T14:35:00", entered=False) is None


def test_check_with_risk_guard_daily_loss(tmp_path: Path) -> None:
    from yoruu.config.settings import RiskSettings
    from yoruu.execution.risk_guard import RiskGuard

    db = init_db(tmp_path)
    db.update_balance_and_pnl(900.0, -35.0)
    risk = RiskGuard(RiskSettings(max_trade_size_usd=10.0, daily_loss_limit_usd=30.0), db)
    with pytest.raises(InvariantViolationError) as exc_info:
        _checker(db).check_with_risk_guard(risk, size_usd=5.0)
    assert exc_info.value.inv_id == "INV-R-02"


# --- INV-M (3) ---


def test_inv_m01_live_blocked_after_emergency(tmp_path: Path) -> None:
    db = init_db(tmp_path, mode=Mode.LIVE)
    db._conn.execute(
        """
        INSERT INTO emergency_stops (
          triggered_at, trigger, state_before, mode_before,
          open_positions_closed, recovered_at
        ) VALUES (
          datetime('now', '-1 hour'), 'dashboard_button', 'TRADING', 'LIVE', 0, NULL
        )
        """
    )
    db.commit()
    v = _checker(db).inv_m01_live_blocked_after_emergency_24h()
    assert v is not None
    assert v.inv_id == "INV-M-01"


def test_inv_m01_paper_mode_skips(tmp_path: Path) -> None:
    db = init_db(tmp_path, mode=Mode.PAPER)
    assert _checker(db).inv_m01_live_blocked_after_emergency_24h() is None


def test_inv_m02_m03_stubs(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    checker = _checker(db)
    assert checker.inv_m02_paper_balance_reset_on_restart() is None
    assert checker.inv_m03_simmer_balance_monotonic() is None


def test_raise_if_critical_only_errors_on_critical() -> None:
    from yoruu.safety.invariants import _raise_if

    with pytest.raises(InvariantViolationError):
        _raise_if(
            InvariantViolation(inv_id="INV-S-01", message="x", severity="CRITICAL")
        )
    with pytest.raises(InvariantViolationError):
        _raise_if(InvariantViolation(inv_id="INV-R-01", message="x", severity="ERROR"))
    _raise_if(InvariantViolation(inv_id="X", message="warn", severity="WARN"))
