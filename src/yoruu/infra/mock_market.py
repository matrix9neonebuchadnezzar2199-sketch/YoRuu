"""Offline market data for paper core (M3.1)."""

from __future__ import annotations

from datetime import UTC, datetime

from yoruu.types import MarketState, OrderBook, PriceTick


class MockMarketProvider:
    """Synthetic ticks and order books without network (lab default)."""

    def __init__(
        self,
        *,
        market_id: str = "BTC_5MIN_UPDOWN",
        base_price: float = 0.81,
        spread: float = 0.02,
    ) -> None:
        self._market_id = market_id
        self._base = base_price
        self._spread = spread

    def next_tick(self, symbol: str = "BTCUSDT", *, delta: float = 0.0) -> PriceTick:
        price = self._base + delta
        return PriceTick(
            source="BINANCE",
            symbol=symbol,
            price=price,
            ts_iso=datetime.now(UTC).isoformat(),
        )

    def market_state(self, *, yes_ask: float | None = None) -> MarketState:
        ask = yes_ask if yes_ask is not None else self._base
        bid = max(ask - self._spread, 0.01)
        now = datetime.now(UTC).isoformat()
        yes_book = OrderBook(
            market=self._market_id,
            best_bid=bid,
            best_ask=ask,
            bid_size_usd=100.0,
            ask_size_usd=100.0,
            spread=ask - bid,
            captured_at_iso=now,
            source="MOCK",
        )
        no_ask = 1.0 - bid
        no_bid = 1.0 - ask
        no_book = OrderBook(
            market=self._market_id,
            best_bid=max(no_bid, 0.01),
            best_ask=no_ask,
            bid_size_usd=100.0,
            ask_size_usd=100.0,
            spread=no_ask - no_bid,
            captured_at_iso=now,
            source="MOCK",
        )
        return MarketState(order_book_yes=yes_book, order_book_no=no_book)
