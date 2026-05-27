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
from yoruu.errors import ConfigValidationError, StrategyApplyError, YoRuuError
from yoruu.execution.fill_model import FillModel
from yoruu.execution.paper_executor import OpenRequest, PaperExecutor
from yoruu.execution.risk_guard import RiskGuard
from yoruu.infra.mock_market import MockMarketProvider
from yoruu.review.nightly_reporter import NightlyReporter
from yoruu.review.strategy_applier import StrategyApplier
from yoruu.review.strategy_writer import StrategyWriter
from yoruu.safety.invariants import InvariantChecker
from yoruu.strategy.evaluator import StrategyEvaluator
from yoruu.strategy.markov import MarkovEngine
from yoruu.types import Mode, State

MARKOV_WINDOW = 20


def _default_config() -> Path:
    return Path("config/yoruu.yaml")


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
    db.ensure_strategy_version_seed(
        json.dumps(strategy.to_json_dict(), ensure_ascii=False),
        strategy_version=strategy.version,
    )
    invariants = InvariantChecker(db, initial_balance=settings.initial_balance)
    invariants.check_startup(strategy, strategy.version)
    sm = StateMachine(db, invariant_checker=invariants)
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
    db.ensure_strategy_version_seed(
        json.dumps(strategy.to_json_dict(), ensure_ascii=False),
        strategy_version=strategy.version,
    )
    invariants = InvariantChecker(db, initial_balance=settings.initial_balance)
    invariants.check_startup(strategy, strategy.version)
    sm = StateMachine(db, invariant_checker=invariants)
    if sm.current() == State.INITIALIZING:
        sm.transition(State.IDLE, "paper evaluate bootstrap")

    markov = MarkovEngine(window_size=MARKOV_WINDOW)
    market = MockMarketProvider()
    price = 100.0
    for _ in range(22):
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

    risk = RiskGuard(settings.risk, db)
    evaluator = StrategyEvaluator(markov, strategy)
    mstate = market.market_state(yes_ask=0.81)
    result = evaluator.evaluate(
        mstate,
        balance=db.get_balance(),
        max_trade_size_usd=settings.risk.max_trade_size_usd,
        snapshot=snap,
        risk_guard=risk,
    )
    click.echo(json.dumps(result.__dict__, default=str, indent=2))

    if result.should_enter and result.side is not None:
        sm.transition(State.TRADING, "paper evaluate-once")
        executor = PaperExecutor(
            db,
            FillModel(settings.paper, seed=42),
            invariant_checker=invariants,
            max_trade_size_usd=settings.risk.max_trade_size_usd,
            daily_loss_limit=settings.risk.daily_loss_limit_usd,
        )
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
    invariants = InvariantChecker(db, initial_balance=settings.initial_balance)
    sm = StateMachine(db, invariant_checker=invariants)
    try:
        if sm.current() == State.IDLE:
            sm.transition(State.NIGHTLY_REVIEW, "nightly generate", actor="NIGHTLY_REVIEW")
        reporter = NightlyReporter(db)
        summary = reporter.generate(report_date, strategy)
        path = reporter.write_report_file(report_date, summary, settings.paths.reports)
        sm.transition(State.IDLE, "nightly generate complete", actor="NIGHTLY_REVIEW")
        click.echo(f"OK: {path}")
    except Exception as exc:
        db.insert_audit(
            actor="NIGHTLY_REVIEW",
            action="NIGHTLY_GENERATE",
            resource="daily_reports",
            resource_id=report_date,
            details={"error": str(exc)},
            result="FAILURE",
        )
        db.commit()
        if sm.current() == State.NIGHTLY_REVIEW:
            sm.transition(State.IDLE, "nightly generate failed", actor="NIGHTLY_REVIEW")
        click.echo(f"FAIL: {exc}", err=True)
        sys.exit(1)
    finally:
        db.close()


@main.command("strategy")
@click.argument("action", type=click.Choice(["apply"]))
@click.argument("proposal_file", type=click.Path(path_type=Path, exists=True))
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--by", "applied_by", default="USER")
@click.option("--report-date", default=None, help="daily_reports.report_date for linkage")
def strategy_cmd(
    action: str,
    proposal_file: Path,
    config_path: Path,
    applied_by: str,
    report_date: str | None,
) -> None:
    """Apply validated strategy proposal JSON."""

    settings = load_settings(config_path)
    writer = StrategyWriter(Path(settings.paths.strategy))
    current = writer.read()
    proposal = json.loads(proposal_file.read_text(encoding="utf-8"))
    if "applied_by" not in proposal:
        proposal["applied_by"] = applied_by

    db = Database(settings.paths.db)
    db.initialize_schema()
    invariants = InvariantChecker(db, initial_balance=settings.initial_balance)
    sm = StateMachine(db, invariant_checker=invariants)

    try:
        applier = StrategyApplier(
            db,
            writer,
            history_dir=Path(settings.paths.strategy).parent / "strategy_history",
        )
        result = applier.apply(
            proposal,
            current,
            state_machine=sm,
            report_date=report_date,
        )
        click.echo(f"OK: strategy version {result.new_version}")
    except StrategyApplyError as exc:
        click.echo(json.dumps({"code": exc.code, "message": str(exc)}, indent=2), err=True)
        sys.exit(1)
    except YoRuuError as exc:
        click.echo(json.dumps({"code": exc.code, "message": str(exc)}, indent=2), err=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
