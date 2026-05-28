"""FastAPI application factory (ch10 §10.6)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from yoruu.web.routes.api_v1 import router as api_v1_router

_STATIC_ROOT = Path(__file__).resolve().parent / "static"
_PAGES_DIR = _STATIC_ROOT / "pages"


def create_app() -> FastAPI:
    app = FastAPI(title="YoRuu API", version="0.4.0")
    app.include_router(api_v1_router)

    if _STATIC_ROOT.is_dir():
        app.mount("/static", StaticFiles(directory=_STATIC_ROOT), name="static")
    if _PAGES_DIR.is_dir():
        app.mount("/pages", StaticFiles(directory=_PAGES_DIR, html=True), name="pages")

        @app.get("/")
        def root() -> RedirectResponse:
            return RedirectResponse(url="/pages/index.html")

    return app


app = create_app()
