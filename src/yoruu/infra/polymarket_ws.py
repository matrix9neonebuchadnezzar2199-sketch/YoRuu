"""Polymarket market-data WebSocket (ch10 §10.8.1)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from yoruu.config.settings import WebSocketSettings
from yoruu.data.database import Database
from yoruu.infra.ws_client import AsyncWsClient
from yoruu.types import OrderBook, PriceTick

logger = logging.getLogger(__name__)

BookHandler = Callable[[OrderBook], Awaitable[None]]


class PolymarketMarketWs:
    """Polymarket WS for book / price updates (market channel)."""

    def __init__(
        self,
        settings: WebSocketSettings,
        *,
        market_id: str,
        db: Database | None = None,
        on_book: BookHandler | None = None,
    ) -> None:
        self._market_id = market_id
        self._db = db
        self._on_book = on_book
        self._client = AsyncWsClient(
            name="polymarket",
            url=settings.polymarket_url,
            settings=settings,
            on_message=self._handle_message,
        )

    @property
    def client(self) -> AsyncWsClient:
        return self._client

    async def connect(self) -> None:
        await self._client.connect()
        if self._db is not None:
            self._db.set_ws_connected(polymarket=True)

    async def disconnect(self) -> None:
        await self._client.disconnect()
        if self._db is not None:
            self._db.set_ws_connected(polymarket=False)

    async def _handle_message(self, payload: dict[str, Any]) -> None:
        bids = payload.get("bids") or payload.get("buys")
        asks = payload.get("asks") or payload.get("sells")
        if not bids or not asks:
            price = payload.get("price")
            if price is not None and self._db is not None:
                tick = PriceTick(
                    source="POLYMARKET",
                    symbol=self._market_id,
                    price=float(price),
                    ts_iso=datetime.now(UTC).isoformat(),
                )
                self._db.insert_price_tick(
                    source=tick.source,
                    symbol=tick.symbol,
                    price=tick.price,
                    ts_iso=tick.ts_iso,
                )
            return

        def top(levels: list[Any]) -> tuple[float, float]:
            first = levels[0]
            if isinstance(first, (list, tuple)) and len(first) >= 2:
                return float(first[0]), float(first[1])
            return 0.0, 0.0

        best_bid, bid_size = top(list(bids))
        best_ask, ask_size = top(list(asks))
        if best_bid <= 0 or best_ask <= 0:
            return
        book = OrderBook(
            market=self._market_id,
            best_bid=best_bid,
            best_ask=best_ask,
            bid_size_usd=bid_size,
            ask_size_usd=ask_size,
            spread=best_ask - best_bid,
            captured_at_iso=datetime.now(UTC).isoformat(),
            source="WS",
        )
        if self._on_book is not None:
            await self._on_book(book)
