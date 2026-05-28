"""Test helpers (not collected as tests)."""

from __future__ import annotations

import json
from pathlib import Path

from yoruu.data.database import Database
from yoruu.strategy.models import StrategyConfig
from yoruu.types import Mode


def init_db(
    tmp_path: Path,
    *,
    balance: float = 1000.0,
    mode: Mode = Mode.PAPER,
    strategy_version: int = 1,
) -> Database:
    db = Database(tmp_path / "test.sqlite")
    db.initialize_schema()
    db.ensure_bot_state(
        mode=mode,
        balance=balance,
        daily_loss_limit=30.0,
        strategy_version=strategy_version,
    )
    return db


def write_isolated_config(tmp_path: Path, strategy: StrategyConfig) -> Path:
    """Minimal yoruu.yaml + strategy.json for CLI tests."""

    strategy_path = tmp_path / "strategy.json"
    strategy_path.write_text(
        json.dumps(strategy.to_json_dict(), ensure_ascii=False),
        encoding="utf-8",
    )
    cfg_path = tmp_path / "yoruu.yaml"
    cfg_path.write_text(
        f"""
mode: PAPER
initial_balance: 1000.0
currency: USD
market:
  id: BTC_5MIN_UPDOWN
  source: POLYMARKET
  binance_symbol: BTCUSDT
risk:
  max_trade_size_usd: 10.0
  daily_loss_limit_usd: 30.0
  emergency_stop_enabled: true
  consecutive_fail_limit: 3
  consecutive_fail_window_min: 15
websocket:
  polymarket_url: wss://example.invalid/ws/
  binance_url: wss://example.invalid/btc
  reconnect_interval_sec: 5
  max_reconnect_attempts: 10
  stale_tick_sec: 30
nightly_review:
  enabled: true
  send_time: "04:00"
  timezone: Asia/Tokyo
  pause_trading_during_review: true
paths:
  db: {(tmp_path / "yoruu.db").as_posix()}
  strategy: {strategy_path.as_posix()}
  logs: {(tmp_path / "logs").as_posix()}
  historical: {(tmp_path / "historical").as_posix()}
  reports: {(tmp_path / "reports").as_posix()}
paper:
  slippage_coeff: 0.0001
  slippage_max: 0.02
  latency_ms_mean: 80
  latency_ms_std: 20
""".strip(),
        encoding="utf-8",
    )
    return cfg_path
