"""SSE wire format helpers."""

from __future__ import annotations

import json
from typing import Any


def format_sse_frame(event: str, payload: dict[str, Any]) -> str:
    """Format one SSE message (payload only in data line, per B1 mock)."""

    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"
