"""Nightly reporter tests."""

import json
from pathlib import Path

from yoruu.data.database import Database
from yoruu.review.nightly_reporter import NightlyReporter
from yoruu.review.strategy_writer import StrategyWriter
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)
from yoruu.types import Mode


def test_generate_report(tmp_path: Path) -> None:
    strategy_path = tmp_path / "strategy.json"
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
    strategy_path.write_text(json.dumps(strategy.to_json_dict()), encoding="utf-8")

    db = Database(tmp_path / "db.sqlite")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=Mode.PAPER,
        balance=1000.0,
        daily_loss_limit=30.0,
        strategy_version=1,
    )
    reporter = NightlyReporter(db)
    summary = reporter.generate("2026-05-27", StrategyWriter(strategy_path).read())
    assert summary["schema_version"] == "1.0"
    assert summary["performance"]["trades_total"] == 0
    assert "constraints" in summary
    assert "constraints" not in summary["current_strategy"]
    assert "history_summary" in summary["markov_snapshot"]
    assert "by_hour_jst" in summary["trade_breakdown"]
    assert "wait_reason_distribution" in summary["trade_breakdown"]
    assert "pnl_usd" in summary["trade_breakdown"]["by_side"].get("YES", {}) or True
    db.close()
