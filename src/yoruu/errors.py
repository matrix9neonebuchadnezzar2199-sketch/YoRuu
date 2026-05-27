"""YoRuu domain exceptions (ch18)."""

from __future__ import annotations


class YoRuuError(Exception):
    """Base exception for YoRuu."""

    code: str = "E_YORUU_000"

    def __init__(self, message: str, *, code: str | None = None, details: dict | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code
        self.details = details or {}


class StateViolationError(YoRuuError):
    """Invalid state transition or disallowed operation in current state."""

    code = "E_STATE_001"


class ConfigValidationError(YoRuuError):
    """Configuration file validation failed."""

    code = "E_SETTINGS_001"


class DatabaseNotInitializedError(YoRuuError):
    """bot_state or required DB row missing."""

    code = "E_DB_001"


class InvariantViolationError(YoRuuError):
    """Runtime invariant check failed (ch16)."""

    def __init__(
        self,
        message: str,
        *,
        inv_id: str,
        severity: str = "ERROR",
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code=f"E_INV_{inv_id.replace('-', '_')}", details=details)
        self.inv_id = inv_id
        self.severity = severity


class StrategyApplyError(YoRuuError):
    """Strategy apply validation or persistence failed."""

    code = "E_NIGHTLY_007"
