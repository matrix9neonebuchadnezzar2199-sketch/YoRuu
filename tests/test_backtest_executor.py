"""BacktestExecutor (PHASE 6 M6.3)."""

from __future__ import annotations

from pathlib import Path

from yoruu.config.settings import PaperSettings
from yoruu.execution.backtest_executor import BacktestExecutor
from yoruu.execution.fill_model import FillModel
from yoruu.infra.historical_loader import HistoricalLoader
from yoruu.strategy.evaluator import StrategyEvaluator
from yoruu.strategy.markov import MarkovEngine
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)


def _strategy() -> StrategyConfig:
    return StrategyConfig(
        version=1,
        parameters=StrategyParameters(
            MIN_PROB=0.55,
            MIN_EDGE=0.03,
            KELLY_FRACTION=0.65,
            PERSISTENCE_THRESHOLD=0.70,
        ),
        constraints={
            "MIN_PROB": ParameterConstraints(min=0.5, max=0.95),
            "MIN_EDGE": ParameterConstraints(min=0.01, max=0.15),
            "KELLY_FRACTION": ParameterConstraints(min=0.10, max=1.00),
            "PERSISTENCE_THRESHOLD": ParameterConstraints(min=0.50, max=0.90),
        },
    )


def test_backtest_deterministic(tmp_path: Path) -> None:
    loader = HistoricalLoader(None)
    markov = MarkovEngine(window_size=20)
    strategy = _strategy()
    evaluator = StrategyEvaluator(markov, strategy)
    fill = FillModel(PaperSettings(), seed=42)
    bt = BacktestExecutor(
        loader,
        fill,
        markov,
        evaluator,
        max_trade_size_usd=10.0,
        initial_balance=1000.0,
    )
    r1 = bt.run(start="2026-05-01", end="2026-05-03", rng_seed=42)
    markov2 = MarkovEngine(window_size=20)
    evaluator2 = StrategyEvaluator(markov2, strategy)
    bt2 = BacktestExecutor(
        loader,
        FillModel(PaperSettings(), seed=42),
        markov2,
        evaluator2,
        max_trade_size_usd=10.0,
        initial_balance=1000.0,
    )
    r2 = bt2.run(start="2026-05-01", end="2026-05-03", rng_seed=42)
    assert r1.trades == r2.trades
    assert r1.pnl_total == r2.pnl_total
    assert r1.max_drawdown == r2.max_drawdown
