"""Infra / WS / CLOB stack unit tests (lab, no live network)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from helpers import init_db
from yoruu.config.settings import WebSocketSettings
from yoruu.execution.live_executor import LiveExecutor
from yoruu.infra.binance_ws import BinanceMarketWs
from yoruu.infra.clob_rest import ClobRestClient
from yoruu.infra.clob_types import LiveOrderRequest
from yoruu.infra.clob_ws import ClobWsClient
from yoruu.infra import market_runner
from yoruu.infra.polymarket_clob import PolymarketClient
from yoruu.infra.polymarket_ws import PolymarketMarketWs
from yoruu.infra.ws_client import AsyncWsClient
from yoruu.types import OrderBook, Side


def _ws_settings() -> WebSocketSettings:
    return WebSocketSettings(
        polymarket_url="wss://example.invalid/p",
        binance_url="wss://example.invalid/b",
        reconnect_interval_sec=1,
        max_reconnect_attempts=2,
        stale_tick_sec=30,
    )


@pytest.mark.asyncio
async def test_async_ws_client_stale_and_connect_idempotent() -> None:
    async def on_msg(payload: dict) -> None:
        del payload

    client = AsyncWsClient(
        name="unit",
        url="wss://example.invalid/ws",
        settings=_ws_settings(),
        on_message=on_msg,
    )
    assert client.name == "unit"
    assert client.is_stale
    assert not client.is_connected

    async def fake_run_loop(self: AsyncWsClient) -> None:
        self._state.connected = True
        await self._stop.wait()

    with patch.object(AsyncWsClient, "_run_loop", fake_run_loop):
        await client.connect()
        await asyncio.sleep(0)
        await client.connect()
        assert client.is_connected
        await client.disconnect()
        assert not client.is_connected


@pytest.mark.asyncio
async def test_clob_ws_client_fill_handler() -> None:
    fills: list[dict] = []

    async def on_fill(payload: dict) -> None:
        fills.append(payload)

    clob_ws = ClobWsClient(_ws_settings(), on_fill=on_fill)
    await clob_ws._handle_message({"type": "fill", "order_id": "x"})
    assert fills[0]["order_id"] == "x"


@pytest.mark.asyncio
async def test_polymarket_client_from_settings_fixture(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "clob"
    client = PolymarketClient.from_settings(
        _ws_settings(),
        fixture_dir=fixture_dir,
    )
    with patch.object(client._ws, "connect", new_callable=AsyncMock):
        await client.connect()
    balance = await client.get_balance_usdc()
    assert balance == 1000.0
    assert client.is_ws_stale()
    result = await client.place_order(
        LiveOrderRequest(token_id="t", side=Side.YES, price=0.5, size_usd=1.0)
    )
    assert result.success
    with patch.object(client._ws, "disconnect", new_callable=AsyncMock):
        await client.close()


@pytest.mark.asyncio
async def test_live_executor_blocks_on_stale_ws() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "clob"
    client = PolymarketClient.from_settings(_ws_settings(), fixture_dir=fixture_dir)
    executor = LiveExecutor(client)
    result = await executor.open(
        LiveOrderRequest(token_id="t", side=Side.YES, price=0.5, size_usd=1.0)
    )
    assert result.success is False
    assert result.error_code == "E_WS_001"
    with patch.object(client, "close", new_callable=AsyncMock):
        await executor.close()


@pytest.mark.asyncio
async def test_market_runner_short_run(tmp_path: Path) -> None:
    from yoruu.config.settings import load_settings

    cfg = tmp_path / "yoruu.yaml"
    cfg.write_text(
        """
mode: PAPER
initial_balance: 1000.0
currency: USD
market:
  id: BTC_5MIN
  source: POLYMARKET
  binance_symbol: BTCUSDT
risk:
  max_trade_size_usd: 10.0
  daily_loss_limit_usd: 30.0
  emergency_stop_enabled: true
  consecutive_fail_limit: 3
  consecutive_fail_window_min: 15
