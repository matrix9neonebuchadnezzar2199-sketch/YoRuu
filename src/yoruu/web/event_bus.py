"""In-memory event bus for SSE (ch10 §10.5)."""

from __future__ import annotations

import asyncio
from collections import deque
from typing import Any


class MemoryEventBus:
    """Store recent events for SSE subscribers."""

    def __init__(self, *, maxlen: int = 256) -> None:
        self._events: deque[tuple[str, dict[str, Any]]] = deque(maxlen=maxlen)
        self._subscribers: list[asyncio.Queue[tuple[str, dict[str, Any]]]] = []

    def publish(self, event: str, payload: dict[str, Any]) -> None:
        item = (event, payload)
        self._events.append(item)
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(item)
            except asyncio.QueueFull:
                continue

    def subscribe(self) -> asyncio.Queue[tuple[str, dict[str, Any]]]:
        queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue(maxsize=64)
        for item in self._events:
            queue.put_nowait(item)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[tuple[str, dict[str, Any]]]) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)
