"""API strategy apply/rollback and SSE stream tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from helpers import write_isolated_config
from yoruu.api.sse.bus import ValidatingEventBus
from yoruu.data.database import Database
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
    strategy_path = tmp_path / "strategy.json"
    strategy_path.write_text(
        json.dumps(strategy.to_json_dict(), ensure_ascii=False),
        encoding="utf-8",
    )

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
    return TestClient(create_app())


def test_sse_contracts_endpoint(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/sse/contracts")
    assert resp.status_code == 200
    assert len(resp.json()["events"]) == 12


def test_sse_fixtures_endpoint(api_client: TestClient) -> None:
    resp = api_client.get("/api/v1/sse/fixtures")
    assert resp.status_code == 200
    assert "strategy_applied" in resp.json()["fixtures"]


def test_strategy_apply_and_rollback(api_client: TestClient, tmp_path: Path) -> None:
    apply_resp = api_client.post(
        "/api/v1/strategy/apply",
        json={
            "parameters": {"MIN_PROB": 0.88},
            "rationale": "lab API apply test",
            "applied_by": "USER",
        },
    )
    assert apply_resp.status_code == 200, apply_resp.text
    assert apply_resp.json()["new_version"] >= 2

    rollback_resp = api_client.post(
        "/api/v1/strategy/rollback",
        json={"reason": "undo lab apply"},
    )
    assert rollback_resp.status_code == 200, rollback_resp.text
    assert rollback_resp.json()["new_version"] >= 3

    strategy_path = tmp_path / "strategy.json"
    data = json.loads(strategy_path.read_text(encoding="utf-8"))
    assert data["parameters"]["MIN_PROB"] == pytest.approx(0.87)


def test_emergency_stop_sse_shape(api_client: TestClient) -> None:
    bus: ValidatingEventBus = deps.get_event_bus()
    queue = bus.subscribe()
    resp = api_client.post("/api/v1/emergency/stop")
    assert resp.status_code == 200
    event, payload = queue.get_nowait()
    assert event == "emergency_stop_triggered"
    assert "timestamp" in payload
    assert "T" in payload["timestamp"]
