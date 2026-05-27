"""Markov engine tests."""

import pytest

from yoruu.strategy.markov import MarkovEngine, compute_persistence
from yoruu.types import TransitionMatrix


def test_compute_persistence_alpha() -> None:
    matrix = TransitionMatrix(0.58, 0.42, 0.39, 0.61).normalized()
    assert compute_persistence(matrix) == pytest.approx(0.58, rel=1e-2)


def test_markov_recompute_on_rising_closes() -> None:
    engine = MarkovEngine(window_size=5)
    price = 100.0
    snap = None
    for _ in range(6):
        snap = engine.add_close(price)
        price += 1.0
    assert snap is not None
    assert snap.rolling_persistence >= 0.5
    assert snap.last_direction is not None
