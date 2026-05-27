"""Pre-trade risk checks (ch11 §11.6.6, ch17)."""

from __future__ import annotations

from yoruu.config.settings import RiskSettings
from yoruu.data.database import Database
from yoruu.types import RiskCheckResult, TradeSignal


class RiskGuard:
    """Daily loss and size limits."""

    def __init__(self, config: RiskSettings, db: Database) -> None:
        self._config = config
        self._db = db

    def daily_pnl(self) -> float:
        return self._db.get_daily_pnl()

    def daily_loss_exceeded(self) -> bool:
        return self.daily_pnl() <= -self._config.daily_loss_limit_usd

    def remaining_budget(self) -> float:
        return self._config.daily_loss_limit_usd + self.daily_pnl()

    def check_pre_trade(self, signal: TradeSignal) -> RiskCheckResult:
        if self.daily_loss_exceeded():
            return RiskCheckResult(ok=False, reason="risk_daily_loss")
        if signal.size_usd > self._config.max_trade_size_usd:
            return RiskCheckResult(ok=False, reason="risk_max_trade")
        if signal.size_usd > self.remaining_budget():
            return RiskCheckResult(ok=False, reason="risk_budget")
        balance = self._db.get_balance()
        if signal.size_usd > balance:
            return RiskCheckResult(ok=False, reason="risk_balance")
        return RiskCheckResult(ok=True)
