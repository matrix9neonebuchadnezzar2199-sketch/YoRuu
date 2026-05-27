"""Apply validator tests (ch15)."""

from yoruu.review.apply_validator import ApplyValidator
from yoruu.strategy.models import (
    ParameterConstraints,
    StrategyConfig,
    StrategyParameters,
)


def _sample_strategy() -> StrategyConfig:
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


def test_apply_rejects_large_change() -> None:
    validator = ApplyValidator()
    current = _sample_strategy()
    proposal = {
        "parameters": {
            "MIN_PROB": 0.50,
            "MIN_EDGE": 0.06,
            "KELLY_FRACTION": 0.65,
            "PERSISTENCE_THRESHOLD": 0.70,
        }
    }
    result = validator.validate(proposal, current)
    assert not result.valid
    assert any("E_NIGHTLY_008" in e for e in result.errors)
