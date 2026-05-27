"""Kelly criterion sizing (ch11 §11.6)."""

from __future__ import annotations


def kelly_fraction_binary(*, prob_win: float, market_price: float) -> float:
    """Full Kelly fraction f* for binary market (ch11 §11.6.1)."""

    if market_price <= 0 or market_price >= 1:
        return 0.0
    q = 1.0 - prob_win
    b = (1.0 - market_price) / market_price
    if b <= 0:
        return 0.0
    return (b * prob_win - q) / b


def size_usd_from_kelly(
    *,
    balance: float,
    prob_win: float,
    market_price: float,
    kelly_fraction_param: float,
    max_trade_size_usd: float,
) -> float:
    """Fractional Kelly position size in USD (ch11 §11.6.2–6.3)."""

    f_star = kelly_fraction_binary(prob_win=prob_win, market_price=market_price)
    if f_star <= 0:
        return 0.0
    fraction = f_star * kelly_fraction_param
    raw = balance * fraction
    return min(max(raw, 0.0), max_trade_size_usd)
