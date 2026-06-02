"""FastAPI application factory (ch10 §10.6)."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from yoruu.errors import FxError, PrincipalError, http_status_for_error_code
from yoruu.web.deps import get_settings, shutdown_trading_loop, start_trading_loop
from yoruu.web.routes.api_v1 import router as api_v1_router
from yoruu.web.routes.principal import router as principal_router

logger = logging.getLogger(__name__)

_STATIC_ROOT = Path(__file__).resolve().parent / "static"
_PAGES_DIR = _STATIC_ROOT / "pages"


def _error_response(exc: PrincipalError | FxError) -> JSONResponse:
    return JSONResponse(
        status_code=http_status_for_error_code(exc.code),
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "details": exc.details,
            }
        },
    )


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Start TradingLoop alongside API (PHASE 6 M6.2 案 A)."""

    settings = get_settings()
    with_loop = bool(getattr(app.state, "with_trading_loop", True))
    task: asyncio.Task | None = None
    if with_loop:
        task = await start_trading_loop(settings)
    try:
        yield
    finally:
        await shutdown_trading_loop(task)


def create_app(*, with_trading_loop: bool = True) -> FastAPI:
    app = FastAPI(title="YoRuu API", version="0.7.0", lifespan=_lifespan)
    app.state.with_trading_loop = with_trading_loop
    app.include_router(api_v1_router)
    app.include_router(principal_router)

    @app.exception_handler(PrincipalError)
    async def principal_error_handler(
        _request: Request, exc: PrincipalError
    ) -> JSONResponse:
        return _error_response(exc)

    @app.exception_handler(FxError)
    async def fx_error_handler(_request: Request, exc: FxError) -> JSONResponse:
        return _error_response(exc)

    if _STATIC_ROOT.is_dir():
        app.mount("/static", StaticFiles(directory=_STATIC_ROOT), name="static")
    if _PAGES_DIR.is_dir():
        app.mount("/pages", StaticFiles(directory=_PAGES_DIR, html=True), name="pages")

        @app.get("/")
        def root() -> RedirectResponse:
            return RedirectResponse(url="/pages/00_hud.html")

    return app


app = create_app()
