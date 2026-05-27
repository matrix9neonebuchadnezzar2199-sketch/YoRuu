"""Runtime invariant checks (ch16)."""

from __future__ import annotations

from dataclasses import dataclass

from yoruu.data.database import Database
from yoruu.errors import InvariantViolationError
from yoruu.strategy.models import StrategyConfig
from yoruu.types import State


@dataclass(frozen=True)
class InvariantViolation:
    inv_id: str
    message: str
    severity: str


class InvariantChecker:
    """Check INV-* rules at startup and before trade."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def check_startup(self, strategy: StrategyConfig, strategy_path_version: int) -> None:
        """INV-D-03: DB strategy version matches file."""

        db_version = self._db.get_strategy_version()
        if strategy.version != strategy_path_version:
            raise InvariantViolationError(
                "strategy.json version mismatch with DB",
                code="E_STATE_002",
            )
        if db_version != strategy.version and strategy_path_version != strategy.version:
            raise InvariantViolationError(
                "bot_state strategy version inconsistent",
                code="E_STATE_002",
            )

    def check_pre_trade(self, *, size_usd: float, max_trade_size: float) -> None:
        """INV-R-01."""

        if size_usd > max_trade_size:
            raise InvariantViolationError(
                f"size {size_usd} exceeds max {max_trade_size}",
                code="E_STATE_001",
            )

    def check_state_for_trading(self) -> None:
        """INV-S-02: not in EMERGENCY_STOP."""

        state = self._db.get_state()
        if state == State.EMERGENCY_STOP:
            raise InvariantViolationError("trading while EMERGENCY_STOP", code="E_STATE_001")
