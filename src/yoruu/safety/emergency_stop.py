"""Emergency stop controller (ch19 §19.4, PHASE 6 M6.5)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from yoruu.core.state_machine import StateMachine
from yoruu.data.database import Database
from yoruu.execution.paper_executor import CloseRequest, PaperExecutor
from yoruu.types import CloseReason, State

if TYPE_CHECKING:
    from yoruu.api.sse.bus import ValidatingEventBus
    from yoruu.core.trading_loop import TradingLoop

logger = logging.getLogger(__name__)

_TRIGGER_MAP = {
    "USER": "dashboard_button",
    "RISK_GUARD": "system_invariant",
    "SYSTEM": "system_invariant",
}


@dataclass(frozen=True)
class EmergencyStopResult:
    """Outcome of ``EmergencyStopController.trigger``."""

    success: bool
    open_closed: int
    state: State
    emergency_stop_id: int | None
    partial: bool = False


class EmergencyStopController:
    """Close open positions, persist stop record, transition to EMERGENCY_STOP."""

    def __init__(
        self,
        db: Database,
        state_machine: StateMachine,
        executor: PaperExecutor,
        *,
        event_bus: ValidatingEventBus | None = None,
        trading_loop: TradingLoop | None = None,
    ) -> None:
        self._db = db
        self._sm = state_machine
        self._executor = executor
        self._bus = event_bus
        self._loop = trading_loop

    def trigger(self, *, source: str, detail: str) -> EmergencyStopResult:
        """Run ch19 §19.4.1 stop sequence."""

        if self._loop is not None:
            self._loop.request_stop()

        state_before = self._sm.current()
        mode_before = self._db.get_mode()
        closed = 0
        partial = False

        for pos in self._db.list_open_positions():
            from yoruu.infra.mock_market import MockMarketProvider

            book = MockMarketProvider().market_state().order_book_yes
            fill = self._executor.close(
                CloseRequest(
                    position_id=pos.position_id,
                    trade_id=pos.trade_id,
                    side=pos.side,
                    size_usd=pos.size_usd,
                    book=book,
                    reason=CloseReason.EMERGENCY_STOP,
                )
            )
            if fill.success:
                closed += 1
            else:
                partial = True
                logger.error(
                    "emergency_close_failed",
                    extra={"trade_id": pos.trade_id, "detail": detail},
                )

        trigger_key = _TRIGGER_MAP.get(source, "api_call")
        stop_id = self._db.insert_emergency_stop(
            trigger=trigger_key,
            state_before=state_before.value,
            mode_before=mode_before.value,
            open_positions_closed=closed,
            daily_pnl_at_stop=self._db.get_daily_pnl(),
        )
        audit_result = "PARTIAL" if partial else "SUCCESS"
        self._db.insert_audit(
            actor="USER" if source == "USER" else "SYSTEM",
            action="EMERGENCY_STOP",
            resource="bot",
            resource_id=str(stop_id),
            details={"source": source, "detail": detail, "closed": closed},
            result=audit_result,
        )

        if state_before != State.EMERGENCY_STOP:
            try:
                self._sm.transition(State.EMERGENCY_STOP, detail, actor=source)
            except Exception as exc:
                logger.error("emergency_state_transition_failed", extra={"error": str(exc)})
                partial = True

        if self._loop is not None:
            self._loop.mark_emergency_stopped()

        if self._bus is not None:
            self._bus.publish(
                "emergency_stop_triggered",
                {
                    "trigger": source,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "open_positions_closed": closed,
                    "severity": "CRITICAL",
                },
            )

        self._db.commit()
        return EmergencyStopResult(
            success=not partial,
            open_closed=closed,
            state=self._sm.current(),
            emergency_stop_id=stop_id,
            partial=partial,
        )
