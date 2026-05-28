"""PrincipalService deposit/withdraw (M4.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import init_db
from yoruu.errors import PrincipalError
from yoruu.execution.principal_service import PrincipalService
from yoruu.safety.invariants import InvariantChecker


def _service(db, **kwargs) -> PrincipalService:
    defaults = {
        "max_deposit_per_tx": 100_000.0,
        "max_withdraw_per_tx": 100_000.0,
        "require_confirm_on_withdraw": True,
        "invariant_checker": InvariantChecker(db, initial_principal=1000.0),
    }
    defaults.update(kwargs)
    return PrincipalService(db, **defaults)


def test_deposit_increases_balance_and_principal(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    svc = _service(db)
    summary = svc.deposit(100.0, note="lab")
    assert summary.principal == 1100.0  # 1000 bootstrap + 100 deposit
    assert summary.balance == 1100.0
    assert summary.withdrawable_principal == 1100.0


def test_withdraw_requires_confirm(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    svc = _service(db)
    with pytest.raises(PrincipalError) as exc_info:
        svc.withdraw(10.0, confirm=False)
    assert exc_info.value.code == "E_PRINCIPAL_004"


def test_withdraw_exceeds_balance(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    svc = _service(db)
    with pytest.raises(PrincipalError) as exc_info:
        svc.withdraw(2000.0, confirm=True)
    assert exc_info.value.code == "E_PRINCIPAL_001"


def test_withdraw_ok(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    svc = _service(db)
    svc.deposit(50.0)
    summary = svc.withdraw(25.0, confirm=True)
    assert summary.balance == 1025.0  # 1000 + 50 - 25
    assert summary.principal == 1025.0


def test_deposit_zero_rejected(tmp_path: Path) -> None:
    db = init_db(tmp_path)
    with pytest.raises(PrincipalError) as exc_info:
        _service(db).deposit(0)
    assert exc_info.value.code == "E_PRINCIPAL_002"
