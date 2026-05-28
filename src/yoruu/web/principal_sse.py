"""SSE payload builder for principal_changed (ch10 §10.5.3)."""

from __future__ import annotations

from typing import Any

from yoruu.execution.principal_service import PrincipalChangeResult


def build_principal_changed_payload(change: PrincipalChangeResult) -> dict[str, Any]:
    """Build validated SSE payload from a completed deposit/withdraw."""

    summary = change.summary
    return {
        "kind": change.kind,
        "amount": change.amount,
        "balance_before": change.balance_before,
        "balance_after": change.balance_after,
        "principal_before": change.principal_before,
        "principal_after": change.principal_after,
        "locked_principal": summary.locked_principal,
        "withdrawable_principal": summary.withdrawable_principal,
        "total_assets": summary.total_assets,
        "cumulative_pnl": summary.cumulative_pnl,
        "ts_utc": change.ts_utc,
        "note": change.note,
        "severity": "INFO",
    }
