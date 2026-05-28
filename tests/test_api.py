"""FastAPI route smoke tests."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from helpers import write_isolated_config
from yoruu.data.database import Database
from yoruu.types import Mode
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)
from yoruu.web.app import create_app
from yoruu.web import deps


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
    settings_paths_db = tmp_path / "yoruu.db"
    db = Database(settings_paths_db)
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
    return TestClient(create_app())


def test_health_endpoint(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body


def test_state_endpoint(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/state")
    assert resp.status_code == 200
    assert "balance" in resp.json()


def test_api_v1_route_smoke(api_client: TestClient) -> None:
    """Exercise REST v1 surface (ch10 §10.6)."""

    get_paths = [
        "/api/v1/trades",
        "/api/v1/trades/export",
        "/api/v1/trades/export?format=csv",
        "/api/v1/positions",
        "/api/v1/markov/current",
        "/api/v1/markov/history",
        "/api/v1/strategy/current",
        "/api/v1/strategy/versions",
        "/api/v1/emergency/logs",
        "/api/v1/alerts",
        "/api/v1/reports",
        "/api/v1/whatif/scenarios",
        "/api/v1/settings",
        "/api/v1/i18n/ja",
        "/api/v1/principal",
        "/api/v1/principal/transactions",
        "/api/v1/fx/usd_jpy",
    ]
    for path in get_paths:
        resp = api_client.get(path)
        assert resp.status_code in (200, 404), path

    assert api_client.get("/api/v1/trades/999").status_code == 404
    assert api_client.get("/api/v1/strategy/versions/1").status_code in (200, 404)
    assert api_client.get("/api/v1/reports/1").status_code in (200, 404)

    post_calls = [
        ("/api/v1/strategy/apply", {"parameters": {"MIN_PROB": 0.88}, "rationale": "lab smoke"}),
        ("/api/v1/strategy/rollback", None),
        ("/api/v1/mode/switch", {"mode": "paper"}),
        ("/api/v1/emergency/stop", None),
        ("/api/v1/emergency/recover", None),
        ("/api/v1/alerts/1/read", None),
        ("/api/v1/alerts/read-all", None),
        ("/api/v1/reports/1/preview-apply", None),
        ("/api/v1/reports/regenerate", None),
        ("/api/v1/whatif/simulate", None),
        ("/api/v1/whatif/scenarios", None),
        ("/api/v1/settings", None),
    ]
    for path, body in post_calls:
        if body is None:
            resp = api_client.post(path)
        else:
            resp = api_client.post(path, json=body)
        assert resp.status_code == 200, path
