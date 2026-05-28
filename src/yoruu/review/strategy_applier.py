"""Strategy apply sequence (ch15 §15.8)."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from yoruu.core.event_bus import EventBus, NoOpEventBus
from yoruu.core.state_machine import StateMachine
from yoruu.data.database import Database
from yoruu.errors import StrategyApplyError
from yoruu.review.apply_validator import ApplyValidationResult, ApplyValidator
from yoruu.review.strategy_writer import StrategyWriter
from yoruu.strategy.models import StrategyConfig
from yoruu.types import State

_apply_lock = threading.Lock()


@dataclass(frozen=True)
class ApplyResult:
    new_version: int
    previous_version: int
    applied_by: str
    diff: dict[str, tuple[float, float]]


class StrategyApplier:
    """§15.8 apply: validate, backup, DB transaction, strategy.json atomic write."""

    def __init__(
        self,
        db: Database,
        writer: StrategyWriter,
        *,
        event_bus: EventBus | None = None,
        history_dir: Path | None = None,
    ) -> None:
        self._db = db
        self._writer = writer
        self._event_bus = event_bus or NoOpEventBus()
        self._history_dir = history_dir or writer._path.parent / "strategy_history"
        self._validator = ApplyValidator()

    def apply(
        self,
        proposal: dict[str, Any],
        current: StrategyConfig,
        *,
        state_machine: StateMachine | None = None,
        report_date: str | None = None,
    ) -> ApplyResult:
        if not _apply_lock.acquire(blocking=False):
            raise StrategyApplyError(
                "concurrent strategy apply",
                code="E_NIGHTLY_013",
            )
        try:
            return self._apply_locked(
                proposal,
                current,
                state_machine=state_machine,
                report_date=report_date,
            )
        finally:
            _apply_lock.release()

    def _apply_locked(
        self,
        proposal: dict[str, Any],
        current: StrategyConfig,
        *,
        state_machine: StateMachine | None,
        report_date: str | None,
    ) -> ApplyResult:
        validation = self._validator.validate_or_raise(proposal, current)
        assert validation.normalized_parameters is not None

        sm = state_machine
        if sm is not None:
            sm.require_state(State.NIGHTLY_REVIEW, State.IDLE)

        new_config = self._validator.build_strategy_config(
            current,
            validation.normalized_parameters,
            applied_by=validation.applied_by,
        )

        diff = {
            key: (float(current.parameters.model_dump()[key]), float(validation.normalized_parameters[key]))
            for key in validation.normalized_parameters
            if current.parameters.model_dump()[key] != validation.normalized_parameters[key]
        }

        performance_summary = json.dumps(
            {
                "source_report_id": validation.source_report_id,
                "rationale": validation.rationale,
                "previous_version": current.version,
            },
            ensure_ascii=False,
        )

        self._history_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self._history_dir / f"strategy_v{current.version}.json"
        if self._writer._path.exists():
            backup_path.write_text(
                self._writer._path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        else:
            try:
                backup_path.write_text(
                    json.dumps(current.to_json_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except OSError as exc:
                raise StrategyApplyError(
                    "backup write failed",
                    code="E_NIGHTLY_011",
                    details={"error": str(exc)},
                ) from exc

        try:
            with self._db.transaction():
                version = self._db.insert_strategy_version(
                    json.dumps(new_config.to_json_dict(), ensure_ascii=False),
                    applied_by=validation.applied_by,
                    performance_summary_json=performance_summary,
                )
                new_config = new_config.model_copy(update={"version": version})
                payload = json.dumps(new_config.to_json_dict(), ensure_ascii=False)
                self._db.insert_audit(
                    actor=validation.applied_by,
                    action="STRATEGY_APPLY",
                    resource="strategy_versions",
                    resource_id=str(version),
                    details={
                        "previous_version": current.version,
                        "new_version": version,
                        "source_report_id": validation.source_report_id,
                        "diff": [
                            {"key": k, "old": o, "new": n} for k, (o, n) in diff.items()
                        ],
                        "rationale": validation.rationale,
                    },
                    result="SUCCESS",
                )
                if report_date:
                    self._db.update_daily_report_proposed(
                        report_date,
                        proposal,
                        applied_strategy_version=version,
                    )
            self._writer.apply(new_config)
        except StrategyApplyError:
            raise
        except OSError as exc:
            raise StrategyApplyError(
                "strategy.json write failed",
                code="E_NIGHTLY_011",
                details={"error": str(exc)},
            ) from exc
        except Exception as exc:
            raise StrategyApplyError(
                "strategy apply transaction failed",
                code="E_NIGHTLY_010",
                details={"error": str(exc)},
            ) from exc

        if sm is not None and sm.current() == State.NIGHTLY_REVIEW:
            sm.transition(State.IDLE, "strategy apply complete", actor=validation.applied_by)

        applied_at = datetime.now(UTC).isoformat()
        self._event_bus.publish(
            "strategy_applied",
            {
                "new_version": new_config.version,
                "previous_version": current.version,
                "applied_by": validation.applied_by,
                "rationale": validation.rationale or "",
                "applied_at": applied_at,
                "diff": {k: [o, n] for k, (o, n) in diff.items()},
            },
        )

        return ApplyResult(
            new_version=new_config.version,
            previous_version=current.version,
            applied_by=validation.applied_by,
            diff=diff,
        )

    def rollback(
        self,
        current: StrategyConfig,
        *,
        reason: str = "API rollback",
        state_machine: StateMachine | None = None,
    ) -> ApplyResult:
        """Restore previous strategy_versions row (applied_by=ROLLBACK)."""

        if not _apply_lock.acquire(blocking=False):
            raise StrategyApplyError(
                "concurrent strategy apply",
                code="E_NIGHTLY_013",
            )
        try:
            if state_machine is not None:
                state_machine.require_state(State.NIGHTLY_REVIEW, State.IDLE)

            current_db_version = self._db.get_strategy_version()
            prev_row = self._db.fetch_previous_strategy_version_row(current_db_version)
            if prev_row is None:
                raise StrategyApplyError(
                    "no previous strategy version",
                    code="E_NIGHTLY_012",
                )

            prev_config = StrategyConfig.from_json_dict(
                json.loads(prev_row["parameters_json"])
            )
            diff = {
                key: (
                    float(current.parameters.model_dump()[key]),
                    float(prev_config.parameters.model_dump()[key]),
                )
                for key in prev_config.parameters.model_dump()
                if current.parameters.model_dump()[key]
                != prev_config.parameters.model_dump()[key]
            }

            self._history_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self._history_dir / f"strategy_v{current.version}.json"
            if self._writer._path.exists():
                backup_path.write_text(
                    self._writer._path.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

            performance_summary = json.dumps(
                {"rollback_reason": reason, "restored_from": int(prev_row["version"])},
                ensure_ascii=False,
            )

            with self._db.transaction():
                version = self._db.insert_strategy_version(
                    json.dumps(prev_config.to_json_dict(), ensure_ascii=False),
                    applied_by="ROLLBACK",
                    performance_summary_json=performance_summary,
                    rollback_reason=reason,
                )
                restored = prev_config.model_copy(update={"version": version})
                self._db.insert_audit(
                    actor="USER",
                    action="STRATEGY_ROLLBACK",
                    resource="strategy_versions",
                    resource_id=str(version),
                    details={
                        "previous_version": current_db_version,
                        "restored_from": int(prev_row["version"]),
                        "reason": reason,
                    },
                    result="SUCCESS",
                )
            self._writer.apply(restored)

            applied_at = datetime.now(UTC).isoformat()
            self._event_bus.publish(
                "strategy_applied",
                {
                    "new_version": version,
                    "previous_version": current_db_version,
                    "applied_by": "ROLLBACK",
                    "rationale": reason,
                    "applied_at": applied_at,
                    "diff": {k: [o, n] for k, (o, n) in diff.items()},
                },
            )

            return ApplyResult(
                new_version=version,
                previous_version=current_db_version,
                applied_by="ROLLBACK",
                diff=diff,
            )
        finally:
            _apply_lock.release()
