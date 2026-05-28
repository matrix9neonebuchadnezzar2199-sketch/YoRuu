"""Binance market-data WebSocket (ch10 §10.8.2)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from yoruu.config.settings import WebSocketSettings
from yoruu.data.database import Database
from yoruu.infra.ws_client import AsyncWsClient
from yoruu.types import PriceTick

logger = logging.getLogger(__name__)

TickHandler = Callable[[PriceTick], Awaitable[None]]


class BinanceMarketWs:
    """Subscribe to Binance trade stream and emit PriceTick."""

    def __init__(
        self,
        settings: WebSocketSettings,
        *,
        symbol: str = "BTCUSDT",
        db: Database | None = None,
        on_tick: TickHandler | None = None,
    ) -> None:
        self._symbol = symbol.upper()
        self._db = db
        self._on_tick = on_tick
        self._client = AsyncWsClient(
            name="binance",
            url=settings.binance_url,
            settings=settings,
            on_message=self._handle_message,
        )

    @property
    def client(self) -> AsyncWsClient:
        return self._client

    async def connect(self) -> None:
        await self._client.connect()
        if self._db is not None:
            self._db.set_ws_connected(binance=True)

    async def disconnect(self) -> None:
        await self._client.disconnect()
        if self._db is not None:
            self._db.set_ws_connected(binance=False)

    async def _handle_message(self, payload: dict[str, Any]) -> None:
        price_raw = payload.get("p") or payload.get("price")
        if price_raw is None:
            return
        tick = PriceTick(
            source="BINANCE",
            symbol=self._symbol,
            price=float(price_raw),
            ts_iso=datetime.now(UTC).isoformat(),
        )
        if self._db is not None:
            self._db.insert_price_tick(
                source=tick.source,
                symbol=tick.symbol,
                price=tick.price,
                ts_iso=tick.ts_iso,
            )
        if self._on_tick is not None:
            await self._on_tick(tick)
