"""Lab smoke for paper-24h harness (not a full 24h run)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from helpers import write_isolated_config
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)


def test_paper_24h_max_cycles(tmp_path: Path) -> None:
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
    cfg = write_isolated_config(tmp_path, strategy)
    (tmp_path / "strategy.json").write_text(
        json.dumps(strategy.to_json_dict(), ensure_ascii=False),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "yoruu.cli",
            "paper-24h",
            "--config",
            str(cfg),
            "--hours",
            "1",
            "--interval-sec",
            "1",
            "--max-cycles",
            "2",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK: 2 paper cycles" in proc.stdout
