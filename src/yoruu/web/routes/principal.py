"""Principal REST routes (ch10 §10.6.12)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from yoruu.api.sse.bus import ValidatingEventBus
from yoruu.data.database import Database
from yoruu.execution.principal_service import PrincipalChangeResult, PrincipalService
from yoruu.infra.fx_provider import FxRateProvider
from yoruu.web.deps import get_db, get_event_bus, get_fx_provider, get_principal_service
from yoruu.web.principal_sse import build_principal_changed_payload

router = APIRouter(prefix="/api/v1")


class DepositBody(BaseModel):
    amount: float = Field(gt=0)
    note: str | None = None


class WithdrawBody(BaseModel):
    amount: float = Field(gt=0)
    note: str | None = None
    confirm: bool = False


def _publish_principal_changed(
    bus: ValidatingEventBus,
    change: PrincipalChangeResult,
) -> None:
    bus.publish("principal_changed", build_principal_changed_payload(change))


@router.get("/principal")
def get_principal(
    service: PrincipalService = Depends(get_principal_service),
) -> dict[str, Any]:
    return service.get_detail()


@router.get("/principal/transactions")
def list_principal_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    kind: str | None = Query(None, pattern="^(DEPOSIT|WITHDRAW)$"),
    from_ts: str | None = Query(None, alias="from"),
    to_ts: str | None = Query(None, alias="to"),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    items = db.list_principal_transactions(
        limit=limit,
        offset=offset,
        kind=kind,
        from_ts=from_ts,
        to_ts=to_ts,
    )
    return {"items": items, "limit": limit, "offset": offset}


@router.post("/principal/deposit")
def post_principal_deposit(
    body: DepositBody,
    service: PrincipalService = Depends(get_principal_service),
    bus: ValidatingEventBus = Depends(get_event_bus),
) -> dict[str, Any]:
    change = service.deposit(body.amount, note=body.note)
    _publish_principal_changed(bus, change)
    return _change_response(change)


@router.post("/principal/withdraw")
def post_principal_withdraw(
    body: WithdrawBody,
    service: PrincipalService = Depends(get_principal_service),
    bus: ValidatingEventBus = Depends(get_event_bus),
) -> dict[str, Any]:
    change = service.withdraw(body.amount, note=body.note, confirm=body.confirm)
    _publish_principal_changed(bus, change)
    return _change_response(change)


def _change_response(change: PrincipalChangeResult) -> dict[str, Any]:
    summary = change.summary
    return {
        "kind": change.kind,
        "amount": change.amount,
        "principal": summary.principal,
        "balance": summary.balance,
        "locked_principal": summary.locked_principal,
        "withdrawable_principal": summary.withdrawable_principal,
        "total_assets": summary.total_assets,
        "cumulative_pnl": summary.cumulative_pnl,
        "ts_utc": change.ts_utc,
    }


@router.get("/fx/usd_jpy")
def get_fx_usd_jpy(
    provider: FxRateProvider = Depends(get_fx_provider),
) -> dict[str, Any]:
    quote = provider.get_usd_jpy()
    return {
        "pair": quote.pair,
        "rate": quote.rate,
        "fetched_at": quote.fetched_at,
        "source": quote.source,
        "stale": quote.stale,
    }
