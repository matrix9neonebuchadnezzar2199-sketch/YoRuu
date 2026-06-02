"""Chaos / safety scenarios (PHASE 6 M6.5, lab)."""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import init_db
from yoruu.config.settings import PaperSettings, RiskSettings
from yoruu.core.loop_runtime import build_trading_loop
from yoruu.config.settings import load_settings
from yoruu.execution.risk_guard import RiskGuard
from yoruu.types import State


@pytest.mark.asyncio
async def test_daily_loss_triggers_emergency(tmp_path: Path) -> None:
    cfg_path = tmp_path / "yoruu.yaml"
    (tmp_path / "logs").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "historical").mkdir()
    db_path = tmp_path / "yoruu.db"
    strategy_path = tmp_path / "strategy.json"
    strategy_path.write_text(
        '{"version":1,"parameters":{"MIN_PROB":0.55,"MIN_EDGE":0.03,'
        '"KELLY_FRACTION":0.65,"PERSISTENCE_THRESHOLD":0.70},'
        '"constraints":{}}',
        encoding="utf-8",
    )
    cfg_path.write_text(
        f"""
mode: PAPER
initial_balance: 1000.0
market:
  id: BTC_5MIN_UPDOWN
risk:
  max_trade_size_usd: 10.0
  daily_loss_limit_usd: 5.0
websocket:
  polymarket_url: wss://example.invalid/ws/
  binance_url: wss://example.invalid/btc
paths:
  db: {db_path.as_posix()}
  strategy: {strategy_path.as_posix()}
  logs: logs/
  historical: historical/
  reports: reports/
paper:
  slippage_coeff: 0.0001
  slippage_max: 0.02
""".strip(),
        encoding="utf-8",
    )
    settings = load_settings(cfg_path)
    db = init_db(tmp_path, balance=1000.0)
    db.update_balance_and_pnl(990.0, -10.0)
    db.commit()
    loop = build_trading_loop(settings, db, interval_sec=1)
    assert loop.emergency_controller is not None
    await loop.evaluate_cycle()
    assert loop._sm.current() == State.EMERGENCY_STOP  # noqa: SLF001
