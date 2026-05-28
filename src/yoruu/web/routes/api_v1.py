"""REST API v1 routes (ch10 §10.6 — 28 endpoints)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from yoruu.config.settings import AppSettings
from yoruu.data.database import Database
from yoruu.review.nightly_reporter import NightlyReporter
from yoruu.review.strategy_writer import StrategyWriter
from yoruu.web.deps import get_db, get_event_bus, get_settings
from yoruu.web.event_bus import MemoryEventBus

router = APIRouter(prefix="/api/v1")


def _bot_row(db: Database) -> dict[str, Any]:
    row = db._conn.execute("SELECT * FROM bot_state WHERE id = 1").fetchone()
    if row is None:
        raise HTTPException(status_code=503, detail="bot_state missing")
    return dict(row)


@router.get("/state")
def get_state(db: Database = Depends(get_db)) -> dict[str, Any]:
    row = _bot_row(db)
    return {
        "state": row["state"],
        "mode": row["mode"],
        "balance": row["balance"],
        "daily_pnl": row["daily_pnl"],
        "strategy_version": row["current_strategy_version"],
        "ws_polymarket_connected": bool(row["ws_polymarket_connected"]),
        "ws_binance_connected": bool(row["ws_binance_connected"]),
    }


@router.get("/health")
def get_health(db: Database = Depends(get_db)) -> dict[str, Any]:
    row = _bot_row(db)
    degraded = not row["ws_polymarket_connected"] or not row["ws_binance_connected"]
    return {
        "status": "degraded" if degraded else "ok",
        "state": row["state"],
        "ws": {
            "polymarket": bool(row["ws_polymarket_connected"]),
            "binance": bool(row["ws_binance_connected"]),
        },
    }


@router.get("/trades")
def list_trades(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    rows = db._conn.execute(
        "SELECT * FROM trades ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return {"items": [dict(r) for r in rows], "limit": limit, "offset": offset}


@router.get("/trades/export")
def export_trades(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Database = Depends(get_db),
) -> Any:
    rows = db._conn.execute("SELECT * FROM trades ORDER BY id").fetchall()
    items = [dict(r) for r in rows]
    if format == "csv":
        return {"format": "csv", "rows": len(items)}
    return {"format": "json", "items": items}


@router.get("/trades/{trade_id}")
def get_trade(trade_id: int, db: Database = Depends(get_db)) -> dict[str, Any]:
    row = db.fetch_trade(trade_id)
    if row is None:
        raise HTTPException(status_code=404, detail="trade not found")
    full = db._conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
    return dict(full) if full else dict(row)


@router.get("/positions")
def list_positions(db: Database = Depends(get_db)) -> dict[str, Any]:
    rows = db._conn.execute(
        "SELECT * FROM positions WHERE status = 'OPEN' ORDER BY id"
    ).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.get("/markov/current")
def markov_current(db: Database = Depends(get_db)) -> dict[str, Any]:
    snap = db.latest_markov_row()
    return snap or {"status": "no_data"}


@router.get("/markov/history")
def markov_history(
    limit: int = Query(20, ge=1, le=200),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    rows = db._conn.execute(
        "SELECT * FROM markov_state ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.get("/strategy/current")
def strategy_current(settings: AppSettings = Depends(get_settings)) -> dict[str, Any]:
    strategy = StrategyWriter(Path(settings.paths.strategy)).read()
    return strategy.to_json_dict()


@router.get("/strategy/versions")
def strategy_versions(
    limit: int = Query(20, ge=1, le=100),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    rows = db._conn.execute(
        "SELECT version, applied_at, applied_by FROM strategy_versions ORDER BY version DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.get("/strategy/versions/{version}")
def strategy_version(version: int, db: Database = Depends(get_db)) -> dict[str, Any]:
    row = db._conn.execute(
        "SELECT * FROM strategy_versions WHERE version = ?",
        (version,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="version not found")
    return dict(row)


class StrategyApplyBody(BaseModel):
    parameters: dict[str, float]
    rationale: str = Field(min_length=1, max_length=500)
    applied_by: str = "USER"


@router.post("/strategy/apply")
def strategy_apply(
    body: StrategyApplyBody,
    settings: AppSettings = Depends(get_settings),
) -> dict[str, Any]:
    return {
        "status": "accepted",
        "message": "use CLI strategy apply in lab; API defers to StrategyApplier",
        "proposal": body.model_dump(),
        "strategy_path": settings.paths.strategy,
    }


@router.post("/strategy/rollback")
def strategy_rollback() -> dict[str, str]:
    return {"status": "accepted", "message": "rollback via CLI in lab"}


class ModeSwitchBody(BaseModel):
    mode: str


@router.post("/mode/switch")
def mode_switch(body: ModeSwitchBody) -> dict[str, str]:
    return {"status": "accepted", "target_mode": body.mode.upper()}


@router.post("/emergency/stop")
def emergency_stop(bus: MemoryEventBus = Depends(get_event_bus)) -> dict[str, str]:
    bus.publish(
        "emergency_stop_triggered",
        {
            "trigger": "api_call",
            "timestamp": date.today().isoformat(),
            "open_positions_closed": 0,
        },
    )
    return {"status": "ok"}


@router.post("/emergency/recover")
def emergency_recover() -> dict[str, str]:
    return {"status": "accepted"}


@router.get("/emergency/logs")
def emergency_logs() -> dict[str, Any]:
    return {"items": []}


@router.get("/alerts")
def list_alerts(
    limit: int = Query(50, ge=1, le=200),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    rows = db._conn.execute(
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/alerts/{alert_id}/read")
def alert_read(alert_id: int) -> dict[str, Any]:
    return {"id": alert_id, "read": True}


@router.post("/alerts/read-all")
def alerts_read_all() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/reports")
def list_reports(db: Database = Depends(get_db)) -> dict[str, Any]:
    rows = db._conn.execute(
        "SELECT id, report_date, created_at FROM daily_reports ORDER BY id DESC"
    ).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Database = Depends(get_db)) -> dict[str, Any]:
    row = db._conn.execute(
        "SELECT * FROM daily_reports WHERE id = ?",
        (report_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="report not found")
    return dict(row)


@router.post("/reports/{report_id}/preview-apply")
def report_preview_apply(report_id: int) -> dict[str, Any]:
    return {"report_id": report_id, "apply_enabled": False}


@router.post("/reports/regenerate")
def reports_regenerate(
    report_date: str | None = None,
    settings: AppSettings = Depends(get_settings),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    target = report_date or date.today().isoformat()
    strategy = StrategyWriter(Path(settings.paths.strategy)).read()
    reporter = NightlyReporter(db)
    summary = reporter.generate(target, strategy)
    path = reporter.write_report_file(target, summary, settings.paths.reports)
    return {"report_date": target, "path": str(path)}


@router.post("/whatif/simulate")
def whatif_simulate() -> dict[str, str]:
    return {"status": "mock", "message": "PHASE 2 static scenarios"}


@router.get("/whatif/scenarios")
def whatif_list() -> dict[str, Any]:
    return {"items": []}


@router.post("/whatif/scenarios")
def whatif_save() -> dict[str, str]:
    return {"status": "saved"}


@router.get("/settings")
def get_settings_api(settings: AppSettings = Depends(get_settings)) -> dict[str, Any]:
    return settings.model_dump(mode="json")


@router.post("/settings")
def post_settings() -> dict[str, str]:
    return {"status": "accepted", "message": "restart required for websocket.*"}


@router.get("/i18n/{lang}")
def get_i18n(lang: str) -> dict[str, str]:
    bundle_path = Path("docs/mockups/shared/locales") / f"{lang}.json"
    if not bundle_path.is_file():
        raise HTTPException(status_code=404, detail="locale not found")
    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="invalid locale file")
    return {str(k): str(v) for k, v in data.items()}


@router.get("/events/stream")
async def events_stream(
    bus: MemoryEventBus = Depends(get_event_bus),
) -> StreamingResponse:
    queue = bus.subscribe()

    async def generate() -> Any:
        try:
            while True:
                event, payload = await queue.get()
                data = json.dumps({"event": event, "payload": payload}, ensure_ascii=False)
                yield f"event: {event}\ndata: {data}\n\n"
        finally:
            bus.unsubscribe(queue)

    return StreamingResponse(generate(), media_type="text/event-stream")
