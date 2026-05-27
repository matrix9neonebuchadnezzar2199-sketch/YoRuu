"""Strategy apply validation (ch15 §15.6 / §15.7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yoruu.errors import StrategyApplyError
from yoruu.strategy.models import StrategyConfig, StrategyParameters

ALLOWED_KEYS = frozenset(
    {"MIN_PROB", "MIN_EDGE", "KELLY_FRACTION", "PERSISTENCE_THRESHOLD"}
)
FORBIDDEN_CONSTRAINT_KEYS = frozenset({"constraints"})
FORBIDDEN_TOP = frozenset({"mode", "risk", "websocket", "daily_loss_limit_usd"})
SILENT_IGNORE_KEYS = frozenset({"version", "metadata"})


@dataclass
class ApplyValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    normalized_parameters: dict[str, float] | None = None
    rationale: str | None = None
    source_report_id: int | None = None
    applied_by: str = "USER"


class ApplyValidator:
    """Validate Opus proposal JSON before apply."""

    def validate(
        self,
        proposal: dict[str, Any],
        current: StrategyConfig,
    ) -> ApplyValidationResult:
        result = ApplyValidationResult(valid=True)

        rationale = proposal.get("rationale")
        if not isinstance(rationale, str) or not (1 <= len(rationale) <= 500):
            result.valid = False
            result.errors.append("E_NIGHTLY_009:invalid rationale (1-500 chars required)")
            return result
        result.rationale = rationale

        if "applied_by" in proposal and isinstance(proposal["applied_by"], str):
            result.applied_by = proposal["applied_by"]

        source_id = proposal.get("source_report_id")
        if source_id is not None:
            if not isinstance(source_id, int):
                result.valid = False
                result.errors.append("E_NIGHTLY_009:invalid source_report_id")
                return result
            result.source_report_id = source_id

        for key in proposal:
            if key in SILENT_IGNORE_KEYS or key in (
                "parameters",
                "rationale",
                "applied_by",
                "source_report_id",
            ):
                continue
            if key in FORBIDDEN_CONSTRAINT_KEYS or key.startswith("constraints"):
                result.valid = False
                result.errors.append(f"E_NIGHTLY_005:forbidden key {key}")
            elif key in FORBIDDEN_TOP or key.startswith("risk.") or key.startswith("websocket."):
                result.valid = False
                result.errors.append(f"E_NIGHTLY_006:forbidden key {key}")

        params = proposal.get("parameters")
        if not isinstance(params, dict):
            result.valid = False
            result.errors.append("E_NIGHTLY_009:missing parameters")
            return result

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
                    result.warnings.append(f"E_NIGHTLY_008:{key} change > 10%")

        result.normalized_parameters = normalized if result.valid else None
        return result

    def validate_or_raise(
        self,
        proposal: dict[str, Any],
        current: StrategyConfig,
    ) -> ApplyValidationResult:
        """Validate and raise StrategyApplyError on failure."""

        result = self.validate(proposal, current)
        if not result.valid:
            code = result.errors[0].split(":", 1)[0] if result.errors else "E_NIGHTLY_007"
            raise StrategyApplyError(
                "; ".join(result.errors),
                code=code,
                details={"errors": result.errors},
            )
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
