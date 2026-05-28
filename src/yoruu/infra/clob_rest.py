"""Polymarket CLOB REST client (ch24 §24.2)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx

from yoruu.infra.clob_types import LiveOrderRequest, LiveOrderResult

logger = logging.getLogger(__name__)


class ClobRestClient:
    """HTTP client for CLOB REST. Lab: use offline fixtures or explicit base URL."""

    def __init__(
        self,
        *,
        base_url: str = "https://clob.lab.invalid",
        fixture_dir: Path | None = None,
        timeout_sec: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._fixture_dir = fixture_dir
        self._timeout = timeout_sec

    async def place_order(self, req: LiveOrderRequest) -> LiveOrderResult:
        if self._fixture_dir is not None:
            return self._fixture_order(req)
        return await self._http_place_order(req)

    async def cancel_order(self, order_id: str) -> bool:
        if self._fixture_dir is not None:
            return True
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.delete(f"{self._base_url}/order/{order_id}")
            return resp.status_code < 400

    async def get_balance_usdc(self) -> float:
        if self._fixture_dir is not None:
            path = self._fixture_dir / "balance.json"
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
                return float(data.get("balance", 0.0))
            return 1000.0
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base_url}/balance")
            resp.raise_for_status()
            data = resp.json()
            return float(data.get("balance", 0.0))

    def _fixture_order(self, req: LiveOrderRequest) -> LiveOrderResult:
        return LiveOrderResult(
            success=True,
            order_id="lab-order-001",
            message="fixture accept",
        )

    async def _http_place_order(self, req: LiveOrderRequest) -> LiveOrderResult:
        body: dict[str, Any] = {
            "token_id": req.token_id,
            "side": req.side.value,
            "price": req.price,
            "size_usd": req.size_usd,
            "order_type": req.order_type,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._base_url}/order", json=body)
                if resp.status_code >= 400:
                    return LiveOrderResult(
                        success=False,
                        order_id=None,
                        message=resp.text,
                        error_code="E_LIVE_003",
                    )
                data = resp.json()
                return LiveOrderResult(
                    success=True,
                    order_id=str(data.get("order_id", "unknown")),
                    message="accepted",
                )
        except httpx.HTTPError as exc:
            logger.warning("clob rest error: %s", exc)
            return LiveOrderResult(
                success=False,
                order_id=None,
                message=str(exc),
                error_code="E_LIVE_002",
            )