websocket:
  polymarket_url: wss://example.invalid/p
  binance_url: wss://example.invalid/b
  reconnect_interval_sec: 5
  max_reconnect_attempts: 1
  stale_tick_sec: 30
nightly_review:
  enabled: false
  send_time: "04:00"
  timezone: Asia/Tokyo
  pause_trading_during_review: false
paths:
  db: {db}
  strategy: {strategy}
  logs: {logs}
  historical: {hist}
  reports: {reports}
paper:
  slippage_coeff: 0.0001
  slippage_max: 0.02
  latency_ms_mean: 80
  latency_ms_std: 20
""".format(
            db=(tmp_path / "yoruu.db").as_posix(),
            strategy=(tmp_path / "strategy.json").as_posix(),
            logs=(tmp_path / "logs").as_posix(),
            hist=(tmp_path / "hist").as_posix(),
            reports=(tmp_path / "reports").as_posix(),
        ).strip(),
        encoding="utf-8",
    )
    (tmp_path / "strategy.json").write_text('{"version":1,"parameters":{}}', encoding="utf-8")

    settings = load_settings(cfg)
    db = init_db(tmp_path, balance=1000.0)

    class _StubFeed:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def connect(self) -> None:
            return None

        async def disconnect(self) -> None:
            return None

    with (
        patch.object(market_runner, "BinanceMarketWs", _StubFeed),
        patch.object(market_runner, "PolymarketMarketWs", _StubFeed),
    ):
        await market_runner.run_market_feeds(settings, db, duration_sec=0.01)


@pytest.mark.asyncio
async def test_binance_ws_db_tick(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    ws = BinanceMarketWs(_ws_settings(), db=db)
    with patch.object(ws._client, "connect", new_callable=AsyncMock):
        await ws.connect()
    await ws._handle_message({"price": "42000"})
    with patch.object(ws._client, "disconnect", new_callable=AsyncMock):
        await ws.disconnect()
    row = db._conn.execute(
        "SELECT COUNT(*) AS c FROM price_ticks WHERE source = 'BINANCE'"
    ).fetchone()
    assert row["c"] == 1
    db.close()


@pytest.mark.asyncio
async def test_polymarket_ws_book_and_price(tmp_path: Path) -> None:
    books: list[OrderBook] = []

    async def on_book(book: OrderBook) -> None:
        books.append(book)

    db = init_db(tmp_path)
    ws = PolymarketMarketWs(_ws_settings(), market_id="M1", db=db, on_book=on_book)
    await ws._handle_message({"price": "0.55"})
    await ws._handle_message(
        {"bids": [["0.54", "100"]], "asks": [["0.56", "120"]]}
    )
    assert len(books) == 1
    assert books[0].best_bid == pytest.approx(0.54)
    db.close()


@pytest.mark.asyncio
async def test_clob_rest_http_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/order"):
            return httpx.Response(200, json={"order_id": "http-1"})
        if request.method == "DELETE":
            return httpx.Response(204)
        if request.url.path.endswith("/balance"):
            return httpx.Response(200, json={"balance": 42.5})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs.setdefault("transport", transport)
        kwargs.setdefault("timeout", 5.0)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    client = ClobRestClient(base_url="https://clob.lab.invalid")
    bal = await client.get_balance_usdc()
    assert bal == 42.5
    ok = await client.cancel_order("ord-1")
    assert ok is True
    result = await client.place_order(
        LiveOrderRequest(token_id="t", side=Side.NO, price=0.4, size_usd=2.0)
    )
    assert result.success and result.order_id == "http-1"

    def fail_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="server error")

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *a, **kw: real_client(transport=httpx.MockTransport(fail_handler)),
    )
    bad = await client.place_order(
        LiveOrderRequest(token_id="t", side=Side.YES, price=0.5, size_usd=1.0)
    )
    assert bad.success is False
    assert bad.error_code == "E_LIVE_003"
