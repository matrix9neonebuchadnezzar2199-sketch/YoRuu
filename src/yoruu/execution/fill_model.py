"""Paper fill price model (ch13 §13.7)."""

from __future__ import annotations

import random
from dataclasses import dataclass

from yoruu.config.settings import PaperSettings
from yoruu.types import CloseReason, OrderBook, Side


@dataclass(frozen=True)
class FillComputation:
    base_price: float
    slippage: float
    fill_price: float
    spread: float
    latency_ms: int


class FillModel:
    """Compute synthetic fills for paper/backtest (ch13)."""

    def __init__(self, settings: PaperSettings, *, seed: int | None = None) -> None:
        self._settings = settings
        self._rng = random.Random(seed)

    def sample_latency_ms(self) -> int:
        mean = self._settings.latency_ms_mean
        std = self._settings.latency_ms_std
        value = int(self._rng.gauss(mean, std))
        return max(value, 0)

    def detect_liquidity_failure(self, *, book: OrderBook, size_usd: float) -> bool:
        """True when ask depth cannot cover full size (ch13 §13.8.1)."""

        return book.ask_size_usd < size_usd

    def compute_open_fill(self, *, book: OrderBook, size_usd: float) -> FillComputation:
        spread = book.spread
        if spread > 0.05:
            raise ValueError("spread too wide")

        if self.detect_liquidity_failure(book=book, size_usd=size_usd):
            raise ValueError("insufficient liquidity")

        base = book.best_ask
        slippage = min(size_usd * self._settings.slippage_coeff, self._settings.slippage_max)
        fill_price = base + slippage
        if fill_price > 0.99:
            raise ValueError("price above binary cap")
        return FillComputation(
            base_price=base,
            slippage=slippage,
            fill_price=fill_price,
            spread=spread,
            latency_ms=self.sample_latency_ms(),
        )

    def compute_close_fill(
        self,
        *,
        book: OrderBook,
        size_usd: float,
        side: Side,
        reason: CloseReason,
    ) -> FillComputation:
        if reason == CloseReason.EXPIRATION:
            fill_price = 1.0 if side == Side.YES else 0.0
            return FillComputation(
                base_price=fill_price,
                slippage=0.0,
                fill_price=fill_price,
                spread=book.spread,
                latency_ms=0,
            )

        base = book.best_bid
        slippage = min(size_usd * self._settings.slippage_coeff, self._settings.slippage_max)
        fill_price = base - slippage
        if fill_price < 0.01:
            raise ValueError("fill price below minimum (E_FILL_004)")
        return FillComputation(
            base_price=base,
            slippage=slippage,
            fill_price=fill_price,
            spread=book.spread,
            latency_ms=self.sample_latency_ms(),
        )
