"""Bot state machine (ch3, ch10 §10.7.2)."""

from __future__ import annotations

from dataclasses import dataclass

from yoruu.data.database import Database
from yoruu.errors import StateViolationError
from yoruu.types import State

# Allowed transitions (ch3 §3.2 simplified)
_ALLOWED: dict[State, set[State]] = {
    State.INITIALIZING: {State.IDLE, State.EMERGENCY_STOP, State.SHUTDOWN},
    State.IDLE: {
        State.TRADING,
        State.NIGHTLY_REVIEW,
        State.SHUTDOWN,
        State.EMERGENCY_STOP,
    },
    State.TRADING: {
        State.MONITORING_POSITION,
        State.IDLE,
        State.EMERGENCY_STOP,
        State.ERROR,
    },
    State.MONITORING_POSITION: {State.IDLE, State.EMERGENCY_STOP},
    State.NIGHTLY_REVIEW: {State.IDLE},
    State.EMERGENCY_STOP: {State.INITIALIZING},
    State.ERROR: {State.IDLE, State.EMERGENCY_STOP},
    State.SHUTDOWN: set(),
    State.BACKTEST: set(),
}


@dataclass(frozen=True)
class StateTransition:
    from_state: State
    to_state: State
    reason: str
    transition_id: str


class StateMachine:
    """Persisted singleton state with transition guards."""

    def __init__(self, db: Database) -> None:
        self._db = db
        self._pending_ack: str | None = None

    def current(self) -> State:
        return self._db.get_state()

    def require_state(self, *allowed: State) -> None:
        current = self.current()
        if current not in allowed:
            raise StateViolationError(
                f"State {current.value} not in {[s.value for s in allowed]}",
                code="E_STATE_001",
            )

    def allowed_transitions(self, from_state: State | None = None) -> list[State]:
        src = from_state or self.current()
        return sorted(_ALLOWED.get(src, set()), key=lambda s: s.value)

    def transition(
        self,
        to: State,
        reason: str,
        *,
        actor: str = "system",
    ) -> StateTransition:
        from_state = self.current()
        allowed = _ALLOWED.get(from_state, set())
        if to not in allowed:
            raise StateViolationError(
                f"Transition {from_state.value} -> {to.value} not allowed",
                code="E_STATE_001",
            )
        self._db.set_state(to)
        self._db.insert_audit(
            actor=actor,
            action="STATE_TRANSITION",
            resource="bot",
            resource_id=None,
            details={"from": from_state.value, "to": to.value, "reason": reason},
            result="SUCCESS",
        )
        self._db.commit()
        tid = f"{from_state.value}-{to.value}-{reason}"
        self._pending_ack = tid
        return StateTransition(
            from_state=from_state,
            to_state=to,
            reason=reason,
            transition_id=tid,
        )

    def ack(self, transition_id: str) -> None:
        if self._pending_ack != transition_id:
            raise StateViolationError("Unknown transition ack", code="E_STATE_001")
        self._pending_ack = None
