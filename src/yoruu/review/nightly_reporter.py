"""Nightly report JSON generator (ch15 §15.4)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from yoruu.data.database import Database
from yoruu.strategy.models import StrategyConfig
from yoruu.types import Mode

_JST = timezone(timedelta(hours=9))
_WAIT_REASON_KEYS = ("persistence", "edge", "prob", "liquidity", "risk_budget")


class NightlyReporter:
    """Aggregate DB stats into summary_json (no LLM)."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def generate(self, target_date: str, strategy: StrategyConfig) -> dict[str, Any]:
        mode = self._db.get_mode()
        if mode == Mode.BACKTEST:
            raise ValueError("BACKTEST does not generate nightly reports")

        rows = self._db.trades_for_date(target_date, mode)
        wins = sum(1 for r in rows if r["win"] == 1)
        losses = sum(1 for r in rows if r["win"] == 0)
        total = len(rows)
        closed_rows = [r for r in rows if r["status"] == "CLOSED"]
        pnl = sum(float(r["pnl"] or 0) for r in closed_rows)
        balance_end = self._db.get_balance()
        balance_start = balance_end - pnl

        markov = self._db.latest_markov_row()
        history = self._db.markov_persistence_stats_24h()
        markov_snapshot: dict[str, Any]
        if markov:
            markov_snapshot = {
                "computed_at": markov["computed_at"],
                "window_size": markov["window_size"],
                "matrix": {
                    "p_up_up": markov["p_up_up"],
                    "p_up_down": markov["p_up_down"],
                    "p_down_up": markov["p_down_up"],
                    "p_down_down": markov["p_down_down"],
                },
                "rolling_persistence": markov["rolling_persistence"],
                "last_direction": markov["last_direction"],
                "history_summary": history,
            }
        else:
            markov_snapshot = {
                "computed_at": None,
                "window_size": 0,
                "matrix": {},
                "rolling_persistence": None,
                "last_direction": None,
                "history_summary": history,
            }

        notes: list[str] = []
        if total == 0:
            notes.append("no_trades_today")

        win_rate = wins / (wins + losses) if (wins + losses) > 0 else None
        by_state: dict[str, dict[str, int]] | None = None
        if total > 0:
            by_state = {
                "TRADING": {"count": total, "win": wins},
                "MONITORING_POSITION": {"count": total, "win": wins},
            }

        performance: dict[str, Any] = {
            "trades_total": total,
            "trades_win": wins,
            "trades_loss": losses,
            "trades_expired": sum(1 for r in rows if r["status"] == "EXPIRED"),
            "win_rate": win_rate,
            "pnl_usd": pnl,
            "pnl_pct": (pnl / balance_start * 100) if balance_start else None,
            "balance_start_usd": balance_start,
            "balance_end_usd": balance_end,
            "max_drawdown_usd": _max_drawdown(closed_rows),
            "avg_edge_at_entry": _avg(rows, "edge_at_entry"),
            "avg_persistence_at_entry": _avg(rows, "persistence_at_entry"),
            "by_state": by_state,
        }

        constraints = {
            key: {"min": c.min, "max": c.max, "default": c.default}
            for key, c in strategy.constraints.items()
        }

        summary: dict[str, Any] = {
            "schema_version": "1.0",
            "report_date": target_date,
            "generated_at": datetime.now(_JST).isoformat(),
            "mode": mode.value,
            "current_strategy": strategy.to_report_strategy_dict(),
            "performance": performance,
            "markov_snapshot": markov_snapshot,
            "trade_breakdown": {
                "by_side": _by_side(rows),
                "by_hour_jst": _by_hour_jst(rows),
                "wait_reason_distribution": {k: 0 for k in _WAIT_REASON_KEYS},
            },
            "constraints": constraints,
            "notes": notes,
        }
        self._db.insert_daily_report(target_date, summary)
        self._db.commit()
        return summary

    def write_report_file(self, target_date: str, summary: dict[str, Any], reports_dir: str) -> str:
        from pathlib import Path

        out_dir = Path(reports_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{target_date}.json"
        path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)


def _avg(rows: list[Any], field: str) -> float | None:
    values = [float(r[field]) for r in rows if r[field] is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _max_drawdown(closed_rows: list[Any]) -> float | None:
    if not closed_rows:
        return None
    ordered = sorted(closed_rows, key=lambda r: str(r["closed_at"] or r["opened_at"]))
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for row in ordered:
        cumulative += float(row["pnl"] or 0)
        peak = max(peak, cumulative)
        max_dd = min(max_dd, cumulative - peak)
    return max_dd if max_dd != 0.0 else None


def _by_side(rows: list[Any]) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for row in rows:
        side = str(row["side"])
        bucket = result.setdefault(side, {"count": 0, "win": 0, "pnl_usd": 0.0})
        bucket["count"] = int(bucket["count"]) + 1
        if row["win"] == 1:
            bucket["win"] = int(bucket["win"]) + 1
        if row["status"] == "CLOSED" and row["pnl"] is not None:
            bucket["pnl_usd"] = float(bucket["pnl_usd"]) + float(row["pnl"])
    return result


def _by_hour_jst(rows: list[Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        opened = str(row["opened_at"])
        try:
            if opened.endswith("Z"):
                dt = datetime.fromisoformat(opened.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(opened)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            hour = dt.astimezone(_JST).strftime("%H")
        except ValueError:
            hour = "00"
        bucket = result.setdefault(hour, {"count": 0, "win": 0})
        bucket["count"] += 1
        if row["win"] == 1:
            bucket["win"] += 1
    return result
