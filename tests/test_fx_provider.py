"""FxRateProvider unit tests (M4.5)."""

from __future__ import annotations

import pytest

from yoruu.config.settings import DisplayFxSettings
from yoruu.errors import FxError
from yoruu.infra.fx_provider import FxRateProvider


def test_fx_disabled_raises() -> None:
    provider = FxRateProvider(DisplayFxSettings(enabled=False))
    with pytest.raises(FxError) as exc_info:
        provider.get_usd_jpy()
    assert exc_info.value.code == "E_FX_004"


def test_fx_unknown_provider() -> None:
    provider = FxRateProvider(DisplayFxSettings(provider="unknown_vendor"))
    with pytest.raises(FxError) as exc_info:
        provider.get_usd_jpy()
    assert exc_info.value.code == "E_FX_002"


def test_fx_fetch_live_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FxRateProvider(DisplayFxSettings())

    def fake_fetch(self: FxRateProvider):
        from yoruu.infra.fx_provider import FxRateQuote

        return FxRateQuote(
            pair="USD/JPY",
            rate=155.0,
            fetched_at="2026-05-28T00:00:00+00:00",
            source="exchangerate_host",
        )

    monkeypatch.setattr(FxRateProvider, "_fetch_live", fake_fetch)
    quote = provider.get_usd_jpy()
    assert quote.rate == 155.0
    assert quote.source == "exchangerate_host"


def test_fx_fallback_on_fetch_error(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FxRateProvider(DisplayFxSettings(fallback_rate=149.5))

    def fail_fetch(self: FxRateProvider):
        raise FxError("network down", code="E_FX_001")

    monkeypatch.setattr(FxRateProvider, "_fetch_live", fail_fetch)
    quote = provider.get_usd_jpy()
    assert quote.source == "fallback"
    assert quote.rate == 149.5
    assert quote.stale is True
