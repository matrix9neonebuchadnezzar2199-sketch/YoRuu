"""OHLC API tests (PHASE 5 M5.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from helpers import write_isolated_config
from yoruu.api.sse.bus import ValidatingEventBus
from yoruu.config.settings import load_settings
from yoruu.data.database import Database
from yoruu.infra.fx_provider import FxRateProvider
from yoruu.infra.ohlc_provider import OhlcProvider
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)
from yoruu.types import Mode
from yoruu.web import deps
from yoruu.web.app import create_app


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
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
            "MIN_EDGE": ParameterConstraints(min=0.01, max=0.2),
            "KELLY_FRACTION": ParameterConstraints(min=0.1, max=1.0),
            "PERSISTENCE_THRESHOLD": ParameterConstraints(min=0.5, max=0.95),
        },
    )
    cfg = write_isolated_config(tmp_path, strategy)
    db = Database(tmp_path / "yoruu.db")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=Mode.PAPER,
        balance=1000.0,
        principal=1000.0,
        daily_loss_limit=30.0,
        strategy_version=1,
    )
    db.close()

    settings = load_settings(cfg)
    monkeypatch.setattr(deps, "_settings", settings)
    monkeypatch.setattr(deps, "_event_bus", ValidatingEventBus())
    monkeypatch.setattr(deps, "_fx_provider", FxRateProvider(settings.display.fx))
    monkeypatch.setattr(deps, "_ohlc_provider", OhlcProvider())
    return TestClient(create_app())


def test_ohlc_returns_bars(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/ohlc?bars=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "BTCUSDT"
    assert body["interval"] == "5m"
    bars = body["bars"]
    assert len(bars) == 10
    first = bars[0]
    assert {"ts", "open", "high", "low", "close", "volume"} <= set(first.keys())
    assert first["high"] >= first["low"]


def test_ohlc_rejects_over_max_bars(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/ohlc?bars=999")
    assert resp.status_code == 422


def test_ohlc_default_sixty_bars(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/ohlc")
    assert resp.status_code == 200
    assert len(resp.json()["bars"]) == 60
