"""Polymarket CLOB user WebSocket (ch24 §24.7)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from yoruu.config.settings import WebSocketSettings
from yoruu.infra.ws_client import AsyncWsClient

logger = logging.getLogger(__name__)

FillHandler = Callable[[dict[str, Any]], Awaitable[None]]


class ClobWsClient:
    """CLOB execution / fill channel over WebSocket."""

    def __init__(
        self,
        settings: WebSocketSettings,
        *,
        url: str | None = None,
        on_fill: FillHandler | None = None,
    ) -> None:
        ws_url = url or settings.polymarket_url
        self._on_fill = on_fill
        self._client = AsyncWsClient(
            name="clob",
            url=ws_url,
            settings=settings,
            on_message=self._handle_message,
        )

    @property
    def client(self) -> AsyncWsClient:
        return self._client

    async def connect(self) -> None:
        await self._client.connect()

    async def disconnect(self) -> None:
        await self._client.disconnect()

    async def _handle_message(self, payload: dict[str, Any]) -> None:
        if self._on_fill is not None:
            await self._on_fill(payload)
