"""YoRuu CLI entry (PHASE 3)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import click

from yoruu.config.settings import AppSettings, load_settings
from yoruu.core.state_machine import StateMachine
from yoruu.data.database import Database
from yoruu.data.migrate import plan_migration, run_migration
from yoruu.errors import ConfigValidationError, PrincipalError, StrategyApplyError, YoRuuError
from yoruu.execution.fill_model import FillModel
from yoruu.execution.paper_executor import OpenRequest, PaperExecutor
from yoruu.execution.principal_service import PrincipalService
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
    click.echo(
        f"OK: mode={settings.mode.value} initial_principal={settings.resolved_initial_principal}"
    )


@main.command("db")
@click.argument("action", type=click.Choice(["init", "migrate"]))
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--dry-run", is_flag=True, help="Show migration steps without applying (migrate only)")
@click.option("--db", "db_path", type=click.Path(path_type=Path), default=None, help="Override paths.db")
def db_cmd(action: str, config_path: Path, dry_run: bool, db_path: Path | None) -> None:
    """Initialize or migrate SQLite schema."""

    settings = load_settings(config_path)
    target_db = db_path or Path(settings.paths.db)

    if action == "migrate":
        db = Database(target_db)
        if not target_db.is_file():
            click.echo(f"FAIL: database not found: {target_db}", err=True)
            sys.exit(1)
        plan = run_migration(
            db,
            initial_principal=settings.resolved_initial_principal,
            dry_run=dry_run,
        )
        if dry_run:
            click.echo("DRY-RUN migration plan:")
        else:
            click.echo("OK: migration applied:")
        click.echo(f"  add principal column: {plan.add_principal_column}")
        click.echo(f"  create principal_transactions: {plan.create_principal_transactions}")
        click.echo(f"  backfill rows: {plan.backfill_principal_rows}")
        click.echo(f"  seed migration tx: {plan.seed_migration_tx}")
        db.close()
        return

    strategy_path = Path(settings.paths.strategy)
    strategy = StrategyWriter(strategy_path).read()
    db = Database(target_db)
    db.initialize_schema()
    seed = settings.resolved_initial_principal
    db.ensure_bot_state(
        mode=settings.mode,
        balance=seed,
        principal=seed,
        daily_loss_limit=settings.risk.daily_loss_limit_usd,
        strategy_version=strategy.version,
    )
    db.ensure_strategy_version_seed(
        json.dumps(strategy.to_json_dict(), ensure_ascii=False),
        strategy_version=strategy.version,
    )
    invariants = InvariantChecker(db, initial_principal=seed)
    invariants.check_startup(strategy, strategy.version)
    sm = StateMachine(db, invariant_checker=invariants)
    if sm.current() == State.INITIALIZING:
        sm.transition(State.IDLE, "db init complete", actor="USER")
    db.close()
    click.echo(f"OK: database at {target_db}")


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
        balance=settings.resolved_initial_principal,
        daily_loss_limit=settings.risk.daily_loss_limit_usd,
        strategy_version=strategy.version,
    )
    db.ensure_strategy_version_seed(
        json.dumps(strategy.to_json_dict(), ensure_ascii=False),
        strategy_version=strategy.version,
    )
    invariants = InvariantChecker(db, initial_principal=settings.resolved_initial_principal)
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
    invariants = InvariantChecker(db, initial_principal=settings.resolved_initial_principal)
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
    invariants = InvariantChecker(db, initial_principal=settings.resolved_initial_principal)
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


def _principal_service_for_cli(settings: AppSettings, db: Database) -> PrincipalService:
    invariants = InvariantChecker(db, initial_principal=settings.resolved_initial_principal)
    return PrincipalService(
        db,
        max_deposit_per_tx=settings.principal.max_deposit_per_tx,
        max_withdraw_per_tx=settings.principal.max_withdraw_per_tx,
        require_confirm_on_withdraw=settings.principal.require_confirm_on_withdraw,
        invariant_checker=invariants,
    )


@main.group("principal")
def principal_group() -> None:
    """Principal deposit/withdraw (ch13 §13.2.6)."""


@principal_group.command("deposit")
@click.argument("amount", type=float)
@click.option("--note", default=None, help="Optional audit note")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
def principal_deposit_cmd(amount: float, note: str | None, config_path: Path) -> None:
    """Deposit principal (increases balance and principal)."""

    settings = load_settings(config_path)
    db = Database(settings.paths.db)
    db.initialize_schema()
    try:
        change = _principal_service_for_cli(settings, db).deposit(amount, note=note)
        click.echo(json.dumps(_principal_cli_payload(change), indent=2, ensure_ascii=False))
    except PrincipalError as exc:
        click.echo(json.dumps({"code": exc.code, "message": str(exc)}, indent=2), err=True)
        sys.exit(1)
    finally:
        db.close()


@principal_group.command("withdraw")
@click.argument("amount", type=float)
@click.option("--confirm", is_flag=True, default=False, help="Required when require_confirm_on_withdraw")
@click.option("--note", default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
def principal_withdraw_cmd(
    amount: float, confirm: bool, note: str | None, config_path: Path
) -> None:
    """Withdraw principal (decreases balance and principal)."""

    settings = load_settings(config_path)
    db = Database(settings.paths.db)
    db.initialize_schema()
    try:
        change = _principal_service_for_cli(settings, db).withdraw(
            amount, note=note, confirm=confirm
        )
        click.echo(json.dumps(_principal_cli_payload(change), indent=2, ensure_ascii=False))
    except PrincipalError as exc:
        click.echo(json.dumps({"code": exc.code, "message": str(exc)}, indent=2), err=True)
        sys.exit(1)
    finally:
        db.close()


@principal_group.command("show")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
def principal_show_cmd(config_path: Path) -> None:
    """Show principal summary."""

    settings = load_settings(config_path)
    db = Database(settings.paths.db)
    db.initialize_schema()
    try:
        detail = _principal_service_for_cli(settings, db).get_detail()
        click.echo(json.dumps(detail, indent=2, ensure_ascii=False))
    finally:
        db.close()


@principal_group.command("transactions")
@click.option("--limit", default=50, type=int)
@click.option("--kind", type=click.Choice(["DEPOSIT", "WITHDRAW"]), default=None)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
def principal_transactions_cmd(
    limit: int, kind: str | None, config_path: Path
) -> None:
    """List principal transactions."""

    settings = load_settings(config_path)
    db = Database(settings.paths.db)
    db.initialize_schema()
    try:
        items = db.list_principal_transactions(limit=limit, kind=kind)
        click.echo(json.dumps({"items": items, "limit": limit}, indent=2, ensure_ascii=False))
    finally:
        db.close()


def _principal_cli_payload(change) -> dict:
    summary = change.summary
    return {
        "kind": change.kind,
        "amount": change.amount,
        "principal": summary.principal,
        "balance": summary.balance,
        "total_assets": summary.total_assets,
        "cumulative_pnl": summary.cumulative_pnl,
        "ts_utc": change.ts_utc,
    }


@main.command("run")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--max-evaluations", type=int, default=None, help="Stop after N evaluation cycles")
@click.option("--deadline-sec", type=float, default=None, help="Stop after N seconds")
@click.option("--interval-sec", type=int, default=300, help="Evaluation interval (lab may shorten)")
@click.option("--lab-mock-feed", is_flag=True, help="Synthetic ticks without live WS")
def run_cmd(
    config_path: Path,
    max_evaluations: int | None,
    deadline_sec: float | None,
    interval_sec: int,
    lab_mock_feed: bool,
) -> None:
    """常駐評価ループ (PHASE 6 M6.1)."""

    import asyncio

    from yoruu.core.loop_runtime import build_trading_loop

    settings = load_settings(config_path)
    if settings.mode not in (Mode.PAPER, Mode.SIMMER):
        click.echo("mode must be PAPER or SIMMER; use yoruu backtest for BACKTEST", err=True)
        sys.exit(1)
    db = Database(settings.paths.db)
    db.initialize_schema()
    loop = build_trading_loop(settings, db, interval_sec=interval_sec)
    stats = asyncio.run(
        loop.run(
            max_evaluations=max_evaluations,
            deadline_sec=deadline_sec,
            lab_mock_feed=lab_mock_feed,
            connect_ws=not lab_mock_feed,
        )
    )
    db.close()
    click.echo(
        f"OK: evaluations={stats.evaluations} entries={stats.entries} "
        f"closes={stats.closes} skipped_stale={stats.skipped_stale}"
    )


@main.command("emergency-stop")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--confirm", is_flag=True, help="Required to trigger stop")
def emergency_stop_cmd(config_path: Path, confirm: bool) -> None:
    """Trigger emergency stop (ch19)."""

    from yoruu.core.loop_runtime import build_trading_loop

    if not confirm:
        click.echo("Refusing without --confirm", err=True)
        sys.exit(1)
    settings = load_settings(config_path)
    db = Database(settings.paths.db)
    db.initialize_schema()
    loop = build_trading_loop(settings, db)
    assert loop.emergency_controller is not None
    result = loop.emergency_controller.trigger(source="USER", detail="cli_confirm")
    db.close()
    click.echo(
        f"OK: state={result.state.value} closed={result.open_closed} "
        f"partial={result.partial}"
    )


@main.group("backtest")
def backtest_group() -> None:
    """Historical strategy replay (PHASE 6 M6.3)."""


@backtest_group.command("run")
@click.option("--start", required=True, help="YYYY-MM-DD")
@click.option("--end", required=True, help="YYYY-MM-DD")
@click.option("--seed", type=int, default=42)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--out", "out_mode", type=click.Choice(["json", "db"]), default="json")
def backtest_run_cmd(
    start: str,
    end: str,
    seed: int,
    config_path: Path,
    out_mode: str,
) -> None:
    """Run backtest over historical bars."""

    from yoruu.execution.backtest_executor import BacktestExecutor
    from yoruu.infra.historical_loader import HistoricalLoader
    from yoruu.strategy.evaluator import StrategyEvaluator
    from yoruu.strategy.markov import MarkovEngine

    settings = load_settings(config_path)
    strategy = StrategyWriter(Path(settings.paths.strategy)).read()
    db = Database(settings.paths.db)
    db.initialize_schema()
    loader = HistoricalLoader(db, historical_dir=Path(settings.paths.historical))
    markov = MarkovEngine(window_size=MARKOV_WINDOW)
    evaluator = StrategyEvaluator(markov, strategy)
    executor = BacktestExecutor(
        loader,
        FillModel(settings.paper, seed=seed),
        markov,
        evaluator,
        max_trade_size_usd=settings.risk.max_trade_size_usd,
        initial_balance=settings.resolved_initial_principal,
        spread_assumed=settings.paper.spread_assumed,
    )
    result = executor.run(start=start, end=end, rng_seed=seed)
    payload = executor.result_to_json(result)
    click.echo(payload)
    if out_mode == "db":
        run_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        db.insert_what_if_scenario(
            name=f"backtest_{run_id}",
            period_from=start,
            period_to=end,
            parameters_json=json.dumps(result.params),
            result_json=payload,
            created_by="CLI",
        )
        db.commit()
    db.close()


@main.command("serve")
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8765, type=int)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--no-loop", is_flag=True, help="API only, no background TradingLoop")
def serve_cmd(host: str, port: int, config_path: Path, no_loop: bool) -> None:
    """Run FastAPI server with optional TradingLoop (ch10 §10.6)."""

    import uvicorn

    del config_path
    if no_loop:
        from yoruu.web.app import create_app

        uvicorn.run(create_app(with_trading_loop=False), host=host, port=port, reload=False)
    else:
        uvicorn.run("yoruu.web.app:app", host=host, port=port, reload=False)


@main.group("market")
def market_group() -> None:
    """Market data WebSocket feeds."""


@market_group.command("run")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--duration-sec", type=float, default=None, help="Stop after N seconds (lab)")
def market_run_cmd(config_path: Path, duration_sec: float | None) -> None:
    """Run Polymarket + Binance WS feeds."""

    import asyncio

    from yoruu.infra.market_runner import run_market_feeds

    settings = load_settings(config_path)
    db = Database(settings.paths.db)
    db.initialize_schema()
    db.ensure_bot_state(
        mode=settings.mode,
        balance=settings.resolved_initial_principal,
        daily_loss_limit=settings.risk.daily_loss_limit_usd,
        strategy_version=1,
    )
    asyncio.run(run_market_feeds(settings, db, duration_sec=duration_sec))
    click.echo("OK: market feeds stopped")


@main.command("paper-24h")
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=_default_config)
@click.option("--hours", type=float, default=24.0)
@click.option("--interval-sec", type=int, default=300)
@click.option("--max-cycles", type=int, default=None, help="Stop after N cycles (lab smoke)")
def paper_24h_cmd(
    config_path: Path,
    hours: float,
    interval_sec: int,
    max_cycles: int | None,
) -> None:
    """Paper evaluate loop for N hours (lab harness)."""

    import subprocess

    deadline = __import__("time").time() + hours * 3600.0
    cycles = 0
    while __import__("time").time() < deadline:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "yoruu.cli",
                "paper",
                "evaluate-once",
                "--config",
                str(config_path),
            ],
            check=False,
        )
        if proc.returncode != 0:
            sys.exit(proc.returncode)
        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            break
        if __import__("time").time() >= deadline:
            break
        __import__("time").sleep(interval_sec)
    click.echo(f"OK: {cycles} paper cycles")


if __name__ == "__main__":
    main()
