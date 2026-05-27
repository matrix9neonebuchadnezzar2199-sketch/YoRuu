"""Apply validator tests (ch15)."""

import pytest

from yoruu.errors import StrategyApplyError
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


def _valid_proposal(**overrides: object) -> dict:
    base = {
        "parameters": {
            "MIN_PROB": 0.87,
            "MIN_EDGE": 0.06,
            "KELLY_FRACTION": 0.65,
            "PERSISTENCE_THRESHOLD": 0.70,
        },
        "rationale": "テスト用の変更理由です。",
        "applied_by": "USER",
    }
    base.update(overrides)
    return base


def test_apply_rejects_large_change() -> None:
    validator = ApplyValidator()
    current = _sample_strategy()
    proposal = _valid_proposal(
        parameters={
            "MIN_PROB": 0.50,
            "MIN_EDGE": 0.06,
            "KELLY_FRACTION": 0.65,
            "PERSISTENCE_THRESHOLD": 0.70,
        }
    )
    result = validator.validate(proposal, current)
    assert not result.valid
    assert any("E_NIGHTLY_008" in e for e in result.errors)


def test_apply_requires_rationale() -> None:
    validator = ApplyValidator()
    proposal = _valid_proposal()
    del proposal["rationale"]
    result = validator.validate(proposal, _sample_strategy())
    assert not result.valid
    assert any("E_NIGHTLY_009" in e for e in result.errors)


def test_apply_constraints_forbidden_uses_e_nightly_005() -> None:
    validator = ApplyValidator()
    proposal = _valid_proposal(constraints={"MIN_PROB": {"min": 0.1, "max": 0.9}})
    result = validator.validate(proposal, _sample_strategy())
    assert not result.valid
    assert any("E_NIGHTLY_005" in e for e in result.errors)


def test_apply_warns_on_10_percent_change() -> None:
    validator = ApplyValidator()
    proposal = _valid_proposal(
        parameters={
            "MIN_PROB": 0.87,
            "MIN_EDGE": 0.06,
            "KELLY_FRACTION": 0.72,
            "PERSISTENCE_THRESHOLD": 0.70,
        }
    )
    result = validator.validate(proposal, _sample_strategy())
    assert result.valid
    assert any("E_NIGHTLY_008" in w for w in result.warnings)


def test_validate_or_raise() -> None:
    validator = ApplyValidator()
    with pytest.raises(StrategyApplyError):
        validator.validate_or_raise(
            _valid_proposal(
                parameters={
                    "MIN_PROB": 0.50,
                    "MIN_EDGE": 0.06,
                    "KELLY_FRACTION": 0.65,
                    "PERSISTENCE_THRESHOLD": 0.70,
                }
            ),
            _sample_strategy(),
        )
