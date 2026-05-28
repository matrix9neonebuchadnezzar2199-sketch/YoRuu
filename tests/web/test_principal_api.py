"""Principal and FX REST API (M4.5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from helpers import write_isolated_config
from yoruu.api.sse.bus import ValidatingEventBus
from yoruu.config.settings import DisplayFxSettings, DisplaySettings
from yoruu.data.database import Database
from yoruu.infra.fx_provider import FxRateProvider
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
    db.ensure_strategy_version_seed(
        json.dumps(strategy.to_json_dict(), ensure_ascii=False),
        strategy_version=1,
    )
    db.close()

    from yoruu.config.settings import load_settings

    settings = load_settings(cfg)
    monkeypatch.setattr(deps, "_settings", settings)
    monkeypatch.setattr(deps, "_event_bus", ValidatingEventBus())
    monkeypatch.setattr(deps, "_fx_provider", FxRateProvider(settings.display.fx))
    return TestClient(create_app())


def test_get_principal(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/principal")
    assert resp.status_code == 200
    body = resp.json()
    assert body["principal"] == 1000.0
    assert "deposit_count" in body


def test_get_principal_transactions(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/principal/transactions?limit=10")
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_deposit_and_withdraw(api_client: TestClient) -> None:
    dep = api_client.post("/api/v1/principal/deposit", json={"amount": 50.0, "note": "api"})
    assert dep.status_code == 200
    assert dep.json()["principal"] == 1050.0

    bad = api_client.post(
        "/api/v1/principal/withdraw",
        json={"amount": 10.0, "confirm": False},
    )
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "E_PRINCIPAL_004"

    ok = api_client.post(
        "/api/v1/principal/withdraw",
        json={"amount": 10.0, "confirm": True},
    )
    assert ok.status_code == 200
    assert ok.json()["balance"] == 1040.0


def test_deposit_over_max(api_client: TestClient) -> None:
    resp = api_client.post("/api/v1/principal/deposit", json={"amount": 200_000.0})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "E_PRINCIPAL_003"


def test_fx_usd_jpy_mocked(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(self: FxRateProvider):
        from yoruu.infra.fx_provider import FxRateQuote

        return FxRateQuote(
            pair="USD/JPY",
            rate=150.25,
            fetched_at="2026-05-28T12:00:00+00:00",
            source="exchangerate_host",
            stale=False,
        )

    monkeypatch.setattr(FxRateProvider, "_fetch_live", fake_fetch)
    resp = api_client.get("/api/v1/fx/usd_jpy")
    assert resp.status_code == 200
    assert resp.json()["rate"] == 150.25


def test_fx_disabled_returns_503(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    disabled = DisplaySettings(
        fx=DisplayFxSettings(enabled=False, provider="exchangerate_host")
    )
    monkeypatch.setattr(deps, "_fx_provider", FxRateProvider(disabled.fx))
    resp = api_client.get("/api/v1/fx/usd_jpy")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "E_FX_004"
