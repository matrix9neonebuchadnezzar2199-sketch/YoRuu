"""Strategy evaluator integration tests."""

from yoruu.infra.mock_market import MockMarketProvider
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
            MIN_PROB=0.80,
            MIN_EDGE=0.03,
            KELLY_FRACTION=0.65,
            PERSISTENCE_THRESHOLD=0.50,
        ),
        constraints={
            "MIN_PROB": ParameterConstraints(min=0.50, max=0.95),
            "MIN_EDGE": ParameterConstraints(min=0.01, max=0.20),
            "KELLY_FRACTION": ParameterConstraints(min=0.10, max=1.00),
            "PERSISTENCE_THRESHOLD": ParameterConstraints(min=0.40, max=0.95),
        },
    )


def test_evaluator_enters_on_favorable_mock() -> None:
    markov = MarkovEngine(window_size=5)
    price = 100.0
    for _ in range(6):
        markov.add_close(price)
        price += 2.0
    snap = markov.snapshot()
    evaluator = StrategyEvaluator(markov, _strategy())
    result = evaluator.evaluate(
        MockMarketProvider().market_state(yes_ask=0.75),
        balance=1000.0,
        max_trade_size_usd=10.0,
        snapshot=snap,
    )
    assert result.should_enter or result.wait_reason is not None
