"""Shared enums and value types (ch10/ch11/ch13)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class State(StrEnum):
    """Bot lifecycle state (ch10 §10.7.2)."""

    INITIALIZING = "INITIALIZING"
    IDLE = "IDLE"
    TRADING = "TRADING"
    MONITORING_POSITION = "MONITORING_POSITION"
    NIGHTLY_REVIEW = "NIGHTLY_REVIEW"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"
    BACKTEST = "BACKTEST"


class Mode(StrEnum):
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    SIMMER = "SIMMER"
    LIVE = "LIVE"


class Side(StrEnum):
    YES = "YES"
    NO = "NO"


class Direction(StrEnum):
    UP = "UP"
    DOWN = "DOWN"


class CloseReason(StrEnum):
    EXPIRATION = "EXPIRATION"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    MANUAL = "MANUAL"
    SYSTEM_INVARIANT = "SYSTEM_INVARIANT"


WaitReason = Literal[
    "persistence",
    "edge",
    "prob",
    "liquidity",
    "risk_budget",
]


@dataclass(frozen=True)
class TransitionMatrix:
    p_up_up: float
    p_up_down: float
    p_down_up: float
    p_down_down: float

    def normalized(self) -> TransitionMatrix:
        """Row-normalize with neutral 0.5/0.5 when denominator is zero (ch11 §11.3.3)."""

        def row(a: float, b: float) -> tuple[float, float]:
            total = a + b
            if total <= 0:
                return 0.5, 0.5
            return a / total, b / total

        uu, ud = row(self.p_up_up, self.p_up_down)
        du, dd = row(self.p_down_up, self.p_down_down)
        return TransitionMatrix(p_up_up=uu, p_up_down=ud, p_down_up=du, p_down_down=dd)


@dataclass(frozen=True)
class Prediction:
    direction: Direction
    prob_up: float
    prob_down: float


@dataclass(frozen=True)
class PriceTick:
    source: Literal["BINANCE", "POLYMARKET"]
    symbol: str
    price: float
    ts_iso: str


@dataclass(frozen=True)
class OrderBook:
    market: str
    best_bid: float
    best_ask: float
    bid_size_usd: float
    ask_size_usd: float
    spread: float
    captured_at_iso: str
    source: Literal["WS", "BACKTEST_HISTORY", "FALLBACK", "MOCK"] = "MOCK"

    @property
    def spread_ok(self) -> bool:
        return self.spread <= 0.05


@dataclass(frozen=True)
class MarketState:
    order_book_yes: OrderBook
    order_book_no: OrderBook | None = None


@dataclass(frozen=True)
class ErrorPayload:
    code: str
    message: str
    severity: Literal["INFO", "WARN", "ERROR"]
    details: dict


@dataclass(frozen=True)
class EvaluationResult:
    should_enter: bool
    side: Side | None
    size_usd: float
    edge: float
    persistence: float
    predicted_prob: float
    market_price: float
    reason: str
    wait_reason: WaitReason | None = None


@dataclass(frozen=True)
class RiskCheckResult:
    ok: bool
    reason: str | None = None


@dataclass(frozen=True)
class TradeSignal:
    side: Side
    size_usd: float
    edge: float
    persistence: float
    predicted_prob: float
    market_price: float
