"""Lab SSE fixture payloads (mirror mock-data.js SSE_PAYLOADS)."""

from __future__ import annotations

from typing import Any

# Keys and shapes match docs/mockups/shared/mock-data.js (§F T4.1 / B1).
LAB_SSE_FIXTURES: dict[str, dict[str, Any]] = {
    "state_changed": {
        "from": "TRADING",
        "to": "MONITORING_POSITION",
        "timestamp": "2026-05-27T14:32:48+09:00",
        "reason": "position_opened",
    },
    "markov_update": {
        "computed_at": "2026-05-27T14:35:00+09:00",
        "window_size": 20,
        "matrix": {
            "p_up_up": 0.578,
            "p_up_down": 0.422,
            "p_down_up": 0.388,
            "p_down_down": 0.612,
        },
        "rolling_persistence": 0.578,
        "last_direction": "UP",
        "threshold_met": False,
        "wait_reason": "persistence",
    },
    "health_degraded": {
        "component": "polymarket_ws",
        "reason": "disconnected",
        "retry_count": 2,
        "timestamp": "2026-05-27T14:32:48+09:00",
    },
    "health_recovered": {
        "component": "polymarket_ws",
        "reason": "reconnected",
        "recovery_duration_sec": 8,
        "timestamp": "2026-05-27T14:32:48+09:00",
    },
    "position_opened": {
        "trade_id": 71,
        "market": "BTC_5MIN_UPDOWN",
        "side": "YES",
        "size_usd": 7.1,
        "entry_price": 0.62,
        "expires_at": "2026-05-27T14:37:00+09:00",
        "edge_at_entry": 0.071,
        "persistence_at_entry": 0.72,
    },
    "position_closed": {
        "trade_id": 71,
        "exit_price": 1.0,
        "pnl": 4.35,
        "win": True,
        "closed_at": "2026-05-27T14:37:00+09:00",
    },
    "nightly_report_ready": {
        "report_date": "2026-05-27",
        "report_id": 7,
        "summary_url": "/api/v1/reports/7",
    },
    "mode_changed": {
        "from": "PAPER",
        "to": "SIMMER",
        "timestamp": "2026-05-27T14:32:48+09:00",
    },
    "emergency_stop_triggered": {
        "trigger": "dashboard_button",
        "timestamp": "2026-05-27T14:32:48+09:00",
        "open_positions_closed": 1,
    },
    "alert_added": {
        "id": 143,
        "code": "W_HEALTH_001",
        "severity": "WARN",
        "message": "WebSocket reconnected after 8s",
        "created_at": "2026-05-27T14:32:48+09:00",
    },
    "strategy_applied": {
        "new_version": 4,
        "previous_version": 3,
        "applied_by": "NIGHTLY_REVIEW",
        "rationale": "lab fixture",
        "applied_at": "2026-05-28T04:15:00+09:00",
        "diff": {"MIN_PROB": [0.87, 0.89]},
    },
    "principal_changed": {
        "kind": "DEPOSIT",
        "amount": 500.0,
        "balance_before": 1042.18,
        "balance_after": 1542.18,
        "principal_before": 1000.0,
        "principal_after": 1500.0,
        "locked_principal": 7.10,
        "withdrawable_principal": 1492.90,
        "total_assets": 1500.0,
        "cumulative_pnl": 0.0,
        "ts_utc": "2026-05-28T05:30:00+00:00",
        "note": "lab_fixture",
        "severity": "INFO",
    },
}
