"""SSE stream integration with ValidatingEventBus."""

import pytest
from fastapi.testclient import TestClient

from helpers import write_isolated_config
from yoruu.api.sse.fixtures import LAB_SSE_FIXTURES
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)
from yoruu.web import deps
from yoruu.web.app import create_app


@pytest.fixture
def sse_client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    strategy = StrategyConfig(
        version=1,
        parameters=StrategyParameters(
            MIN_PROB=0.87,
            MIN_EDGE=0.06,
            KELLY_FRACTION=0.65,
            PERSISTENCE_THRESHOLD=0.70,
        ),
        constraints={
            "MIN_PROB": ParameterConstraints(min=0.8, max=0.95),
        },
    )
    cfg = write_isolated_config(tmp_path, strategy)
    from yoruu.config.settings import load_settings

    monkeypatch.setattr(deps, "_settings", load_settings(cfg))
    from yoruu.api.sse.bus import ValidatingEventBus

    monkeypatch.setattr(deps, "_event_bus", ValidatingEventBus())
    return TestClient(create_app())


def test_sse_bus_stores_validated_payload() -> None:
    from yoruu.api.sse.bus import ValidatingEventBus
    from yoruu.web.event_bus import MemoryEventBus

    bus = ValidatingEventBus(MemoryEventBus())
    bus.publish("mode_changed", LAB_SSE_FIXTURES["mode_changed"])
    assert bus.inner._events[-1][0] == "mode_changed"
    assert bus.inner._events[-1][1]["from"] == "PAPER"


def test_sse_stream_route_exists(sse_client: TestClient) -> None:
    """Stream endpoint is registered (full read would block)."""

    routes = [getattr(r, "path", None) for r in sse_client.app.routes]
    assert "/api/v1/events/stream" in routes
