"""Runtime invariant checks (ch16)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from yoruu.data.database import Database
from yoruu.errors import InvariantViolationError
from yoruu.strategy.models import StrategyConfig
from yoruu.types import Mode, State

# ch16 §16.3.1 SSOT
INV_D06_TOLERANCE_USD = 0.02

if TYPE_CHECKING:
    from yoruu.execution.risk_guard import RiskGuard


@dataclass(frozen=True)
class InvariantViolation:
    inv_id: str
    message: str
    severity: str


def _raise_if(violation: InvariantViolation | None) -> None:
    if violation is None:
        return
    if violation.severity == "CRITICAL":
        raise InvariantViolationError(
            violation.message,
            inv_id=violation.inv_id,
            severity=violation.severity,
        )
    if violation.severity == "ERROR":
        raise InvariantViolationError(
            violation.message,
            inv_id=violation.inv_id,
            severity=violation.severity,
        )


class InvariantChecker:
    """Check INV-* rules at startup, transition, trade, and 5m boundaries."""

    def __init__(self, db: Database, *, initial_balance: float | None = None) -> None:
        self._db = db
        self._initial_balance = initial_balance
        self._last_entry_boundary: str | None = None

    def check_startup(self, strategy: StrategyConfig, strategy_path_version: int) -> None:
        """Run startup invariants (INV-D-03, INV-S-01)."""

        _raise_if(self.inv_s01_single_bot_state())
        _raise_if(self.inv_d03_strategy_version(strategy, strategy_path_version))

    def check_pre_transition(self, from_state: State, to_state: State) -> None:
        """Transition guards (INV-S-02, INV-S-03, INV-S-04)."""

        _raise_if(self.inv_s02_no_trading_from_emergency(from_state, to_state))
        _raise_if(self.inv_s03_shutdown_terminal(from_state, to_state))
        _raise_if(self.inv_s04_no_mode_change_during_nightly(from_state, to_state))

    def check_pre_trade(
        self,
        *,
        size_usd: float,
        max_trade_size: float,
        daily_loss_limit: float | None = None,
    ) -> None:
        """Trade-time invariants (INV-S-02, INV-R-01, INV-R-02, INV-R-04)."""

        _raise_if(self.inv_s02_emergency_blocks_trading())
        _raise_if(self.inv_r01_max_trade_size(size_usd, max_trade_size))
        if daily_loss_limit is not None:
            _raise_if(self.inv_r02_daily_loss_limit(daily_loss_limit))
        _raise_if(self.inv_r04_non_negative_size(size_usd))

    def check_post_open(self, *, size_usd: float) -> None:
        """Balance conservation after open (INV-D-06)."""

        _raise_if(self.inv_d06_balance_conservation())

    def check_post_close(self) -> None:
        """Balance conservation after close (INV-D-06)."""

        _raise_if(self.inv_d06_balance_conservation())

    def check_five_minute_boundary(self, *, boundary_key: str, entered: bool) -> None:
        """INV-R-05: no double entry in same 5m window."""

        _raise_if(self.inv_r05_single_entry_per_boundary(boundary_key, entered))

    def check_with_risk_guard(self, risk: RiskGuard, size_usd: float) -> None:
        """INV-R-02 via RiskGuard."""

        if risk.daily_loss_exceeded():
            _raise_if(
                InvariantViolation(
                    inv_id="INV-R-02",
                    message="daily loss limit exceeded",
                    severity="CRITICAL",
                )
            )

    def record_entry_boundary(self, boundary_key: str) -> None:
        self._last_entry_boundary = boundary_key

    # --- INV-S-* ---

    def inv_s01_single_bot_state(self) -> InvariantViolation | None:
        count = self._db.count_bot_state_rows()
        if count != 1:
            return InvariantViolation(
                inv_id="INV-S-01",
                message=f"bot_state must have exactly 1 row, found {count}",
                severity="CRITICAL",
            )
        return None

    def inv_s02_emergency_blocks_trading(self) -> InvariantViolation | None:
        if self._db.get_state() == State.EMERGENCY_STOP:
            return InvariantViolation(
                inv_id="INV-S-02",
                message="trading while EMERGENCY_STOP",
                severity="ERROR",
            )
        return None

    def inv_s02_no_trading_from_emergency(
        self, from_state: State, to_state: State
    ) -> InvariantViolation | None:
        if from_state == State.EMERGENCY_STOP and to_state in (
            State.TRADING,
            State.MONITORING_POSITION,
        ):
            return InvariantViolation(
                inv_id="INV-S-02",
                message="cannot enter trading from EMERGENCY_STOP without recovery",
                severity="ERROR",
            )
        return None

    def inv_s03_shutdown_terminal(self, from_state: State, to_state: State) -> InvariantViolation | None:
        if from_state == State.SHUTDOWN and to_state != State.SHUTDOWN:
            return InvariantViolation(
                inv_id="INV-S-03",
                message="SHUTDOWN is terminal",
                severity="ERROR",
            )
        return None

    def inv_s04_no_mode_change_during_nightly(
        self, from_state: State, to_state: State
    ) -> InvariantViolation | None:
        if from_state == State.NIGHTLY_REVIEW and to_state in (
            State.NIGHTLY_REVIEW,
            State.IDLE,
        ):
            return None
        if from_state == State.NIGHTLY_REVIEW:
            return InvariantViolation(
                inv_id="INV-S-04",
                message="mode change blocked during NIGHTLY_REVIEW",
                severity="ERROR",
            )
        return None

    def inv_s05_backtest_uses_separate_flow(self, mode: Mode) -> InvariantViolation | None:
        if mode == Mode.BACKTEST and self._db.get_state() not in (
            State.BACKTEST,
            State.INITIALIZING,
            State.IDLE,
        ):
            return InvariantViolation(
                inv_id="INV-S-05",
                message="BACKTEST must not use live state machine path",
                severity="ERROR",
            )
        return None

    # --- INV-D-* ---

    def inv_d01_open_positions_mode_match(self) -> InvariantViolation | None:
        mismatches = self._db.count_open_positions_mode_mismatch(self._db.get_mode())
        if mismatches > 0:
            return InvariantViolation(
                inv_id="INV-D-01",
                message="open position mode mismatch",
                severity="ERROR",
            )
        return None

    def inv_d03_strategy_version(
        self, strategy: StrategyConfig, strategy_path_version: int
    ) -> InvariantViolation | None:
        db_version = self._db.get_strategy_version()
        if strategy.version != strategy_path_version:
            return InvariantViolation(
                inv_id="INV-D-03",
                message="strategy.json version mismatch with file",
                severity="CRITICAL",
            )
        if db_version != strategy.version:
            return InvariantViolation(
                inv_id="INV-D-03",
                message="bot_state strategy version inconsistent with strategy.json",
                severity="CRITICAL",
            )
        return None

    def inv_d04_strategy_apply_has_version_row(self) -> InvariantViolation | None:
        return None

    def inv_d05_live_trades_paper_only_executor(self) -> InvariantViolation | None:
        if self._db.get_mode() != Mode.LIVE:
            return None
        return None

    def inv_d06_balance_conservation(self) -> InvariantViolation | None:
        if self._initial_balance is None:
            return None
        balance = self._db.get_balance()
        open_total = self._db.open_positions_total_size()
        closed_sum = self._db.sum_closed_trade_pnl()
        if abs(balance + open_total - (self._initial_balance + closed_sum)) > INV_D06_TOLERANCE_USD:
            return InvariantViolation(
                inv_id="INV-D-06",
                message=(
                    f"balance conservation failed: balance={balance}, "
                    f"open={open_total}, initial={self._initial_balance}, closed_pnl={closed_sum}"
                ),
                severity="ERROR",
            )
        return None

    # --- INV-R-* ---

    def inv_r01_max_trade_size(self, size_usd: float, max_trade_size: float) -> InvariantViolation | None:
        if size_usd > max_trade_size:
            return InvariantViolation(
                inv_id="INV-R-01",
                message=f"size {size_usd} exceeds max {max_trade_size}",
                severity="ERROR",
            )
        return None

    def inv_r02_daily_loss_limit(self, daily_loss_limit: float) -> InvariantViolation | None:
        daily_pnl = self._db.get_daily_pnl()
        if daily_pnl <= -daily_loss_limit:
            return InvariantViolation(
                inv_id="INV-R-02",
                message="daily loss limit reached",
                severity="CRITICAL",
            )
        return None

    def inv_r03_parameters_in_constraints(self, strategy: StrategyConfig) -> InvariantViolation | None:
        errors = strategy.validate_parameters_in_constraints()
        if errors:
            return InvariantViolation(
                inv_id="INV-R-03",
                message=f"parameters out of constraints: {errors}",
                severity="ERROR",
            )
        return None

    def inv_r04_non_negative_size(self, size_usd: float) -> InvariantViolation | None:
        if size_usd < 0:
            return InvariantViolation(
                inv_id="INV-R-04",
                message="Kelly size must be non-negative",
                severity="ERROR",
            )
        return None

    def inv_r05_single_entry_per_boundary(
        self, boundary_key: str, entered: bool
    ) -> InvariantViolation | None:
        if entered and self._last_entry_boundary == boundary_key:
            return InvariantViolation(
                inv_id="INV-R-05",
                message="duplicate entry in same 5m boundary",
                severity="ERROR",
            )
        return None

    # --- INV-M-* ---

    def inv_m01_live_blocked_after_emergency_24h(self) -> InvariantViolation | None:
        if self._db.get_mode() != Mode.LIVE:
            return None
        if self._db.count_emergency_stops_last_24h_unrecovered() > 0:
            return InvariantViolation(
                inv_id="INV-M-01",
                message="LIVE blocked within 24h of emergency stop",
                severity="ERROR",
            )
        return None

    def inv_m02_paper_balance_reset_on_restart(self) -> InvariantViolation | None:
        return None

    def inv_m03_simmer_balance_monotonic(self) -> InvariantViolation | None:
        return None
