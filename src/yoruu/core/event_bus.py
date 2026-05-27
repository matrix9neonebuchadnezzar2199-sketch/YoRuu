"""Event bus protocol for SSE publishing (ch10 §10.5)."""

from __future__ import annotations

from typing import Any, Protocol


class EventBus(Protocol):
    """Publish domain events to connected clients."""

    def publish(self, event: str, payload: dict[str, Any]) -> None: ...


class NoOpEventBus:
    """Default bus until FastAPI SSE is wired (PHASE 4)."""

    def publish(self, event: str, payload: dict[str, Any]) -> None:
        del event, payload
