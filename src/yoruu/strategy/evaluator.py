"""Entry evaluation (ch11 §11.7)."""

from __future__ import annotations

from yoruu.strategy.kelly import size_usd_from_kelly
from yoruu.strategy.markov import MarkovEngine, MarkovSnapshot
from yoruu.strategy.models import StrategyConfig
from yoruu.types import Direction, EvaluationResult, MarketState, Side


class StrategyEvaluator:
    """Combine Markov persistence, edge, and Kelly sizing."""

    def __init__(self, markov: MarkovEngine, strategy: StrategyConfig) -> None:
        self._markov = markov
        self._strategy = strategy

    @property
    def strategy(self) -> StrategyConfig:
        return self._strategy

    def reload(self, strategy: StrategyConfig) -> None:
        self._strategy = strategy

    def evaluate(
        self,
        market_state: MarketState,
        *,
        balance: float,
        max_trade_size_usd: float,
        snapshot: MarkovSnapshot | None = None,
    ) -> EvaluationResult:
        """Run four AND conditions from ch11 §11.7.2."""

        snap = snapshot or self._markov.snapshot()
        params = self._strategy.parameters
        persistence = snap.rolling_persistence

        if persistence < params.PERSISTENCE_THRESHOLD:
            return self._wait(
                persistence=persistence,
                wait_reason="persistence",
                msg="persistence below threshold",
            )

        if snap.last_direction is None:
            return self._wait(
                persistence=persistence,
                wait_reason="persistence",
                msg="no direction yet",
            )

        prob_up, prob_down = self._markov.predict_next(snap.last_direction)
        if prob_up >= prob_down:
            pred_dir = Direction.UP
            predicted_prob = prob_up
            book = market_state.order_book_yes
            side = Side.YES
        else:
            pred_dir = Direction.DOWN
            predicted_prob = prob_down
            book = market_state.order_book_no or market_state.order_book_yes
            side = Side.NO

        if predicted_prob < params.MIN_PROB:
            return self._wait(
                persistence=persistence,
                predicted_prob=predicted_prob,
                market_price=book.best_ask,
                wait_reason="prob",
                msg="probability below MIN_PROB",
            )

        if not book.spread_ok:
            return self._wait(
                persistence=persistence,
                predicted_prob=predicted_prob,
                market_price=book.best_ask,
                wait_reason="liquidity",
                msg="spread too wide",
            )

        market_price = book.best_ask
        edge = predicted_prob - market_price
        if edge < params.MIN_EDGE:
            return self._wait(
                persistence=persistence,
                predicted_prob=predicted_prob,
                market_price=market_price,
                edge=edge,
                wait_reason="edge",
                msg="edge below MIN_EDGE",
            )

        size_usd = size_usd_from_kelly(
            balance=balance,
            prob_win=predicted_prob,
            market_price=market_price,
            kelly_fraction_param=params.KELLY_FRACTION,
            max_trade_size_usd=max_trade_size_usd,
        )
        if size_usd < 1.0:
            return self._wait(
                persistence=persistence,
                predicted_prob=predicted_prob,
                market_price=market_price,
                edge=edge,
                wait_reason="edge",
                msg="Kelly size too small",
            )

        return EvaluationResult(
            should_enter=True,
            side=side,
            size_usd=size_usd,
            edge=edge,
            persistence=persistence,
            predicted_prob=predicted_prob,
            market_price=market_price,
            reason="all_conditions_met",
            wait_reason=None,
        )

    def _wait(
        self,
        *,
        persistence: float,
        wait_reason: str,
        msg: str,
        predicted_prob: float = 0.0,
        market_price: float = 0.0,
        edge: float = 0.0,
    ) -> EvaluationResult:
        return EvaluationResult(
            should_enter=False,
            side=None,
            size_usd=0.0,
            edge=edge,
            persistence=persistence,
            predicted_prob=predicted_prob,
            market_price=market_price,
            reason=f"wait:{msg}",
            wait_reason=wait_reason,
        )
