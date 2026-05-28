"""Binance WS message parsing (no network)."""

import pytest

from yoruu.config.settings import WebSocketSettings
from yoruu.infra.binance_ws import BinanceMarketWs
from yoruu.types import PriceTick


@pytest.mark.asyncio
async def test_binance_trade_message_parsed() -> None:
    ticks: list[PriceTick] = []

    async def on_tick(tick: PriceTick) -> None:
        ticks.append(tick)

    ws = BinanceMarketWs(
        WebSocketSettings(
            polymarket_url="wss://example.invalid/p",
            binance_url="wss://example.invalid/b",
        ),
        on_tick=on_tick,
    )
    await ws._handle_message({"p": "65000.5", "s": "BTCUSDT"})
    assert len(ticks) == 1
    assert ticks[0].price == pytest.approx(65000.5)
    assert ticks[0].source == "BINANCE"
