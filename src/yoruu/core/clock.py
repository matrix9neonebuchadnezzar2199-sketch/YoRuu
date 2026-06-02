"""Injectable clocks for TradingLoop tests (PHASE 6 M6.1)."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta


class Clock(ABC):
    """Abstract time source for deterministic loop tests."""

    @abstractmethod
    def now(self) -> datetime:
        """Current instant (timezone-aware UTC)."""

    @abstractmethod
    async def sleep(self, seconds: float) -> None:
        """Wait until the next evaluation boundary."""


class SystemClock(Clock):
    """Production clock backed by wall time."""

    def now(self) -> datetime:
        return datetime.now(UTC)

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(max(0.0, seconds))


class VirtualClock(Clock):
    """Advances only when ``advance`` is called (unit tests)."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now = self._now + timedelta(seconds=seconds)

    async def sleep(self, seconds: float) -> None:
        self.advance(seconds)
