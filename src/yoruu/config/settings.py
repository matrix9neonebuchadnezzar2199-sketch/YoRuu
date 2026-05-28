"""yoruu.yaml loader (ch22 SSOT)."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from yoruu.errors import ConfigValidationError
from yoruu.types import Mode


class RiskSettings(BaseModel):
    max_trade_size_usd: float = Field(gt=0)
    daily_loss_limit_usd: float = Field(gt=0)
    emergency_stop_enabled: bool = True
    consecutive_fail_limit: int = 3
    consecutive_fail_window_min: int = 15


class WebSocketSettings(BaseModel):
    polymarket_url: str
    binance_url: str
    reconnect_interval_sec: int = 5
    max_reconnect_attempts: int = 10
    stale_tick_sec: int = 30


class NightlyReviewSettings(BaseModel):
    enabled: bool = True
    send_time: str = "04:00"
    timezone: str = "Asia/Tokyo"
    pause_trading_during_review: bool = True


class PathsSettings(BaseModel):
    db: str = "data/yoruu.db"
    strategy: str = "config/strategy.json"
    logs: str = "logs/"
    historical: str = "data/historical/"
    reports: str = "reports/"


class PaperSettings(BaseModel):
    spread_assumed: float = 0.02
    slippage_coeff: float = 0.0001
    slippage_max: float = 0.02
    latency_ms_mean: int = 80
    latency_ms_std: int = 20


class PrincipalSettings(BaseModel):
    max_deposit_per_tx: float = Field(gt=0, default=100_000.0)
    max_withdraw_per_tx: float = Field(gt=0, default=100_000.0)
    require_confirm_on_withdraw: bool = True


class DisplayFxSettings(BaseModel):
    enabled: bool = True
    provider: str = "exchangerate_host"
    cache_ttl_sec: int = Field(gt=0, default=900)
    stale_after_sec: int = Field(gt=0, default=1800)
    fallback_rate: float = Field(gt=0, default=150.0)


class DisplaySettings(BaseModel):
    fx: DisplayFxSettings = Field(default_factory=DisplayFxSettings)


class MarketSettings(BaseModel):
    id: str = "BTC_5MIN_UPDOWN"
    source: str = "POLYMARKET"
    binance_symbol: str = "BTCUSDT"


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mode: Mode = Mode.PAPER
    initial_principal: float = Field(gt=0, default=1000.0)
    initial_balance: float | None = Field(default=None, gt=0)
    currency: str = "USD"
    market: MarketSettings = Field(default_factory=MarketSettings)
    risk: RiskSettings
    websocket: WebSocketSettings
    nightly_review: NightlyReviewSettings = Field(default_factory=NightlyReviewSettings)
    paths: PathsSettings = Field(default_factory=PathsSettings)
    paper: PaperSettings = Field(default_factory=PaperSettings)
    principal: PrincipalSettings = Field(default_factory=PrincipalSettings)
    display: DisplaySettings = Field(default_factory=DisplaySettings)

    @property
    def resolved_initial_principal(self) -> float:
        """SSOT for seeding bot_state.principal (ch22 §22.2.2)."""

        return self.initial_principal

    @field_validator("mode", mode="before")
    @classmethod
    def _mode_upper(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value


def load_settings(path: Path | str) -> AppSettings:
    """Load and validate yoruu.yaml."""

    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigValidationError(f"Config not found: {config_path}")

    try:
        raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigValidationError(f"Invalid YAML: {config_path}") from exc

    if not isinstance(raw, dict):
        raise ConfigValidationError("Config root must be a mapping")

    if raw.get("initial_principal") is None and raw.get("initial_balance") is not None:
        warnings.warn(
            "initial_balance is deprecated; use initial_principal (ch22 §22.2.2)",
            DeprecationWarning,
            stacklevel=2,
        )
        raw = dict(raw)
        raw["initial_principal"] = raw["initial_balance"]

    try:
        return AppSettings.model_validate(raw)
    except Exception as exc:
        raise ConfigValidationError(str(exc)) from exc
