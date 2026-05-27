"""Kelly sizing tests."""

from yoruu.strategy.kelly import kelly_fraction_binary, size_usd_from_kelly


def test_kelly_positive_fraction() -> None:
    f_star = kelly_fraction_binary(prob_win=0.89, market_price=0.81)
    assert f_star > 0


def test_size_clipped_to_max() -> None:
    size = size_usd_from_kelly(
        balance=1042.18,
        prob_win=0.89,
        market_price=0.81,
        kelly_fraction_param=0.65,
        max_trade_size_usd=10.0,
    )
    assert size == 10.0
