"""Strategy apply sequence tests (ch15 §15.8)."""

import json
from pathlib import Path

from yoruu.data.database import Database
from yoruu.review.strategy_applier import StrategyApplier
from yoruu.review.strategy_writer import StrategyWriter
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)
from yoruu.types import Mode


def _strategy() -> StrategyConfig:
    return StrategyConfig(
        version=1,
        parameters=StrategyParameters(
            MIN_PROB=0.87,
            MIN_EDGE=0.06,
            KELLY_FRACTION=0.65,
            PERSISTENCE_THRESHOLD=0.70,
        ),
        constraints={
            "MIN_PROB": ParameterConstraints(min=0.80, max=0.95),
            "MIN_EDGE": ParameterConstraints(min=0.03, max=0.15),
            "KELLY_FRACTION": ParameterConstraints(min=0.10, max=1.00),
            "PERSISTENCE_THRESHOLD": ParameterConstraints(min=0.50, max=0.90),
        },
    )


def test_strategy_apply_writes_version(tmp_path: Path) -> None:
    strategy_path = tmp_path / "strategy.json"
    strategy_path.write_text(json.dumps(_strategy().to_json_dict()), encoding="utf-8")
    db = Database(tmp_path / "db.sqlite")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=Mode.PAPER,
        balance=1000.0,
        daily_loss_limit=30.0,
        strategy_version=1,
    )
    db.ensure_strategy_version_seed(
        json.dumps(_strategy().to_json_dict(), ensure_ascii=False),
        strategy_version=1,
    )
    writer = StrategyWriter(strategy_path)
    applier = StrategyApplier(db, writer)
    proposal = {
        "parameters": {
            "MIN_PROB": 0.88,
            "MIN_EDGE": 0.06,
            "KELLY_FRACTION": 0.65,
            "PERSISTENCE_THRESHOLD": 0.70,
        },
        "rationale": "微調整テスト",
        "applied_by": "USER",
    }
    result = applier.apply(proposal, _strategy())
    assert result.new_version >= 2
    saved = json.loads(strategy_path.read_text(encoding="utf-8"))
    assert saved["parameters"]["MIN_PROB"] == 0.88
    db.close()
