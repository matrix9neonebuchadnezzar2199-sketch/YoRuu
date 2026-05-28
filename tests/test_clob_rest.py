"""CLOB REST fixture tests (ch24 §24.9)."""

from pathlib import Path

import pytest

from yoruu.infra.clob_rest import ClobRestClient
from yoruu.infra.clob_types import LiveOrderRequest
from yoruu.types import Side


@pytest.mark.asyncio
async def test_clob_rest_fixture_balance() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "clob"
    client = ClobRestClient(fixture_dir=fixture_dir)
    balance = await client.get_balance_usdc()
    assert balance == 1000.0


@pytest.mark.asyncio
async def test_clob_rest_fixture_order() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "clob"
    client = ClobRestClient(fixture_dir=fixture_dir)
    result = await client.place_order(
        LiveOrderRequest(
            token_id="lab-token",
            side=Side.YES,
            price=0.62,
            size_usd=5.0,
        )
    )
    assert result.success is True
    assert result.order_id == "lab-order-001"
