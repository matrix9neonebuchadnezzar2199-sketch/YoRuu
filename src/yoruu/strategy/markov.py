"""Markov transition matrix engine (ch11 §11.3)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from yoruu.types import Direction, PriceTick, TransitionMatrix


def compute_persistence(matrix: TransitionMatrix) -> float:
    """min(P(UP→UP), P(DOWN→DOWN)) — ch11 §11.4.1."""

    normalized = matrix.normalized()
    return min(normalized.p_up_up, normalized.p_down_down)


@dataclass
class MarkovSnapshot:
    computed_at_iso: str
    window_size: int
    matrix: TransitionMatrix
    rolling_persistence: float
    last_direction: Direction | None


class MarkovEngine:
    """Estimate 2-state Markov chain from price closes (ch11 §11.3)."""

    def __init__(self, window_size: int = 20) -> None:
        if window_size < 3:
            raise ValueError("window_size must be >= 3")
        self._window_size = window_size
        self._closes: list[float] = []
        self._matrix = TransitionMatrix(0.5, 0.5, 0.5, 0.5)
        self._last_direction: Direction | None = None
        self._last_computed_at: str | None = None

    @property
    def window_size(self) -> int:
        return self._window_size

    def add_close(self, price: float) -> MarkovSnapshot | None:
        """Append a 5-minute close price; recompute when enough samples."""

        self._closes.append(price)
        if len(self._closes) > self._window_size + 1:
            self._closes = self._closes[-(self._window_size + 1) :]
        if len(self._closes) < self._window_size + 1:
            return None
        return self._recompute()

    def update_tick(self, tick: PriceTick) -> MarkovSnapshot | None:
        """Optional hook for tick stream; treats each tick as close (tests)."""

        return self.add_close(tick.price)

    def _recompute(self) -> MarkovSnapshot:
        prices = self._closes[-(self._window_size + 1) :]
        directions: list[Direction] = []
        prev_dir: Direction | None = None
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                prev_dir = Direction.UP
            elif prices[i] < prices[i - 1]:
                prev_dir = Direction.DOWN
            elif prev_dir is None:
                prev_dir = Direction.DOWN
            directions.append(prev_dir)

        counts = {
            (Direction.UP, Direction.UP): 0,
            (Direction.UP, Direction.DOWN): 0,
            (Direction.DOWN, Direction.UP): 0,
            (Direction.DOWN, Direction.DOWN): 0,
        }
        for i in range(1, len(directions)):
            counts[(directions[i - 1], directions[i])] += 1

        def rate(from_d: Direction, to_d: Direction) -> float:
            total = sum(
                counts[(from_d, d)] for d in (Direction.UP, Direction.DOWN)
            )
            if total == 0:
                return 0.5
            return counts[(from_d, to_d)] / total

        self._matrix = TransitionMatrix(
            p_up_up=rate(Direction.UP, Direction.UP),
            p_up_down=rate(Direction.UP, Direction.DOWN),
            p_down_up=rate(Direction.DOWN, Direction.UP),
            p_down_down=rate(Direction.DOWN, Direction.DOWN),
        ).normalized()
        self._last_direction = directions[-1] if directions else None
        self._last_computed_at = datetime.now(UTC).isoformat()
        persistence = compute_persistence(self._matrix)
        return MarkovSnapshot(
            computed_at_iso=self._last_computed_at,
            window_size=self._window_size,
            matrix=self._matrix,
            rolling_persistence=persistence,
            last_direction=self._last_direction,
        )

    def current_matrix(self) -> TransitionMatrix:
        return self._matrix.normalized()

    def rolling_persistence(self) -> float:
        return compute_persistence(self._matrix)

    def predict_next(self, current_direction: Direction) -> tuple[float, float]:
        """Return (P(UP), P(DOWN)) for next step from current direction."""

        m = self.current_matrix()
        if current_direction == Direction.UP:
            return m.p_up_up, m.p_up_down
        return m.p_down_up, m.p_down_down

    def snapshot(self) -> MarkovSnapshot:
        return MarkovSnapshot(
            computed_at_iso=self._last_computed_at or datetime.now(UTC).isoformat(),
            window_size=self._window_size,
            matrix=self.current_matrix(),
            rolling_persistence=self.rolling_persistence(),
            last_direction=self._last_direction,
        )
