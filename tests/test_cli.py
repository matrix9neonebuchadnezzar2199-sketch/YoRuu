"""CLI smoke tests (Click runner)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from helpers import init_db, write_isolated_config
from yoruu.cli import main
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)


@pytest.fixture
def strategy_config() -> StrategyConfig:
    return StrategyConfig(
        version=1,
        parameters=StrategyParameters(
            MIN_PROB=0.87,
            MIN_EDGE=0.06,
            KELLY_FRACTION=0.65,
            PERSISTENCE_THRESHOLD=0.70,
        ),
        constraints={
            "MIN_PROB": ParameterConstraints(min=0.8, max=0.95),
            "MIN_EDGE": ParameterConstraints(min=0.03, max=0.15),
            "KELLY_FRACTION": ParameterConstraints(min=0.10, max=1.00),
            "PERSISTENCE_THRESHOLD": ParameterConstraints(min=0.50, max=0.90),
        },
    )


def _ensure_dirs(tmp_path: Path) -> None:
    for name in ("logs", "historical", "reports"):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)


def test_config_validate_ok(tmp_path: Path, strategy_config: StrategyConfig) -> None:
    cfg = write_isolated_config(tmp_path, strategy_config)
    result = CliRunner().invoke(main, ["config", "validate", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "OK:" in result.output


def test_config_validate_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    result = CliRunner().invoke(main, ["config", "validate", "--config", str(missing)])
    assert result.exit_code != 0
    assert "FAIL:" in result.output


def test_principal_deposit_cli(tmp_path: Path, strategy_config: StrategyConfig) -> None:
    _ensure_dirs(tmp_path)
    cfg = write_isolated_config(tmp_path, strategy_config)
    CliRunner().invoke(main, ["db", "init", "--config", str(cfg)])
    result = CliRunner().invoke(
        main,
        ["principal", "deposit", "25", "--config", str(cfg), "--note", "cli_test"],
    )
    assert result.exit_code == 0
    body = json.loads(result.output)
    assert body["principal"] == 1025.0


def test_principal_withdraw_requires_confirm(tmp_path: Path, strategy_config: StrategyConfig) -> None:
    _ensure_dirs(tmp_path)
    cfg = write_isolated_config(tmp_path, strategy_config)
    runner = CliRunner()
    runner.invoke(main, ["db", "init", "--config", str(cfg)])
    result = runner.invoke(main, ["principal", "withdraw", "5", "--config", str(cfg)])
    assert result.exit_code != 0
    assert "E_PRINCIPAL_004" in result.output


def test_principal_show_cli(tmp_path: Path, strategy_config: StrategyConfig) -> None:
    _ensure_dirs(tmp_path)
    cfg = write_isolated_config(tmp_path, strategy_config)
    CliRunner().invoke(main, ["db", "init", "--config", str(cfg)])
    result = CliRunner().invoke(main, ["principal", "show", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "principal" in json.loads(result.output)


def test_db_init_ok(tmp_path: Path, strategy_config: StrategyConfig) -> None:
    _ensure_dirs(tmp_path)
    cfg = write_isolated_config(tmp_path, strategy_config)
    result = CliRunner().invoke(main, ["db", "init", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "OK: database" in result.output


def test_paper_evaluate_once(tmp_path: Path, strategy_config: StrategyConfig) -> None:
    _ensure_dirs(tmp_path)
    cfg = write_isolated_config(tmp_path, strategy_config)
    CliRunner().invoke(main, ["db", "init", "--config", str(cfg)])
    result = CliRunner().invoke(main, ["paper", "evaluate-once", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "should_enter" in result.output


def test_paper_evaluate_once_rejects_live_mode(
    tmp_path: Path, strategy_config: StrategyConfig
) -> None:
    cfg = write_isolated_config(tmp_path, strategy_config)
    text = cfg.read_text(encoding="utf-8").replace("mode: PAPER", "mode: LIVE")
    cfg.write_text(text, encoding="utf-8")
    result = CliRunner().invoke(main, ["paper", "evaluate-once", "--config", str(cfg)])
    assert result.exit_code != 0


def test_nightly_generate(tmp_path: Path, strategy_config: StrategyConfig) -> None:
    _ensure_dirs(tmp_path)
    cfg = write_isolated_config(tmp_path, strategy_config)
    CliRunner().invoke(main, ["db", "init", "--config", str(cfg)])
    result = CliRunner().invoke(
        main,
        ["nightly", "generate", "--date", "2026-05-27", "--config", str(cfg)],
    )
    assert result.exit_code == 0
    assert "OK:" in result.output


def test_config_validate_invalid_yaml(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("mode: [not", encoding="utf-8")
    result = CliRunner().invoke(main, ["config", "validate", "--config", str(bad)])
    assert result.exit_code != 0


def test_strategy_apply_cli(tmp_path: Path, strategy_config: StrategyConfig) -> None:
    _ensure_dirs(tmp_path)
    cfg = write_isolated_config(tmp_path, strategy_config)
    CliRunner().invoke(main, ["db", "init", "--config", str(cfg)])
    proposal_path = tmp_path / "proposal.json"
    proposal_path.write_text(
        json.dumps(
            {
                "parameters": {
                    "MIN_PROB": 0.88,
                    "MIN_EDGE": 0.06,
                    "KELLY_FRACTION": 0.65,
                    "PERSISTENCE_THRESHOLD": 0.70,
                },
                "rationale": "cli test",
                "applied_by": "USER",
            }
        ),
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        main,
        ["strategy", "apply", str(proposal_path), "--config", str(cfg)],
    )
    assert result.exit_code == 0
    assert "OK: strategy version" in result.output


def test_strategy_apply_invalid_proposal(
    tmp_path: Path, strategy_config: StrategyConfig
) -> None:
    _ensure_dirs(tmp_path)
    cfg = write_isolated_config(tmp_path, strategy_config)
    CliRunner().invoke(main, ["db", "init", "--config", str(cfg)])
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"parameters": {}}), encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["strategy", "apply", str(bad), "--config", str(cfg)],
    )
    assert result.exit_code != 0


def test_cli_main_entrypoint() -> None:
    from yoruu.cli import main as cli_main

    assert cli_main is main
