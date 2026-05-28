"""CLOB DTOs (ch24 §24.8)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from yoruu.types import Side


@dataclass(frozen=True)
class LiveOrderRequest:
    token_id: str
    side: Side
    price: float
    size_usd: float
    order_type: Literal["LIMIT", "MARKET"] = "LIMIT"


@dataclass(frozen=True)
class LiveOrderResult:
    success: bool
    order_id: str | None
    message: str
    error_code: str | None = None
