"""SSE event registry and validation."""

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel, ValidationError

from yoruu.api.sse.models import (
    AlertAddedPayload,
    EmergencyStopTriggeredPayload,
    HealthDegradedPayload,
    HealthRecoveredPayload,
    MarkovUpdatePayload,
    ModeChangedPayload,
    NightlyReportReadyPayload,
    PositionClosedPayload,
    PositionOpenedPayload,
    StateChangedPayload,
    StrategyAppliedPayload,
)
from yoruu.errors import YoRuuError

SSE_EVENT_NAMES: tuple[str, ...] = (
    "state_changed",
    "markov_update",
    "health_degraded",
    "health_recovered",
    "position_opened",
    "position_closed",
    "nightly_report_ready",
    "mode_changed",
    "emergency_stop_triggered",
    "alert_added",
    "strategy_applied",
)

_EVENT_MODELS: dict[str, Type[BaseModel]] = {
    "state_changed": StateChangedPayload,
    "markov_update": MarkovUpdatePayload,
    "health_degraded": HealthDegradedPayload,
    "health_recovered": HealthRecoveredPayload,
    "position_opened": PositionOpenedPayload,
    "position_closed": PositionClosedPayload,
    "nightly_report_ready": NightlyReportReadyPayload,
    "mode_changed": ModeChangedPayload,
    "emergency_stop_triggered": EmergencyStopTriggeredPayload,
    "alert_added": AlertAddedPayload,
    "strategy_applied": StrategyAppliedPayload,
}


class SseContractError(YoRuuError):
    """SSE payload failed contract validation."""

    def __init__(self, event: str, detail: str) -> None:
        super().__init__(f"SSE contract violation for {event}: {detail}", code="E_API_001")
        self.event = event


def validate_sse_payload(event: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize payload; returns JSON-serializable dict."""

    model_cls = _EVENT_MODELS.get(event)
    if model_cls is None:
        raise SseContractError(event, "unknown event name")
    try:
        model = model_cls.model_validate(payload)
    except ValidationError as exc:
        raise SseContractError(event, str(exc)) from exc
    return model.model_dump(by_alias=True, mode="json")
