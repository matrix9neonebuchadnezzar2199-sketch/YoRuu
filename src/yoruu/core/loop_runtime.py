"""TradingLoop ファクトリ (CLI / serve 共有, PHASE 6)."""

from __future__ import annotations

from pathlib import Path

from yoruu.config.settings import AppSettings
from yoruu.core.clock import Clock
from yoruu.core.state_machine import StateMachine
from yoruu.core.trading_loop import TradingLoop
from yoruu.data.database import Database
from yoruu.execution.fill_model import FillModel
from yoruu.execution.paper_executor import PaperExecutor
from yoruu.execution.risk_guard import RiskGuard
from yoruu.infra.ohlc_provider import OhlcProvider
from yoruu.review.strategy_writer import StrategyWriter
from yoruu.safety.emergency_stop import EmergencyStopController
from yoruu.safety.invariants import InvariantChecker
from yoruu.strategy.evaluator import StrategyEvaluator
from yoruu.strategy.markov import MarkovEngine
from yoruu.types import State

MARKOV_WINDOW = 20


def bootstrap_db(settings: AppSettings, db: Database) -> tuple[StateMachine, InvariantChecker, StrategyWriter]:
    """Ensure bot_state and run startup invariants."""

    strategy_path = Path(settings.paths.strategy)
    writer = StrategyWriter(strategy_path)
    strategy = writer.read()
    db.ensure_bot_state(
        mode=settings.mode,
        balance=settings.resolved_initial_principal,
        principal=settings.resolved_initial_principal,
        daily_loss_limit=settings.risk.daily_loss_limit_usd,
        strategy_version=strategy.version,
    )
    invariants = InvariantChecker(db, initial_principal=settings.resolved_initial_principal)
    invariants.check_startup(strategy, strategy.version)
    sm = StateMachine(db, invariant_checker=invariants)
    if sm.current() == State.INITIALIZING:
        sm.transition(State.IDLE, "loop bootstrap")
    return sm, invariants, writer


def build_trading_loop(
    settings: AppSettings,
    db: Database,
    *,
    ohlc: OhlcProvider | None = None,
    clock: Clock | None = None,
    interval_sec: int = 300,
    event_bus=None,
) -> TradingLoop:
    """Wire Markov, evaluator, executor, emergency for ``run`` / ``serve``."""

    sm, invariants, writer = bootstrap_db(settings, db)
    strategy = writer.read()
    markov = MarkovEngine(window_size=MARKOV_WINDOW)
    evaluator = StrategyEvaluator(markov, strategy)
    executor = PaperExecutor(
        db,
        FillModel(settings.paper, seed=42),
        invariant_checker=invariants,
        max_trade_size_usd=settings.risk.max_trade_size_usd,
        daily_loss_limit=settings.risk.daily_loss_limit_usd,
    )
    risk = RiskGuard(settings.risk, db)
    loop = TradingLoop(
        settings,
        db,
        markov=markov,
        evaluator=evaluator,
        executor=executor,
        state_machine=sm,
        risk_guard=risk,
        invariants=invariants,
        ohlc=ohlc,
        clock=clock,
        interval_sec=interval_sec,
    )
    emergency = EmergencyStopController(
        db,
        sm,
        executor,
        event_bus=event_bus,
        trading_loop=loop,
    )
    loop._emergency = emergency  # noqa: SLF001
    return loop
