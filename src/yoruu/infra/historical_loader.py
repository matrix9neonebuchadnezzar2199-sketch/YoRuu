"""Historical 5m closes for backtest (PHASE 6 M6.3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from yoruu.data.database import Database
from yoruu.types import PriceTick


@dataclass(frozen=True)
class HistoricalBar:
    """One 5-minute close for backtest replay."""

    ts_iso: str
    close: float


class HistoricalLoader:
    """Load closes from SQLite ticks or synthetic lab series."""

    def __init__(self, db: Database | None = None, *, historical_dir: Path | None = None) -> None:
        self._db = db
        self._historical_dir = historical_dir

    def load_closes(
        self,
        *,
        start: str,
        end: str,
        symbol: str = "BTCUSDT",
    ) -> list[HistoricalBar]:
        """Return 5m bars between start/end (inclusive dates, UTC)."""

        if self._db is not None:
            rows = self._db.connection.execute(
                """
                SELECT price, ts FROM price_ticks
                WHERE symbol = ? AND date(ts) >= date(?) AND date(ts) <= date(?)
                ORDER BY ts
                """,
                (symbol, start, end),
            ).fetchall()
            if rows:
                return self._aggregate_ticks(rows)

        return self._synthetic_lab_series(start, end)

    def _aggregate_ticks(self, rows: list) -> list[HistoricalBar]:
        buckets: dict[str, list[float]] = {}
        for row in rows:
            ts = datetime.fromisoformat(str(row["ts"]).replace("Z", "+00:00"))
            minute = (ts.minute // 5) * 5
            key = ts.replace(minute=minute, second=0, microsecond=0).isoformat()
            buckets.setdefault(key, []).append(float(row["price"]))
        return [
            HistoricalBar(ts_iso=k, close=vals[-1])
            for k, vals in sorted(buckets.items())
        ]

    def _synthetic_lab_series(self, start: str, end: str) -> list[HistoricalBar]:
        """Monotonic lab prices for deterministic backtest."""

        start_dt = datetime.fromisoformat(f"{start}T00:00:00+00:00")
        end_dt = datetime.fromisoformat(f"{end}T23:59:00+00:00")
        bars: list[HistoricalBar] = []
        price = 100.0
        cursor = start_dt
        while cursor <= end_dt:
            bars.append(HistoricalBar(ts_iso=cursor.isoformat(), close=price))
            price += 2.0
            cursor += timedelta(minutes=5)
        return bars

    def as_ticks(self, bars: list[HistoricalBar], *, symbol: str = "BTCUSDT") -> list[PriceTick]:
        return [
            PriceTick(source="BINANCE", symbol=symbol, price=b.close, ts_iso=b.ts_iso)
            for b in bars
        ]
