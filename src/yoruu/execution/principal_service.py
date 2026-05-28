"""Principal deposit/withdraw (ch13 §13.2.6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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

    def deposit(self, amount: float, note: str | None = None) -> PrincipalSummary:
        if amount <= 0:
            raise PrincipalError("amount must be positive", code="E_PRINCIPAL_002")
        if amount > self._max_deposit:
            raise PrincipalError(
                f"deposit exceeds max {self._max_deposit}",
                code="E_PRINCIPAL_003",
                details={"amount": amount, "max": self._max_deposit},
            )
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
        return self.get_summary()

    def withdraw(
        self,
        amount: float,
        *,
        note: str | None = None,
        confirm: bool = False,
    ) -> PrincipalSummary:
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
        return self.get_summary()
