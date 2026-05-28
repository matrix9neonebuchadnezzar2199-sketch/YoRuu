"""Live trading executor (ch13 §13.6, ch24)."""

from __future__ import annotations

import logging

from yoruu.infra.clob_types import LiveOrderRequest, LiveOrderResult
from yoruu.infra.polymarket_clob import PolymarketClient

logger = logging.getLogger(__name__)


class LiveExecutor:
    """Place live orders via PolymarketClient."""

    def __init__(self, client: PolymarketClient) -> None:
        self._client = client

    async def open(self, request: LiveOrderRequest) -> LiveOrderResult:
        if self._client.is_ws_stale():
            return LiveOrderResult(
                success=False,
                order_id=None,
                message="market data stale (E_WS_001)",
                error_code="E_WS_001",
            )
        return await self._client.place_order(request)

    async def close(self) -> None:
        await self._client.close()
