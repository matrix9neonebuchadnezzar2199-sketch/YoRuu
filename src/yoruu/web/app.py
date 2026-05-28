"""FastAPI application factory (ch10 §10.6)."""

from __future__ import annotations

from fastapi import FastAPI

from yoruu.web.routes.api_v1 import router as api_v1_router


def create_app() -> FastAPI:
    app = FastAPI(title="YoRuu API", version="0.3.0")
    app.include_router(api_v1_router)
    return app


app = create_app()
