"""MemoryEventBus tests."""

import asyncio

import pytest

from yoruu.web.event_bus import MemoryEventBus


def test_event_bus_publish_subscribe() -> None:
    bus = MemoryEventBus(maxlen=4)
    queue = bus.subscribe()
    bus.publish("trade_opened", {"id": 1})
    item = queue.get_nowait()
    assert item[0] == "trade_opened"
    assert item[1]["id"] == 1
    bus.unsubscribe(queue)
    assert queue not in bus._subscribers


@pytest.mark.asyncio
async def test_event_bus_queue_full_skipped() -> None:
    bus = MemoryEventBus()
    queue: asyncio.Queue = asyncio.Queue(maxsize=1)
    bus._subscribers.append(queue)
    queue.put_nowait(("a", {}))
    bus.publish("b", {"x": 1})
