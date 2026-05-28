"""Pydantic models for SSE payloads (ch10 §10.5.3 / mock-data.js SSE_PAYLOADS)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SseSeverity = Literal["INFO", "WARN", "ERROR", "CRITICAL"]


class StateChangedPayload(BaseModel):
    from_state: str = Field(alias="from")
    to_state: str = Field(alias="to")
    timestamp: str
    reason: str
    severity: SseSeverity = "INFO"

    model_config = {"populate_by_name": True}


class MarkovMatrixPayload(BaseModel):
    p_up_up: float
    p_up_down: float
    p_down_up: float
    p_down_down: float


class MarkovUpdatePayload(BaseModel):
    computed_at: str
    window_size: int
    matrix: MarkovMatrixPayload
    rolling_persistence: float
    last_direction: str
    threshold_met: bool
    wait_reason: str
    severity: SseSeverity = "INFO"


class HealthDegradedPayload(BaseModel):
    component: str
    reason: str
    retry_count: int
    timestamp: str
    severity: SseSeverity = "WARN"


class HealthRecoveredPayload(BaseModel):
    component: str
    reason: str
    recovery_duration_sec: int
    timestamp: str
    severity: SseSeverity = "INFO"


class PositionOpenedPayload(BaseModel):
    trade_id: int
    market: str
    side: str
    size_usd: float
    entry_price: float
    expires_at: str
    edge_at_entry: float
    persistence_at_entry: float
    severity: SseSeverity = "INFO"


class PositionClosedPayload(BaseModel):
    trade_id: int
    exit_price: float
    pnl: float
    win: bool
    closed_at: str
    severity: SseSeverity = "INFO"


class NightlyReportReadyPayload(BaseModel):
    report_date: str
    report_id: int
    summary_url: str
    severity: SseSeverity = "INFO"


class ModeChangedPayload(BaseModel):
    from_mode: str = Field(alias="from")
    to_mode: str = Field(alias="to")
    timestamp: str
    severity: SseSeverity = "INFO"

    model_config = {"populate_by_name": True}


class EmergencyStopTriggeredPayload(BaseModel):
    trigger: str
    timestamp: str
    open_positions_closed: int
    severity: SseSeverity = "CRITICAL"


class AlertAddedPayload(BaseModel):
    id: int
    code: str
    severity: SseSeverity
    message: str
    created_at: str


class StrategyAppliedPayload(BaseModel):
    new_version: int
    previous_version: int
    applied_by: str
    rationale: str
    applied_at: str
    diff: dict[str, list[float]]
    severity: SseSeverity = "INFO"


class PrincipalChangedPayload(BaseModel):
    kind: Literal["DEPOSIT", "WITHDRAW"]
    amount: float
    balance_before: float
    balance_after: float
    principal_before: float
    principal_after: float
    locked_principal: float
    withdrawable_principal: float
    total_assets: float
    cumulative_pnl: float
    ts_utc: str
    note: str | None = None
    severity: SseSeverity = "INFO"
