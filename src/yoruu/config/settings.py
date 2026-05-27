"""yoruu.yaml loader (ch22 SSOT)."""

from __future__ import annotations

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
    slippage_coeff: float = 0.0001
    slippage_max: float = 0.02
    latency_ms_mean: int = 80
    latency_ms_std: int = 20


class MarketSettings(BaseModel):
    id: str = "BTC_5MIN_UPDOWN"
    source: str = "POLYMARKET"
    binance_symbol: str = "BTCUSDT"


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mode: Mode = Mode.PAPER
    initial_balance: float = Field(gt=0, default=1000.0)
    currency: str = "USD"
    market: MarketSettings = Field(default_factory=MarketSettings)
    risk: RiskSettings
    websocket: WebSocketSettings
    nightly_review: NightlyReviewSettings = Field(default_factory=NightlyReviewSettings)
    paths: PathsSettings = Field(default_factory=PathsSettings)
    paper: PaperSettings = Field(default_factory=PaperSettings)

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

    try:
        return AppSettings.model_validate(raw)
    except Exception as exc:
        raise ConfigValidationError(str(exc)) from exc
