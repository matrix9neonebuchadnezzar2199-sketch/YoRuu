"""常駐評価ループ: WS feed → Markov → 5分評価 → paper 約定 (PHASE 6 M6.1)."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from yoruu.core.clock import Clock, SystemClock
from yoruu.core.state_machine import StateMachine
from yoruu.data.database import Database, OpenPositionRow
from yoruu.errors import InvariantViolationError, StateViolationError
from yoruu.execution.paper_executor import CloseRequest, OpenRequest, PaperExecutor
from yoruu.execution.risk_guard import RiskGuard
from yoruu.infra.binance_ws import BinanceMarketWs
from yoruu.infra.mock_market import MockMarketProvider
from yoruu.infra.polymarket_ws import PolymarketMarketWs
from yoruu.strategy.evaluator import StrategyEvaluator
from yoruu.strategy.markov import MarkovEngine
from yoruu.types import CloseReason, Mode, OrderBook, PriceTick, State

if TYPE_CHECKING:
    from yoruu.config.settings import AppSettings
    from yoruu.infra.ohlc_provider import OhlcProvider
    from yoruu.safety.emergency_stop import EmergencyStopController
    from yoruu.safety.invariants import InvariantChecker

logger = logging.getLogger(__name__)


@dataclass
class LoopStats:
    """Counters returned when ``TradingLoop.run`` finishes."""

    evaluations: int = 0
    entries: int = 0
    closes: int = 0
    skipped_stale: int = 0


@dataclass
class EvaluationCycleResult:
    """Outcome of a single ``evaluate_cycle`` call."""

    action: str
    detail: str = ""


@dataclass
class _LoopFlags:
    stop_requested: bool = False
    emergency_stopped: bool = False
    consecutive_fill_failures: int = 0


class TradingLoop:
    """単一 asyncio プロセスで Markov 常駐と 5 分境界評価を行う。"""

    def __init__(
        self,
        settings: AppSettings,
        db: Database,
        *,
        markov: MarkovEngine,
        evaluator: StrategyEvaluator,
        executor: PaperExecutor,
        state_machine: StateMachine,
        risk_guard: RiskGuard,
        invariants: InvariantChecker,
        ohlc: OhlcProvider | None = None,
        clock: Clock | None = None,
        emergency: EmergencyStopController | None = None,
        interval_sec: int = 300,
    ) -> None:
        self._settings = settings
        self._db = db
        self._markov = markov
        self._evaluator = evaluator
        self._executor = executor
        self._sm = state_machine
        self._risk = risk_guard
        self._invariants = invariants
        self._ohlc = ohlc
        self._clock = clock or SystemClock()
        self._emergency = emergency
        self._interval_sec = interval_sec
        self._mock = MockMarketProvider(market_id=settings.market.id)
        self._latest_book: OrderBook | None = None
        self._flags = _LoopFlags()
        self._stats = LoopStats()
        self._binance: BinanceMarketWs | None = None
        self._polymarket: PolymarketMarketWs | None = None

    @property
    def stats(self) -> LoopStats:
        return self._stats

    @property
    def emergency_controller(self) -> EmergencyStopController | None:
        return self._emergency

    def request_stop(self) -> None:
        self._flags.stop_requested = True

    def mark_emergency_stopped(self) -> None:
        """Called by EmergencyStopController after trigger."""

        self._flags.emergency_stopped = True

    async def on_tick(self, tick: PriceTick) -> None:
        """Binance tick: Markov 更新 + OHLC マージ。"""

        self._markov.add_close(tick.price)
        if self._ohlc is not None:
            self._ohlc.update_from_tick(tick.price, tick.ts_iso)

    async def on_book(self, book: OrderBook) -> None:
        """Polymarket book: 最新板を保持。"""

        self._latest_book = book

    def _seconds_to_next_boundary(self, now: datetime) -> float:
        """次の 5 分境界（00,05,10,…）までの秒数。"""

        minute_block = (now.minute // 5) * 5
        boundary = now.replace(minute=minute_block, second=0, microsecond=0)
        if now >= boundary:
            boundary = boundary + timedelta(minutes=5)
        return max(0.0, (boundary - now).total_seconds())

    def _is_feed_stale(self) -> bool:
        if self._binance is None:
            return False
        return self._binance.client.is_stale(self._settings.websocket.stale_tick_sec)

    def _market_state(self):
        if self._latest_book is not None:
            yes = self._latest_book
            no_bid = max(1.0 - yes.best_ask, 0.01)
            no_ask = 1.0 - yes.best_bid
            from yoruu.types import MarketState

            no_book = OrderBook(
                market=yes.market,
                best_bid=no_bid,
                best_ask=no_ask,
                bid_size_usd=yes.bid_size_usd,
                ask_size_usd=yes.ask_size_usd,
                spread=no_ask - no_bid,
                captured_at_iso=yes.captured_at_iso,
                source=yes.source,
            )
            return MarketState(order_book_yes=yes, order_book_no=no_book)
        return self._mock.market_state()

    async def evaluate_cycle(self) -> EvaluationCycleResult:
        """1 評価サイクル（状態遷移 + 約定含む）。"""

        if self._flags.emergency_stopped:
            return EvaluationCycleResult(action="halted", detail="emergency_stop")

        if self._emergency is not None and self._risk.daily_loss_exceeded():
            self._emergency.trigger(source="RISK_GUARD", detail="AUTO_LOSS_LIMIT")
            self._flags.emergency_stopped = True
            return EvaluationCycleResult(action="emergency", detail="AUTO_LOSS_LIMIT")

        current = self._sm.current()
        if current == State.EMERGENCY_STOP:
            self._flags.emergency_stopped = True
            return EvaluationCycleResult(action="halted", detail="state_emergency")

        if current == State.MONITORING_POSITION:
            closed = self._try_expire_open_positions()
            if closed:
                self._stats.closes += closed
                return EvaluationCycleResult(action="close", detail="expiration")
            return EvaluationCycleResult(action="hold", detail="monitoring")

        if current not in (State.IDLE, State.TRADING):
            return EvaluationCycleResult(action="skip", detail=f"state={current.value}")

        if self._binance is not None and self._is_feed_stale():
            self._stats.skipped_stale += 1
            return EvaluationCycleResult(action="skip", detail="ws_stale")

        self._stats.evaluations += 1
        snap = self._markov.snapshot()
        self._db.insert_markov_snapshot(
            computed_at=snap.computed_at_iso,
            window_size=snap.window_size,
            matrix={
                "p_up_up": snap.matrix.p_up_up,
                "p_up_down": snap.matrix.p_up_down,
                "p_down_up": snap.matrix.p_down_up,
                "p_down_down": snap.matrix.p_down_down,
            },
            persistence=snap.rolling_persistence,
            last_direction=snap.last_direction.value if snap.last_direction else None,
        )

        try:
            result = self._evaluator.evaluate(
                self._market_state(),
                balance=self._db.get_balance(),
                max_trade_size_usd=self._settings.risk.max_trade_size_usd,
                snapshot=snap,
                risk_guard=self._risk,
            )
        except InvariantViolationError as exc:
            logger.error("invariant_violation", extra={"detail": str(exc)})
            if self._emergency is not None:
                self._emergency.trigger(source="SYSTEM", detail="AUTO_INVARIANT")
            self._flags.emergency_stopped = True
            return EvaluationCycleResult(action="emergency", detail="AUTO_INVARIANT")

        if not result.should_enter or result.side is None:
            return EvaluationCycleResult(action="wait", detail=result.reason or "no_entry")

        if self._db.count_open_positions() > 0:
            return EvaluationCycleResult(action="skip", detail="position_open")

        strategy_version = self._evaluator.strategy.version
        try:
            self._sm.transition(State.TRADING, "loop entry")
            fill = self._executor.open(
                OpenRequest(
                    market=self._settings.market.id,
                    side=result.side,
                    size_usd=result.size_usd,
                    expected_price=result.market_price,
                    book=self._market_state().order_book_yes,
                    mode=self._settings.mode,
                    strategy_version=strategy_version,
                    edge=result.edge,
                    persistence=result.persistence,
                )
            )
            if not fill.success:
                self._record_fill_failure()
                self._sm.transition(State.IDLE, "fill failed")
                return EvaluationCycleResult(action="fill_fail", detail=fill.error.code if fill.error else "")
            self._flags.consecutive_fill_failures = 0
            self._sm.transition(State.MONITORING_POSITION, "order placed")
            self._stats.entries += 1
            return EvaluationCycleResult(action="enter", detail=f"trade_id={fill.trade_id}")
        except StateViolationError as exc:
            logger.warning("state_transition_failed", extra={"detail": str(exc)})
            return EvaluationCycleResult(action="skip", detail=str(exc))

    def _record_fill_failure(self) -> None:
        self._flags.consecutive_fill_failures += 1
        limit = self._settings.risk.consecutive_fail_limit
        if (
            self._emergency is not None
            and self._flags.consecutive_fill_failures >= limit
        ):
            self._emergency.trigger(source="SYSTEM", detail="AUTO_CONSECUTIVE_FAIL")
            self._flags.emergency_stopped = True

    def _try_expire_open_positions(self) -> int:
        now = self._clock.now()
        closed = 0
        for pos in self._db.list_open_positions():
            expires = datetime.fromisoformat(pos.expires_at.replace("Z", "+00:00"))
            if now < expires:
                continue
            book = self._market_state().order_book_yes
            fill = self._executor.close(
                CloseRequest(
                    position_id=pos.position_id,
                    trade_id=pos.trade_id,
                    side=pos.side,
                    size_usd=pos.size_usd,
                    book=book,
                    reason=CloseReason.EXPIRATION,
                )
            )
            if fill.success:
                closed += 1
                try:
                    self._sm.transition(State.IDLE, "position expired")
                except StateViolationError:
                    pass
        return closed

    async def run(
        self,
        *,
        max_evaluations: int | None = None,
        deadline_sec: float | None = None,
        lab_mock_feed: bool = False,
        connect_ws: bool = True,
    ) -> LoopStats:
        """feed 接続 → 評価ループ → 正常停止。"""

        started = self._clock.now()
        feed_task: asyncio.Task[None] | None = None

        if connect_ws and not lab_mock_feed:
            self._binance = BinanceMarketWs(
                self._settings.websocket,
                symbol=self._settings.market.binance_symbol,
                db=self._db,
                on_tick=self.on_tick,
            )
            self._polymarket = PolymarketMarketWs(
                self._settings.websocket,
                market_id=self._settings.market.id,
                db=self._db,
                on_book=self.on_book,
            )
            await self._binance.connect()
            await self._polymarket.connect()
        elif lab_mock_feed:
            feed_task = asyncio.create_task(self._lab_feed_task())

        try:
            while not self._flags.stop_requested and not self._flags.emergency_stopped:
                if deadline_sec is not None:
                    elapsed = (self._clock.now() - started).total_seconds()
                    if elapsed >= deadline_sec:
                        break

                wait_sec = self._seconds_to_next_boundary(self._clock.now())
                if lab_mock_feed and self._interval_sec < 300:
                    wait_sec = float(self._interval_sec)
                await self._clock.sleep(wait_sec)
                await self.evaluate_cycle()

                if max_evaluations is not None and self._stats.evaluations >= max_evaluations:
                    break
        finally:
            if feed_task is not None:
                feed_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await feed_task
            if self._binance is not None:
                await self._binance.disconnect()
            if self._polymarket is not None:
                await self._polymarket.disconnect()
            self._db.commit()

        return self._stats

    async def _lab_feed_task(self) -> None:
        """テスト/ラボ用: 単調増加ティックを供給。"""

        price = 100.0
        while not self._flags.stop_requested:
            tick = self._mock.next_tick(delta=price - 100.0)
            price += 1.0
            await self.on_tick(tick)
            await self._clock.sleep(min(1.0, float(self._interval_sec)))
