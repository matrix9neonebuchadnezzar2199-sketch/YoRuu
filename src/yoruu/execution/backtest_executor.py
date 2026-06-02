"""Backtest mode executor (ch13 §13.5, PHASE 6 M6.3)."""

from __future__ import annotations

import json
from dataclasses import dataclass

from yoruu.execution.fill_model import FillModel
from yoruu.infra.historical_loader import HistoricalBar, HistoricalLoader
from yoruu.strategy.evaluator import StrategyEvaluator
from yoruu.strategy.markov import MarkovEngine
from yoruu.types import CloseReason, MarketState, Mode, OrderBook, Side


@dataclass(frozen=True)
class BacktestResult:
    trades: int
    wins: int
    win_rate: float
    pnl_total: float
    max_drawdown: float
    final_balance: float
    params: dict
    period: tuple[str, str]


class BacktestExecutor:
    """Replay 5m bars without StateMachine (ch12 §12.4.2)."""

    def __init__(
        self,
        loader: HistoricalLoader,
        fill_model: FillModel,
        markov: MarkovEngine,
        evaluator: StrategyEvaluator,
        *,
        max_trade_size_usd: float,
        initial_balance: float,
        spread_assumed: float = 0.02,
    ) -> None:
        self._loader = loader
        self._fill_model = fill_model
        self._markov = markov
        self._evaluator = evaluator
        self._max_trade_size = max_trade_size_usd
        self._initial_balance = initial_balance
        self._spread = spread_assumed

    def _book_from_mid(self, mid: float, market: str) -> OrderBook:
        half = self._spread / 2.0
        bid = max(mid - half, 0.01)
        ask = min(mid + half, 0.99)
        return OrderBook(
            market=market,
            best_bid=bid,
            best_ask=ask,
            bid_size_usd=100.0,
            ask_size_usd=100.0,
            spread=ask - bid,
            captured_at_iso="backtest",
            source="BACKTEST",
        )

    def run(
        self,
        *,
        start: str,
        end: str,
        market_id: str = "BTC_5MIN_UPDOWN",
        rng_seed: int = 42,
    ) -> BacktestResult:
        del rng_seed  # FillModel seed is set at construction
        bars = self._loader.load_closes(start=start, end=end)
        balance = self._initial_balance
        peak = balance
        max_dd = 0.0
        trades = 0
        wins = 0
        pnl_total = 0.0
        open_trade: dict | None = None

        for i, bar in enumerate(bars):
            self._markov.add_close(bar.close)
            if open_trade is not None:
                book = self._book_from_mid(open_trade["mid"], market_id)
                comp = self._fill_model.compute_close_fill(
                    book=book,
                    size_usd=open_trade["size"],
                    side=open_trade["side"],
                    reason=CloseReason.EXPIRATION,
                )
                entry = open_trade["entry"]
                shares = open_trade["size"] / entry if entry > 0 else 0.0
                pnl = (comp.fill_price - entry) * shares
                balance += open_trade["size"] + pnl
                pnl_total += pnl
                trades += 1
                if pnl > 0:
                    wins += 1
                open_trade = None
                peak = max(peak, balance)
                dd = (peak - balance) / peak if peak > 0 else 0.0
                max_dd = max(max_dd, dd)

            snap = self._markov.snapshot()
            mid = 0.81
            yes_book = self._book_from_mid(mid, market_id)
            mstate = MarketState(order_book_yes=yes_book, order_book_no=None)
            result = self._evaluator.evaluate(
                mstate,
                balance=balance,
                max_trade_size_usd=self._max_trade_size,
                snapshot=snap,
                risk_guard=None,
            )
            if not result.should_enter or result.side is None or open_trade is not None:
                continue
            if result.size_usd > balance:
                continue
            book = yes_book
            try:
                comp = self._fill_model.compute_open_fill(book=book, size_usd=result.size_usd)
            except ValueError:
                continue
            balance -= result.size_usd
            open_trade = {
                "entry": comp.fill_price,
                "size": result.size_usd,
                "side": result.side,
                "mid": mid,
            }
            if i + 1 >= len(bars):
                break

        if open_trade is not None:
            book = self._book_from_mid(open_trade["mid"], market_id)
            comp = self._fill_model.compute_close_fill(
                book=book,
                size_usd=open_trade["size"],
                side=open_trade["side"],
                reason=CloseReason.EXPIRATION,
            )
            entry = open_trade["entry"]
            shares = open_trade["size"] / entry if entry > 0 else 0.0
            pnl = (comp.fill_price - entry) * shares
            balance += open_trade["size"] + pnl
            pnl_total += pnl
            trades += 1
            if pnl > 0:
                wins += 1

        win_rate = (wins / trades) if trades else 0.0
        params = self._evaluator.strategy.parameters.model_dump()
        return BacktestResult(
            trades=trades,
            wins=wins,
            win_rate=win_rate,
            pnl_total=pnl_total,
            max_drawdown=max_dd,
            final_balance=balance,
            params=params,
            period=(start, end),
        )

    def result_to_json(self, result: BacktestResult) -> str:
        return json.dumps(
            {
                "trades": result.trades,
                "wins": result.wins,
                "win_rate": result.win_rate,
                "pnl_total": result.pnl_total,
                "max_drawdown": result.max_drawdown,
                "final_balance": result.final_balance,
                "params": result.params,
                "period": list(result.period),
            },
            indent=2,
        )
