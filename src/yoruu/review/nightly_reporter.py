"""Nightly report JSON generator (ch15 §15.4)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from yoruu.data.database import Database
from yoruu.strategy.models import StrategyConfig
from yoruu.types import Mode


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
        pnl = sum(float(r["pnl"] or 0) for r in rows if r["status"] == "CLOSED")
        balance_end = self._db.get_balance()
        balance_start = balance_end - pnl

        markov = self._db.latest_markov_row()
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
            }
        else:
            markov_snapshot = {
                "computed_at": None,
                "window_size": 0,
                "matrix": {},
                "rolling_persistence": None,
                "last_direction": None,
            }

        notes: list[str] = []
        if total == 0:
            notes.append("no_trades_today")

        win_rate = wins / (wins + losses) if (wins + losses) > 0 else None
        performance = {
            "trades_total": total,
            "trades_win": wins,
            "trades_loss": losses,
            "trades_expired": sum(1 for r in rows if r["status"] == "EXPIRED"),
            "win_rate": win_rate,
            "pnl_usd": pnl,
            "pnl_pct": (pnl / balance_start * 100) if balance_start else None,
            "balance_start_usd": balance_start,
            "balance_end_usd": balance_end,
            "max_drawdown_usd": None,
            "avg_edge_at_entry": _avg(rows, "edge_at_entry"),
            "avg_persistence_at_entry": _avg(rows, "persistence_at_entry"),
        }

        constraints = {
            key: {"min": c.min, "max": c.max, "default": c.default}
            for key, c in strategy.constraints.items()
        }

        summary: dict[str, Any] = {
            "schema_version": "1.0",
            "report_date": target_date,
            "generated_at": datetime.now(UTC).astimezone().isoformat(),
            "mode": mode.value,
            "current_strategy": strategy.to_json_dict(),
            "performance": performance,
            "markov_snapshot": markov_snapshot,
            "trade_breakdown": {"by_side": _by_side(rows)},
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


def _by_side(rows: list[Any]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in rows:
        side = str(row["side"])
        bucket = result.setdefault(side, {"count": 0, "win": 0})
        bucket["count"] += 1
        if row["win"] == 1:
            bucket["win"] += 1
    return result
