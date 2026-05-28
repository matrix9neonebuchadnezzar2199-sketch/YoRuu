"""SSE principal_changed contract (M4.5)."""

from __future__ import annotations

from yoruu.api.sse.bus import ValidatingEventBus
from yoruu.api.sse.registry import validate_sse_payload
from yoruu.execution.principal_service import PrincipalChangeResult, PrincipalSummary
from yoruu.web.principal_sse import build_principal_changed_payload


def test_principal_changed_sse_payload() -> None:
    change = PrincipalChangeResult(
        summary=PrincipalSummary(
            principal=1050.0,
            balance=1042.0,
            locked_principal=8.0,
            withdrawable_principal=1042.0,
            total_assets=1050.0,
            cumulative_pnl=0.0,
        ),
        kind="DEPOSIT",
        amount=50.0,
        balance_before=992.0,
        balance_after=1042.0,
        principal_before=1000.0,
        principal_after=1050.0,
        note="lab",
        ts_utc="2026-05-28T05:30:00+00:00",
    )
    payload = build_principal_changed_payload(change)
    normalized = validate_sse_payload("principal_changed", payload)
    assert normalized["severity"] == "INFO"
    assert normalized["kind"] == "DEPOSIT"

    bus = ValidatingEventBus()
    bus.publish("principal_changed", payload)
