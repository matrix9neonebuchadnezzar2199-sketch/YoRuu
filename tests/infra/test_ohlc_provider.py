"""OhlcProvider unit tests."""

from yoruu.infra.ohlc_provider import OhlcProvider


def test_seed_and_get_bars() -> None:
    provider = OhlcProvider(max_bars=60)
    provider.seed_lab_fixture(base_price=70_000.0)
    bars = provider.get_bars(5)
    assert len(bars) == 5
    assert bars[-1]["close"] != bars[0]["open"] or bars[0]["open"] == 70_000.0
