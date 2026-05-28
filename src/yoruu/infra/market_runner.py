"""Run market WebSocket feeds (ch10 §10.8)."""

from __future__ import annotations

import asyncio
import logging

from yoruu.config.settings import AppSettings
from yoruu.data.database import Database
from yoruu.infra.binance_ws import BinanceMarketWs
from yoruu.infra.polymarket_ws import PolymarketMarketWs

logger = logging.getLogger(__name__)


async def run_market_feeds(
    settings: AppSettings,
    db: Database,
    *,
    duration_sec: float | None = None,
) -> None:
    """Connect Polymarket + Binance WS until stopped or duration elapsed."""

    binance = BinanceMarketWs(
        settings.websocket,
        symbol=settings.market.binance_symbol,
        db=db,
    )
    polymarket = PolymarketMarketWs(
        settings.websocket,
        market_id=settings.market.id,
        db=db,
    )
    await binance.connect()
    await polymarket.connect()
    try:
        if duration_sec is None:
            await asyncio.Event().wait()
        else:
            await asyncio.sleep(duration_sec)
    finally:
        await binance.disconnect()
        await polymarket.disconnect()
        db.commit()
        db.close()
