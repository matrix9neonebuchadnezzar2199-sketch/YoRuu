"""strategy.json models (ch10 §10.4.1)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ParameterConstraints(BaseModel):
    min: float
    max: float
    default: float | None = None


class StrategyParameters(BaseModel):
    MIN_PROB: float
    MIN_EDGE: float
    KELLY_FRACTION: float
    PERSISTENCE_THRESHOLD: float


class StrategyMetadata(BaseModel):
    applied_at: str | None = None
    applied_by: str | None = None
    previous_version: int | None = None


class StrategyConfig(BaseModel):
    version: int
    parameters: StrategyParameters
    constraints: dict[str, ParameterConstraints] = Field(default_factory=dict)
    metadata: StrategyMetadata = Field(default_factory=StrategyMetadata)

    @classmethod
    def from_json_dict(cls, data: dict[str, Any]) -> StrategyConfig:
        return cls.model_validate(data)

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def validate_parameters_in_constraints(self) -> list[str]:
        """Return list of keys out of range."""

        errors: list[str] = []
        params = self.parameters.model_dump()
        for key, value in params.items():
            constraint = self.constraints.get(key)
            if constraint is None:
                continue
            if not constraint.min <= value <= constraint.max:
                errors.append(key)
        return errors
