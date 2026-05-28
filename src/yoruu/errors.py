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


class PrincipalError(YoRuuError):
    """Principal deposit/withdraw validation failed (ch18 E_PRINCIPAL_*)."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "E_PRINCIPAL_002",
        severity: str = "ERROR",
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.severity = severity


class FxError(YoRuuError):
    """FX rate fetch/validation failed (ch18 E_FX_*)."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "E_FX_001",
        severity: str = "WARN",
        details: dict | None = None,
    ) -> None:
        super().__init__(message, code=code, details=details)
        self.severity = severity


def http_status_for_error_code(code: str) -> int:
    """Map ch18 error codes to HTTP status (principal + FX)."""

    if code == "E_PRINCIPAL_005" or code == "E_FX_002":
        return 500
    if code in ("E_FX_001", "E_FX_004"):
        return 503
    if code == "E_FX_003":
        return 422
    if code.startswith("E_PRINCIPAL_") or code.startswith("E_FX_"):
        return 422
    return 400
