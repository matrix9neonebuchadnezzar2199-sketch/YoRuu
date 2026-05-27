"""Paper trading executor (ch13)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from typing import TYPE_CHECKING

from yoruu.data.database import Database
from yoruu.execution.fill_model import FillComputation, FillModel
from yoruu.types import CloseReason, ErrorPayload, Mode, OrderBook, Side

if TYPE_CHECKING:
    from yoruu.safety.invariants import InvariantChecker


@dataclass(frozen=True)
class OpenRequest:
    market: str
    side: Side
    size_usd: float
    expected_price: float
    book: OrderBook
    mode: Mode
    strategy_version: int
    edge: float
    persistence: float


@dataclass(frozen=True)
class CloseRequest:
    position_id: int
    trade_id: int
    side: Side
    size_usd: float
    book: OrderBook
    reason: CloseReason


@dataclass(frozen=True)
class FillResult:
    success: bool
    trade_id: int | None
    fill_price: float | None
    slippage_applied: float | None
    spread_at_fill: float | None
    latency_ms_used: int | None
    error: ErrorPayload | None
    raw_computation: FillComputation | None


class PaperExecutor:
    """Virtual fills with FillModel (ch13 §13.3)."""

    def __init__(
        self,
        db: Database,
        fill_model: FillModel,
        *,
        invariant_checker: InvariantChecker | None = None,
        max_trade_size_usd: float | None = None,
        daily_loss_limit: float | None = None,
    ) -> None:
        self._db = db
        self._fill_model = fill_model
        self._invariants = invariant_checker
        self._max_trade_size = max_trade_size_usd
        self._daily_loss_limit = daily_loss_limit

    def open(self, request: OpenRequest) -> FillResult:
        if self._invariants is not None and self._max_trade_size is not None:
            self._invariants.check_pre_trade(
                size_usd=request.size_usd,
                max_trade_size=self._max_trade_size,
                daily_loss_limit=self._daily_loss_limit,
            )
        try:
            comp = self._fill_model.compute_open_fill(
                book=request.book,
                size_usd=request.size_usd,
            )
        except ValueError as exc:
            code = self._map_error(str(exc))
            return FillResult(
                success=False,
                trade_id=None,
                fill_price=None,
                slippage_applied=None,
                spread_at_fill=request.book.spread,
                latency_ms_used=None,
                error=ErrorPayload(
                    code=code,
                    message=str(exc),
                    severity="WARN",
                    details={},
                ),
                raw_computation=None,
            )

        now = datetime.now(UTC)
        expires = now + timedelta(minutes=5)
        trade_id = self._db.insert_trade_open(
            market=request.market,
            side=request.side.value,
            size_usd=request.size_usd,
            entry_price=comp.fill_price,
            mode=request.mode,
            strategy_version=request.strategy_version,
            edge=request.edge,
            persistence=request.persistence,
            opened_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )
        balance = self._db.get_balance() - request.size_usd
        self._db.update_balance(balance)
        if self._invariants is not None:
            self._invariants.check_post_open(size_usd=request.size_usd)
        self._db.commit()
        return FillResult(
            success=True,
            trade_id=trade_id,
            fill_price=comp.fill_price,
            slippage_applied=comp.slippage,
            spread_at_fill=comp.spread,
            latency_ms_used=comp.latency_ms,
            error=None,
            raw_computation=comp,
        )

    def close(self, request: CloseRequest) -> FillResult:
        try:
            comp = self._fill_model.compute_close_fill(
                book=request.book,
                size_usd=request.size_usd,
                side=request.side,
                reason=request.reason,
            )
        except ValueError as exc:
            return FillResult(
                success=False,
                trade_id=request.trade_id,
                fill_price=None,
                slippage_applied=None,
                spread_at_fill=request.book.spread,
                latency_ms_used=None,
                error=ErrorPayload(
                    code="E_FILL_003",
                    message=str(exc),
                    severity="WARN",
                    details={},
                ),
                raw_computation=None,
            )

        entry_row = self._db.fetch_trade(request.trade_id)
        if entry_row is None:
            return FillResult(
                success=False,
                trade_id=None,
                fill_price=None,
                slippage_applied=None,
                spread_at_fill=None,
                latency_ms_used=None,
                error=ErrorPayload(
                    code="E_FILL_010",
                    message="position not found",
                    severity="ERROR",
                    details={},
                ),
                raw_computation=None,
            )

        entry_price = float(entry_row["entry_price"])
        size_usd = float(entry_row["size_usd"])
        shares = size_usd / entry_price if entry_price > 0 else 0.0
        pnl = (comp.fill_price - entry_price) * shares
        now = datetime.now(UTC).isoformat()
        self._db.close_trade(
            request.trade_id,
            exit_price=comp.fill_price,
            pnl=pnl,
            closed_at=now,
        )
        balance = self._db.get_balance() + size_usd + pnl
        daily_pnl = self._db.get_daily_pnl() + pnl
        self._db.update_balance_and_pnl(balance, daily_pnl)
        if self._invariants is not None:
            self._invariants.check_post_close()
        self._db.commit()
        return FillResult(
            success=True,
            trade_id=request.trade_id,
            fill_price=comp.fill_price,
            slippage_applied=comp.slippage,
            spread_at_fill=comp.spread,
            latency_ms_used=comp.latency_ms,
            error=None,
            raw_computation=comp,
        )

    @staticmethod
    def _map_error(msg: str) -> str:
        if "liquidity" in msg:
            return "E_FILL_001"
        if "spread" in msg:
            return "E_FILL_002"
        if "cap" in msg or "0.99" in msg:
            return "E_FILL_003"
        return "E_FILL_005"
