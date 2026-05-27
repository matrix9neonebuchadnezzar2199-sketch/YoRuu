"""Fill model tests."""

import pytest

from yoruu.config.settings import PaperSettings
from yoruu.execution.fill_model import FillModel
from yoruu.types import OrderBook, Side


def _book() -> OrderBook:
    return OrderBook(
        market="BTC_5MIN_UPDOWN",
        best_bid=0.79,
        best_ask=0.81,
        bid_size_usd=100.0,
        ask_size_usd=100.0,
        spread=0.02,
        captured_at_iso="2026-01-01T00:00:00+00:00",
        source="MOCK",
    )


def test_open_fill_success() -> None:
    model = FillModel(PaperSettings(), seed=1)
    comp = model.compute_open_fill(book=_book(), size_usd=5.0)
    assert comp.fill_price > comp.base_price


def test_open_fill_rejects_wide_spread() -> None:
    model = FillModel(PaperSettings(), seed=1)
    book = OrderBook(
        market="m",
        best_bid=0.40,
        best_ask=0.90,
        bid_size_usd=100.0,
        ask_size_usd=100.0,
        spread=0.50,
        captured_at_iso="t",
        source="MOCK",
    )
    with pytest.raises(ValueError, match="spread"):
        model.compute_open_fill(book=book, size_usd=5.0)
