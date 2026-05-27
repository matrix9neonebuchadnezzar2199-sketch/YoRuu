"""YoRuu CLI entry (PHASE 3)."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import click

from yoruu.config.settings import load_settings
from yoruu.core.state_machine import StateMachine
from yoruu.data.database import Database
from yoruu.errors import ConfigValidationError, YoRuuError
from yoruu.execution.fill_model import FillModel
from yoruu.execution.paper_executor import OpenRequest, PaperExecutor
from yoruu.execution.risk_guard import RiskGuard
from yoruu.infra.mock_market import MockMarketProvider
from yoruu.review.apply_validator import ApplyValidator
from yoruu.review.nightly_reporter import NightlyReporter
from yoruu.review.strategy_writer import StrategyWriter
from yoruu.strategy.evaluator import StrategyEvaluator
from yoruu.strategy.markov import MarkovEngine
from yoruu.types import Mode, State, TradeSignal


def _default_config() -> Path:
    return Path("config/yoruu.yaml")


def _default_strategy() -> Path:
    return Path("config/strategy.json")


@click.group()
@click.version_option(package_name="yoruu")
def main() -> None:
    """YoRuu core CLI (paper-first, no Web UI)."""


@main.command("config")
@click.argument("action", type=click.Choice(["validate"]))
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
def config_cmd(action: str, config_path: Path) -> None:
    """Validate yoruu.yaml."""

    try:
        settings = load_settings(config_path)
    except ConfigValidationError as exc:
        click.echo(f"FAIL: {exc}", err=True)
        sys.exit(1)
    click.echo(f"OK: mode={settings.mode.value} balance={settings.initial_balance}")


@main.command("db")
@click.argument("action", type=click.Choice(["init"]))
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
def db_cmd(action: str, config_path: Path) -> None:
    """Initialize SQLite schema and bot_state."""

    settings = load_settings(config_path)
    strategy_path = Path(settings.paths.strategy)
    strategy = StrategyWriter(strategy_path).read()
    db = Database(settings.paths.db)
    db.initialize_schema()
    db.ensure_bot_state(
        mode=settings.mode,
        balance=settings.initial_balance,
        daily_loss_limit=settings.risk.daily_loss_limit_usd,
        strategy_version=strategy.version,
    )
    sm = StateMachine(db)
    if sm.current() == State.INITIALIZING:
        sm.transition(State.IDLE, "db init complete", actor="USER")
    db.close()
    click.echo(f"OK: database at {settings.paths.db}")


@main.command("paper")
@click.argument("action", type=click.Choice(["evaluate-once"]))
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
def paper_cmd(action: str, config_path: Path) -> None:
    """Run one paper evaluation cycle (mock market)."""

    settings = load_settings(config_path)
    if settings.mode not in (Mode.PAPER, Mode.SIMMER):
        click.echo("mode must be PAPER or SIMMER", err=True)
        sys.exit(1)

    strategy_path = Path(settings.paths.strategy)
    strategy = StrategyWriter(strategy_path).read()
    db = Database(settings.paths.db)
    db.initialize_schema()
    db.ensure_bot_state(
        mode=settings.mode,
        balance=settings.initial_balance,
        daily_loss_limit=settings.risk.daily_loss_limit_usd,
        strategy_version=strategy.version,
    )
    sm = StateMachine(db)
    if sm.current() == State.INITIALIZING:
        sm.transition(State.IDLE, "paper evaluate bootstrap")

    markov = MarkovEngine(window_size=20)
    market = MockMarketProvider()
    # 上昇クローズを投入して persistence を満たしやすくする
    price = 100.0
    for i in range(22):
        markov.add_close(price)
        price += 1.0

    snap = markov.snapshot()
    db.insert_markov_snapshot(
        computed_at=snap.computed_at_iso,
        window_size=snap.window_size,
        matrix={
            "p_up_up": snap.matrix.p_up_up,
            "p_up_down": snap.matrix.p_up_down,
            "p_down_up": snap.matrix.p_down_up,
            "p_down_down": snap.matrix.p_down_down,
        },
        persistence=snap.rolling_persistence,
        last_direction=snap.last_direction.value if snap.last_direction else None,
    )

    evaluator = StrategyEvaluator(markov, strategy)
    mstate = market.market_state(yes_ask=0.81)
    result = evaluator.evaluate(
        mstate,
        balance=db.get_balance(),
        max_trade_size_usd=settings.risk.max_trade_size_usd,
        snapshot=snap,
    )
    click.echo(json.dumps(result.__dict__, default=str, indent=2))

    risk = RiskGuard(settings.risk, db)
    if result.should_enter and result.side is not None:
        signal = TradeSignal(
            side=result.side,
            size_usd=result.size_usd,
            edge=result.edge,
            persistence=result.persistence,
            predicted_prob=result.predicted_prob,
            market_price=result.market_price,
        )
        check = risk.check_pre_trade(signal)
        if not check.ok:
            click.echo(f"Risk blocked: {check.reason}")
            db.close()
            return
        sm.transition(State.TRADING, "paper evaluate-once")
        executor = PaperExecutor(db, FillModel(settings.paper, seed=42))
        fill = executor.open(
            OpenRequest(
                market=settings.market.id,
                side=result.side,
                size_usd=result.size_usd,
                expected_price=result.market_price,
                book=mstate.order_book_yes,
                mode=settings.mode,
                strategy_version=strategy.version,
                edge=result.edge,
                persistence=result.persistence,
            )
        )
        sm.transition(State.MONITORING_POSITION, "order placed")
        click.echo(f"Fill: success={fill.success} trade_id={fill.trade_id}")
    db.close()


@main.command("nightly")
@click.argument("action", type=click.Choice(["generate"]))
@click.option("--date", "report_date", default=lambda: date.today().isoformat())
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
def nightly_cmd(action: str, report_date: str, config_path: Path) -> None:
    """Generate nightly summary JSON."""

    settings = load_settings(config_path)
    strategy = StrategyWriter(Path(settings.paths.strategy)).read()
    db = Database(settings.paths.db)
    db.initialize_schema()
    reporter = NightlyReporter(db)
    summary = reporter.generate(report_date, strategy)
    path = reporter.write_report_file(report_date, summary, settings.paths.reports)
    db.close()
    click.echo(f"OK: {path}")


@main.command("strategy")
@click.argument("action", type=click.Choice(["apply"]))
@click.argument("proposal_file", type=click.Path(path_type=Path, exists=True))
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--by", "applied_by", default="USER")
def strategy_cmd(action: str, proposal_file: Path, config_path: Path, applied_by: str) -> None:
    """Apply validated strategy proposal JSON."""

    settings = load_settings(config_path)
    writer = StrategyWriter(Path(settings.paths.strategy))
    current = writer.read()
    proposal = json.loads(proposal_file.read_text(encoding="utf-8"))
    validator = ApplyValidator()
    validation = validator.validate(proposal, current)
    if not validation.valid:
        click.echo(json.dumps({"errors": validation.errors}, indent=2), err=True)
        sys.exit(1)

    assert validation.normalized_parameters is not None
    new_config = validator.build_strategy_config(
        current,
        validation.normalized_parameters,
        applied_by=applied_by,
    )
    db = Database(settings.paths.db)
    db.initialize_schema()
    with db.transaction():
        db.insert_strategy_version(
            json.dumps(new_config.to_json_dict(), ensure_ascii=False),
            applied_by=applied_by,
        )
        db.insert_audit(
            actor=applied_by,
            action="STRATEGY_APPLY",
            resource="strategy",
            resource_id=str(new_config.version),
            details={"diff": validation.normalized_parameters},
            result="SUCCESS",
        )
    writer.apply(new_config)
    db.close()
    click.echo(f"OK: strategy version {new_config.version}")


if __name__ == "__main__":
    main()
