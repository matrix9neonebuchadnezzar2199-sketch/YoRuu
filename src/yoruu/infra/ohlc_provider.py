"""In-memory OHLC ring buffer for HUD chart (PHASE 5 M5.3)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

Severity = str


@dataclass(frozen=True)
class OhlcBar:
    """Single 5-minute OHLC bar (UTC ISO timestamp)."""

    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def to_dict(self) -> dict[str, float | str]:
        return {
            "ts": self.ts,
            "open": round(self.open, 2),
            "high": round(self.high, 2),
            "low": round(self.low, 2),
            "close": round(self.close, 2),
            "volume": round(self.volume, 4),
        }


class OhlcProvider:
    """Ring buffer of recent 5m bars; lab-seeded when empty."""

    def __init__(self, *, max_bars: int = 60) -> None:
        self._max_bars = max_bars
        self._bars: list[OhlcBar] = []
        self._live: bool = False

    def seed_lab_fixture(self, *, base_price: float = 68_250.0) -> None:
        """Populate synthetic BTC 5m bars for offline HUD (no network)."""
        now = datetime.now(UTC).replace(second=0, microsecond=0)
        # Align to 5-minute boundary
        minute = (now.minute // 5) * 5
        now = now.replace(minute=minute)
        bars: list[OhlcBar] = []
        price = base_price
        for i in range(self._max_bars):
            ts = now - timedelta(minutes=5 * (self._max_bars - 1 - i))
            drift = math.sin(i / 8.0) * 120.0 + (i % 7 - 3) * 15.0
            open_p = price
            close_p = price + drift
            high_p = max(open_p, close_p) + abs(drift) * 0.15
            low_p = min(open_p, close_p) - abs(drift) * 0.15
            bars.append(
                OhlcBar(
                    ts=ts.isoformat(),
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=12.5 + (i % 5),
                )
            )
            price = close_p
        self._bars = bars

    def ensure_seeded(self) -> None:
        if not self._bars:
            self.seed_lab_fixture()

    @property
    def source(self) -> str:
        """``lab`` until a live tick arrives (M6.2 HUD honesty)."""

        return "live" if self._live else "lab"

    def get_bars(self, limit: int | None = None) -> list[dict[str, float | str]]:
        """Return up to ``limit`` most recent bars (oldest first)."""
        self.ensure_seeded()
        n = limit if limit is not None else self._max_bars
        n = max(1, min(n, self._max_bars, len(self._bars)))
        return [b.to_dict() for b in self._bars[-n:]]

    def _bar_bucket_start(self, ts: datetime) -> datetime:
        minute = (ts.minute // 5) * 5
        return ts.replace(minute=minute, second=0, microsecond=0)

    def update_from_tick(self, price: float, ts_iso: str | None = None) -> None:
        """Merge a trade tick; start a new 5m bar when the bucket changes."""
        self._live = True
        raw_ts = ts_iso or datetime.now(UTC).isoformat()
        tick_ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        bucket = self._bar_bucket_start(tick_ts)

        if not self._bars:
            self.seed_lab_fixture()
            self._live = True

        last = self._bars[-1]
        last_bucket = self._bar_bucket_start(
            datetime.fromisoformat(last.ts.replace("Z", "+00:00"))
        )
        if bucket > last_bucket:
            self._bars.append(
                OhlcBar(
                    ts=bucket.isoformat(),
                    open=last.close,
                    high=price,
                    low=price,
                    close=price,
                )
            )
            if len(self._bars) > self._max_bars:
                self._bars = self._bars[-self._max_bars :]
            return

        self._bars[-1] = OhlcBar(
            ts=last.ts,
            open=last.open,
            high=max(last.high, price),
            low=min(last.low, price),
            close=price,
            volume=last.volume + 0.01,
        )
