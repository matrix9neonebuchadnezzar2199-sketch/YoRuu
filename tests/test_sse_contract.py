"""SSE contract tests (template 9 / B1 parity)."""

import pytest

from yoruu.api.sse.fixtures import LAB_SSE_FIXTURES
from yoruu.api.sse.format import format_sse_frame
from yoruu.api.sse.registry import SSE_EVENT_NAMES, SseContractError, validate_sse_payload


def test_all_lab_fixtures_validate() -> None:
    assert len(SSE_EVENT_NAMES) == 11
    for name in SSE_EVENT_NAMES:
        assert name in LAB_SSE_FIXTURES
        payload = validate_sse_payload(name, LAB_SSE_FIXTURES[name])
        assert isinstance(payload, dict)


def test_sse_frame_format() -> None:
    payload = validate_sse_payload("mode_changed", LAB_SSE_FIXTURES["mode_changed"])
    frame = format_sse_frame("mode_changed", payload)
    assert frame.startswith("event: mode_changed\n")
    assert '"from": "PAPER"' in frame or '"from":"PAPER"' in frame.replace(" ", "")


def test_invalid_event_rejected() -> None:
    with pytest.raises(SseContractError):
        validate_sse_payload("not_an_event", {})


def test_strategy_applied_requires_rationale() -> None:
    bad = dict(LAB_SSE_FIXTURES["strategy_applied"])
    del bad["rationale"]
    with pytest.raises(SseContractError):
        validate_sse_payload("strategy_applied", bad)
