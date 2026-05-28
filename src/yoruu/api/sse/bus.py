"""Event bus that validates SSE payloads before publish."""

from __future__ import annotations

from typing import Any

from yoruu.api.sse.registry import validate_sse_payload
from yoruu.web.event_bus import MemoryEventBus


class ValidatingEventBus:
    """Wrap MemoryEventBus with ch10 §10.5.3 payload validation."""

    def __init__(self, inner: MemoryEventBus | None = None) -> None:
        self._inner = inner or MemoryEventBus()

    @property
    def inner(self) -> MemoryEventBus:
        return self._inner

    def publish(self, event: str, payload: dict[str, Any]) -> None:
        normalized = validate_sse_payload(event, payload)
        self._inner.publish(event, normalized)

    def subscribe(self):
        return self._inner.subscribe()

    def unsubscribe(self, queue) -> None:
        self._inner.unsubscribe(queue)
