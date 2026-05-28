"""USD/JPY FX rate provider with cache and fallback (ch22 §22.2.3)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from yoruu.config.settings import DisplayFxSettings
from yoruu.errors import FxError

ALLOWED_FX_PROVIDERS = frozenset({"exchangerate_host"})
EXCHANGERATE_HOST_URL = "https://api.exchangerate.host/latest"


@dataclass(frozen=True)
class FxRateQuote:
    """Normalized FX response for GET /api/v1/fx/usd_jpy."""

    pair: str
    rate: float
    fetched_at: str
    source: str
    stale: bool = False


class FxRateProvider:
    """Fetch and cache USD/JPY; lab uses exchangerate.host (no API key)."""

    def __init__(self, settings: DisplayFxSettings) -> None:
        self._settings = settings
        self._cache_rate: float | None = None
        self._cache_fetched_at: str | None = None
        self._cache_monotonic: float = 0.0

    def get_usd_jpy(self) -> FxRateQuote:
        if not self._settings.enabled:
            raise FxError(
                "display.fx.enabled is false",
                code="E_FX_004",
                severity="WARN",
            )
        if self._settings.provider not in ALLOWED_FX_PROVIDERS:
            raise FxError(
                f"unknown fx provider: {self._settings.provider}",
                code="E_FX_002",
                severity="ERROR",
            )

        now_mono = time.monotonic()
        if (
            self._cache_rate is not None
            and self._cache_fetched_at is not None
            and (now_mono - self._cache_monotonic) < self._settings.cache_ttl_sec
        ):
            stale = (now_mono - self._cache_monotonic) >= self._settings.stale_after_sec
            return FxRateQuote(
                pair="USD/JPY",
                rate=self._cache_rate,
                fetched_at=self._cache_fetched_at,
                source="cache",
                stale=stale,
            )

        try:
            quote = self._fetch_live()
            self._cache_rate = quote.rate
            self._cache_fetched_at = quote.fetched_at
            self._cache_monotonic = now_mono
            return quote
        except (FxError, Exception) as exc:
            return self._cached_or_fallback(now_mono, reason=str(exc))

    def _fetch_live(self) -> FxRateQuote:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    EXCHANGERATE_HOST_URL,
                    params={"base": "USD", "symbols": "JPY"},
                )
                resp.raise_for_status()
                payload: Any = resp.json()
        except httpx.HTTPError as exc:
            raise FxError(
                "FX HTTP request failed",
                code="E_FX_001",
                severity="WARN",
                details={"reason": str(exc)},
            ) from exc

        try:
            rates = payload["rates"]
            rate = float(rates["JPY"])
        except (KeyError, TypeError, ValueError) as exc:
            raise FxError(
                "FX response parse failed",
                code="E_FX_003",
                severity="WARN",
                details={"reason": str(exc)},
            ) from exc

        fetched_at = datetime.now(UTC).isoformat()
        return FxRateQuote(
            pair="USD/JPY",
            rate=rate,
            fetched_at=fetched_at,
            source="exchangerate_host",
            stale=False,
        )

    def _cached_or_fallback(self, now_mono: float, *, reason: str) -> FxRateQuote | None:
        if self._cache_rate is not None and self._cache_fetched_at is not None:
            return FxRateQuote(
                pair="USD/JPY",
                rate=self._cache_rate,
                fetched_at=self._cache_fetched_at,
                source="cache",
                stale=True,
            )
        return FxRateQuote(
            pair="USD/JPY",
            rate=self._settings.fallback_rate,
            fetched_at=datetime.now(UTC).isoformat(),
            source="fallback",
            stale=True,
        )
