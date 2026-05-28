"""Async WebSocket client base (ch10 §10.8, ch24 §24.7)."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from yoruu.config.settings import WebSocketSettings

logger = logging.getLogger(__name__)

MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass
class WsConnectionState:
    connected: bool = False
    last_message_at: datetime | None = None
    reconnect_attempts: int = 0


class AsyncWsClient:
    """Reconnecting WebSocket with stale-tick detection."""

    def __init__(
        self,
        *,
        name: str,
        url: str,
        settings: WebSocketSettings,
        on_message: MessageHandler,
    ) -> None:
        self._name = name
        self._url = url
        self._settings = settings
        self._on_message = on_message
        self._state = WsConnectionState()
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._conn: ClientConnection | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_connected(self) -> bool:
        return self._state.connected

    @property
    def is_stale(self) -> bool:
        if self._state.last_message_at is None:
            return True
        age = (datetime.now(UTC) - self._state.last_message_at).total_seconds()
        return age > self._settings.stale_tick_sec

    async def connect(self) -> None:
        if self._task is not None:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run_loop(), name=f"ws-{self._name}")

    async def disconnect(self) -> None:
        self._stop.set()
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
        if self._task is not None:
            await self._task
            self._task = None
        self._state.connected = False

    async def _run_loop(self) -> None:
        backoff = self._settings.reconnect_interval_sec
        while not self._stop.is_set():
            try:
                async with websockets.connect(self._url, open_timeout=10) as conn:
                    self._conn = conn
                    self._state.connected = True
                    self._state.reconnect_attempts = 0
                    backoff = self._settings.reconnect_interval_sec
                    logger.info("ws connected: %s", self._name)
                    async for raw in conn:
                        if self._stop.is_set():
                            break
                        self._state.last_message_at = datetime.now(UTC)
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError:
                            logger.warning("ws invalid json from %s", self._name)
                            continue
                        if isinstance(payload, dict):
                            await self._on_message(payload)
            except Exception as exc:
                self._state.connected = False
                self._conn = None
                self._state.reconnect_attempts += 1
                logger.warning(
                    "ws error %s (attempt %s): %s",
                    self._name,
                    self._state.reconnect_attempts,
                    exc,
                )
                if self._state.reconnect_attempts >= self._settings.max_reconnect_attempts:
                    logger.error("ws max reconnect exceeded: %s", self._name)
                    await asyncio.sleep(backoff)
                    self._state.reconnect_attempts = 0
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
