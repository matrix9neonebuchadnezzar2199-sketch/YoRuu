"""Polymarket CLOB facade (ch24 §24.8)."""

from __future__ import annotations

from pathlib import Path

from yoruu.config.settings import WebSocketSettings
from yoruu.infra.clob_rest import ClobRestClient
from yoruu.infra.clob_types import LiveOrderRequest, LiveOrderResult
from yoruu.infra.clob_ws import ClobWsClient


class PolymarketClient:
    """REST + WS CLOB client for LiveExecutor."""

    def __init__(
        self,
        *,
        rest: ClobRestClient,
        ws: ClobWsClient,
    ) -> None:
        self._rest = rest
        self._ws = ws

    @classmethod
    def from_settings(
        cls,
        ws_settings: WebSocketSettings,
        *,
        rest_base_url: str = "https://clob.lab.invalid",
        fixture_dir: Path | None = None,
        clob_ws_url: str | None = None,
    ) -> PolymarketClient:
        rest = ClobRestClient(base_url=rest_base_url, fixture_dir=fixture_dir)
        ws = ClobWsClient(ws_settings, url=clob_ws_url)
        return cls(rest=rest, ws=ws)

    async def connect(self) -> None:
        await self._ws.connect()

    async def place_order(self, req: LiveOrderRequest) -> LiveOrderResult:
        return await self._rest.place_order(req)

    async def cancel_order(self, order_id: str) -> bool:
        return await self._rest.cancel_order(order_id)

    async def get_balance_usdc(self) -> float:
        return await self._rest.get_balance_usdc()

    def is_ws_stale(self) -> bool:
        return self._ws.client.is_stale

    async def close(self) -> None:
        await self._ws.disconnect()
