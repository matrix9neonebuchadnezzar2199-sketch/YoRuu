"""Strategy apply validation (ch15 §15.7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yoruu.strategy.models import StrategyConfig, StrategyParameters

ALLOWED_KEYS = frozenset(
    {"MIN_PROB", "MIN_EDGE", "KELLY_FRACTION", "PERSISTENCE_THRESHOLD"}
)
FORBIDDEN_TOP = frozenset({"constraints", "mode", "risk", "websocket", "daily_loss_limit_usd"})


@dataclass
class ApplyValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    normalized_parameters: dict[str, float] | None = None


class ApplyValidator:
    """Validate Opus proposal JSON before apply."""

    def validate(
        self,
        proposal: dict[str, Any],
        current: StrategyConfig,
    ) -> ApplyValidationResult:
        result = ApplyValidationResult(valid=True)
        params = proposal.get("parameters")
        if not isinstance(params, dict):
            result.valid = False
            result.errors.append("E_NIGHTLY_009:missing parameters")
            return result

        for key in proposal:
            if key in FORBIDDEN_TOP:
                result.valid = False
                result.errors.append(f"E_NIGHTLY_006:forbidden key {key}")

        for key in params:
            if key not in ALLOWED_KEYS:
                result.valid = False
                result.errors.append(f"E_NIGHTLY_006:unknown parameter {key}")

        for key in ALLOWED_KEYS:
            if key not in params:
                result.valid = False
                result.errors.append(f"E_NIGHTLY_009:missing {key}")

        if not result.valid:
            return result

        normalized: dict[str, float] = {}
        current_params = current.parameters.model_dump()
        for key in ALLOWED_KEYS:
            value = float(params[key])
            normalized[key] = value
            constraint = current.constraints.get(key)
            if constraint and not constraint.min <= value <= constraint.max:
                result.valid = False
                result.errors.append(f"E_NIGHTLY_007:{key} out of range")
            old = current_params[key]
            if old != 0:
                change_pct = abs(value - old) / old
                if change_pct > 0.20:
                    result.valid = False
                    result.errors.append(f"E_NIGHTLY_008:{key} change > 20%")
                elif change_pct > 0.10:
                    result.warnings.append(f"{key} change > 10%")

        result.normalized_parameters = normalized if result.valid else None
        return result

    def build_strategy_config(
        self,
        current: StrategyConfig,
        normalized_parameters: dict[str, float],
        *,
        applied_by: str,
    ) -> StrategyConfig:
        """Produce next strategy.json content."""

        new_version = current.version + 1
        return StrategyConfig(
            version=new_version,
            parameters=StrategyParameters(**normalized_parameters),
            constraints=current.constraints,
            metadata=current.metadata.model_copy(
                update={
                    "previous_version": current.version,
                    "applied_by": applied_by,
                }
            ),
        )
