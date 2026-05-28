"""Principal deposit/withdraw (ch13 §13.2.6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from yoruu.data.database import Database
from yoruu.errors import InvariantViolationError, PrincipalError

if TYPE_CHECKING:
    from yoruu.safety.invariants import InvariantChecker


@dataclass(frozen=True)
class PrincipalSummary:
    """Derived principal snapshot for API/HUD (ch10 v1.2)."""

    principal: float
    balance: float
    locked_principal: float
    withdrawable_principal: float
    total_assets: float
    cumulative_pnl: float


@dataclass(frozen=True)
class PrincipalChangeResult:
    """Deposit/withdraw outcome for API and SSE (ch10 §10.5.3)."""

    summary: PrincipalSummary
    kind: Literal["DEPOSIT", "WITHDRAW"]
    amount: float
    balance_before: float
    balance_after: float
    principal_before: float
    principal_after: float
    note: str | None
    ts_utc: str


class PrincipalService:
    """Manage principal deposits and withdrawals (D11 v2)."""

    def __init__(
        self,
        db: Database,
        *,
        max_deposit_per_tx: float,
        max_withdraw_per_tx: float,
        require_confirm_on_withdraw: bool = True,
        invariant_checker: InvariantChecker | None = None,
    ) -> None:
        self._db = db
        self._max_deposit = max_deposit_per_tx
        self._max_withdraw = max_withdraw_per_tx
        self._require_confirm = require_confirm_on_withdraw
        self._invariants = invariant_checker

    def get_summary(self) -> PrincipalSummary:
        balance = self._db.get_balance()
        principal = self._db.get_principal()
        locked = self._db.open_positions_total_size()
        total_assets = balance + locked
        return PrincipalSummary(
            principal=principal,
            balance=balance,
            locked_principal=locked,
            withdrawable_principal=balance,
            total_assets=total_assets,
            cumulative_pnl=total_assets - principal,
        )

    def get_detail(self) -> dict[str, float | int | str | None]:
        """GET /api/v1/principal response (ch10 §10.6.12)."""

        summary = self.get_summary()
        stats = self._db.get_principal_transaction_stats()
        return {
            "principal": summary.principal,
            "balance": summary.balance,
            "locked_principal": summary.locked_principal,
            "withdrawable_principal": summary.withdrawable_principal,
            "total_assets": summary.total_assets,
            "cumulative_pnl": summary.cumulative_pnl,
            **stats,
        }

    def deposit(self, amount: float, note: str | None = None) -> PrincipalChangeResult:
        if amount <= 0:
            raise PrincipalError("amount must be positive", code="E_PRINCIPAL_002")
        if amount > self._max_deposit:
            raise PrincipalError(
                f"deposit exceeds max {self._max_deposit}",
                code="E_PRINCIPAL_003",
                details={"amount": amount, "max": self._max_deposit},
            )
        ts_utc = datetime.now(UTC).isoformat()
        try:
            with self._db.transaction():
                balance_before = self._db.get_balance()
                principal_before = self._db.get_principal()
                balance_after = balance_before + amount
                principal_after = principal_before + amount
                self._db.update_balance_and_principal(balance_after, principal_after)
                self._db.insert_principal_transaction(
                    kind="DEPOSIT",
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    principal_before=principal_before,
                    principal_after=principal_after,
                    note=note,
                    ts_utc=ts_utc,
                )
                self._db.insert_audit(
                    actor="USER",
                    action="PRINCIPAL_DEPOSIT",
                    resource="principal",
                    resource_id=None,
                    details={"amount": amount, "note": note},
                    result="SUCCESS",
                )
        except (PrincipalError, InvariantViolationError):
            raise
        except Exception as exc:
            raise PrincipalError(
                "principal deposit failed",
                code="E_PRINCIPAL_005",
                details={"reason": str(exc)},
            ) from exc
        if self._invariants is not None:
            self._invariants.check_post_principal_change()
        summary = self.get_summary()
        return PrincipalChangeResult(
            summary=summary,
            kind="DEPOSIT",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            principal_before=principal_before,
            principal_after=principal_after,
            note=note,
            ts_utc=ts_utc,
        )

    def withdraw(
        self,
        amount: float,
        *,
        note: str | None = None,
        confirm: bool = False,
    ) -> PrincipalChangeResult:
        if not confirm and self._require_confirm:
            raise PrincipalError(
                "withdraw requires confirm=true",
                code="E_PRINCIPAL_004",
            )
        if amount <= 0:
            raise PrincipalError("amount must be positive", code="E_PRINCIPAL_002")
        if amount > self._max_withdraw:
            raise PrincipalError(
                f"withdraw exceeds max {self._max_withdraw}",
                code="E_PRINCIPAL_006",
                details={"amount": amount, "max": self._max_withdraw},
            )
        balance_before = self._db.get_balance()
        if amount > balance_before:
            raise PrincipalError(
                "withdraw exceeds withdrawable balance",
                code="E_PRINCIPAL_001",
                details={"amount": amount, "balance": balance_before},
            )
        ts_utc = datetime.now(UTC).isoformat()
        try:
            with self._db.transaction():
                principal_before = self._db.get_principal()
                balance_after = balance_before - amount
                principal_after = principal_before - amount
                self._db.update_balance_and_principal(balance_after, principal_after)
                self._db.insert_principal_transaction(
                    kind="WITHDRAW",
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    principal_before=principal_before,
                    principal_after=principal_after,
                    note=note,
                    ts_utc=ts_utc,
                )
                self._db.insert_audit(
                    actor="USER",
                    action="PRINCIPAL_WITHDRAW",
                    resource="principal",
                    resource_id=None,
                    details={"amount": amount, "note": note},
                    result="SUCCESS",
                )
        except (PrincipalError, InvariantViolationError):
            raise
        except Exception as exc:
            raise PrincipalError(
                "principal withdraw failed",
                code="E_PRINCIPAL_005",
                details={"reason": str(exc)},
            ) from exc
        if self._invariants is not None:
            self._invariants.check_post_principal_change()
        summary = self.get_summary()
        return PrincipalChangeResult(
            summary=summary,
            kind="WITHDRAW",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            principal_before=principal_before,
            principal_after=principal_after,
            note=note,
            ts_utc=ts_utc,
        )
