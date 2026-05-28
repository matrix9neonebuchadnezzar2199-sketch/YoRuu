"""SQLite access layer (ch10 §10.3)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from yoruu.data.schema import SCHEMA_SQL
from yoruu.errors import DatabaseNotInitializedError
from yoruu.types import Mode, State


class Database:
    """Thin SQLite wrapper; one connection per instance."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    @property
    def connection(self) -> sqlite3.Connection:
        """Underlying SQLite connection (migrations)."""

        return self._conn

    def close(self) -> None:
        self._conn.close()

    def has_column(self, table: str, column: str) -> bool:
        rows = self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(row[1] == column for row in rows)

    def commit(self) -> None:
        self._conn.commit()

    def initialize_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def ensure_bot_state(
        self,
        *,
        mode: Mode,
        balance: float,
        daily_loss_limit: float,
        strategy_version: int,
        principal: float | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        principal_value = balance if principal is None else principal
        row = self._conn.execute("SELECT id FROM bot_state WHERE id = 1").fetchone()
        if row is None:
            if self.has_column("bot_state", "principal"):
                self._conn.execute(
                    """
                    INSERT INTO bot_state (
                      id, state, mode, balance, principal, daily_pnl, daily_loss_limit,
                      ws_polymarket_connected, ws_binance_connected,
                      current_strategy_version, last_updated, started_at
                    ) VALUES (1, ?, ?, ?, ?, 0, ?, 0, 0, ?, ?, ?)
                    """,
                    (
                        State.INITIALIZING.value,
                        mode.value,
                        balance,
                        principal_value,
                        daily_loss_limit,
                        strategy_version,
                        now,
                        now,
                    ),
                )
            else:
                self._conn.execute(
                    """
                    INSERT INTO bot_state (
                      id, state, mode, balance, daily_pnl, daily_loss_limit,
                      ws_polymarket_connected, ws_binance_connected,
                      current_strategy_version, last_updated, started_at
                    ) VALUES (1, ?, ?, ?, 0, ?, 0, 0, ?, ?, ?)
                    """,
                    (
                        State.INITIALIZING.value,
                        mode.value,
                        balance,
                        daily_loss_limit,
                        strategy_version,
                        now,
                        now,
                    ),
                )
            self._conn.commit()
            self._seed_principal_bootstrap_if_needed(principal_value)

    def _seed_principal_bootstrap_if_needed(self, principal_value: float) -> None:
        """Initial DEPOSIT row so INV-D-07 holds for fresh bot_state (ch16)."""

        tables = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='principal_transactions'"
        ).fetchone()
        if tables is None:
            return
        row = self._conn.execute("SELECT COUNT(*) AS c FROM principal_transactions").fetchone()
        if row and int(row["c"]) > 0:
            return
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            """
            INSERT INTO principal_transactions (
              ts_utc, kind, amount, balance_before, balance_after,
              principal_before, principal_after, note
            ) VALUES (?, 'DEPOSIT', ?, ?, ?, 0, ?, ?)
            """,
            (
                now,
                principal_value,
                principal_value,
                principal_value,
                principal_value,
                "bootstrap:db_init",
            ),
        )
        self._conn.commit()

    def _require_bot_row(self) -> sqlite3.Row:
        row = self._conn.execute("SELECT * FROM bot_state WHERE id = 1").fetchone()
        if row is None:
            raise DatabaseNotInitializedError("bot_state not initialized")
        return row

    def get_state(self) -> State:
        row = self._require_bot_row()
        return State(row["state"])

    def set_state(self, state: State) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "UPDATE bot_state SET state = ?, last_updated = ? WHERE id = 1",
            (state.value, now),
        )
        self._conn.commit()

    def get_balance(self) -> float:
        row = self._require_bot_row()
        return float(row["balance"])

    def get_principal(self) -> float:
        row = self._require_bot_row()
        if "principal" not in row.keys():
            return float(row["balance"])
        value = row["principal"]
        if value is None:
            return float(row["balance"])
        return float(value)

    def update_balance_and_principal(self, balance: float, principal: float) -> None:
        now = datetime.now(UTC).isoformat()
        if self.has_column("bot_state", "principal"):
            self._conn.execute(
                """
                UPDATE bot_state SET balance = ?, principal = ?, last_updated = ? WHERE id = 1
                """,
                (balance, principal, now),
            )
        else:
            self._conn.execute(
                "UPDATE bot_state SET balance = ?, last_updated = ? WHERE id = 1",
                (balance, now),
            )

    def sum_principal_deposits(self) -> float:
        if not self.has_column("bot_state", "principal"):
            return 0.0
        tables = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='principal_transactions'"
        ).fetchone()
        if tables is None:
            return 0.0
        row = self._conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS s FROM principal_transactions
            WHERE kind = 'DEPOSIT'
            """
        ).fetchone()
        return float(row["s"]) if row else 0.0

    def sum_principal_withdrawals(self) -> float:
        tables = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='principal_transactions'"
        ).fetchone()
        if tables is None:
            return 0.0
        row = self._conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS s FROM principal_transactions
            WHERE kind = 'WITHDRAW'
            """
        ).fetchone()
        return float(row["s"]) if row else 0.0

    def count_principal_withdraw_violations(self) -> int:
        """Rows where WITHDRAW amount exceeded balance_before (INV-D-08)."""

        tables = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='principal_transactions'"
        ).fetchone()
        if tables is None:
            return 0
        row = self._conn.execute(
            """
            SELECT COUNT(*) AS c FROM principal_transactions
            WHERE kind = 'WITHDRAW' AND amount > balance_before + 0.0001
            """
        ).fetchone()
        return int(row["c"]) if row else 0

    def insert_principal_transaction(
        self,
        *,
        kind: str,
        amount: float,
        balance_before: float,
        balance_after: float,
        principal_before: float,
        principal_after: float,
        note: str | None = None,
        ts_utc: str | None = None,
    ) -> int:
        ts = ts_utc or datetime.now(UTC).isoformat()
        cur = self._conn.execute(
            """
            INSERT INTO principal_transactions (
              ts_utc, kind, amount, balance_before, balance_after,
              principal_before, principal_after, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                kind,
                amount,
                balance_before,
                balance_after,
                principal_before,
                principal_after,
                note,
            ),
        )
        return int(cur.lastrowid)

    def list_principal_transactions(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        kind: str | None = None,
        from_ts: str | None = None,
        to_ts: str | None = None,
    ) -> list[dict[str, Any]]:
        """List principal ledger rows (ch10 §10.6.12)."""

        if not self._has_principal_transactions_table():
            return []
        clauses: list[str] = []
        params: list[Any] = []
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind)
        if from_ts is not None:
            clauses.append("ts_utc >= ?")
            params.append(from_ts)
        if to_ts is not None:
            clauses.append("ts_utc <= ?")
            params.append(to_ts)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])
        rows = self._conn.execute(
            f"""
            SELECT * FROM principal_transactions
            {where}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def get_principal_transaction_stats(self) -> dict[str, int | str | None]:
        """Aggregate counts for GET /api/v1/principal."""

        if not self._has_principal_transactions_table():
            return {
                "deposit_count": 0,
                "withdraw_count": 0,
                "first_deposit_at": None,
                "last_transaction_at": None,
            }
        dep = self._conn.execute(
            "SELECT COUNT(*) AS c FROM principal_transactions WHERE kind = 'DEPOSIT'"
        ).fetchone()
        wit = self._conn.execute(
            "SELECT COUNT(*) AS c FROM principal_transactions WHERE kind = 'WITHDRAW'"
        ).fetchone()
        first = self._conn.execute(
            """
            SELECT ts_utc FROM principal_transactions
            WHERE kind = 'DEPOSIT'
            ORDER BY ts_utc ASC LIMIT 1
            """
        ).fetchone()
        last = self._conn.execute(
            "SELECT ts_utc FROM principal_transactions ORDER BY ts_utc DESC LIMIT 1"
        ).fetchone()
        return {
            "deposit_count": int(dep["c"]) if dep else 0,
            "withdraw_count": int(wit["c"]) if wit else 0,
            "first_deposit_at": str(first["ts_utc"]) if first else None,
            "last_transaction_at": str(last["ts_utc"]) if last else None,
        }

    def _has_principal_transactions_table(self) -> bool:
        row = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='principal_transactions'"
        ).fetchone()
        return row is not None

    def get_mode(self) -> Mode:
        row = self._require_bot_row()
        return Mode(row["mode"])

    def get_daily_loss_limit(self) -> float:
        row = self._require_bot_row()
        return float(row["daily_loss_limit"])

    def get_daily_pnl(self) -> float:
        row = self._conn.execute("SELECT daily_pnl FROM bot_state WHERE id = 1").fetchone()
        return float(row["daily_pnl"]) if row else 0.0

    def get_strategy_version(self) -> int:
        row = self._require_bot_row()
        return int(row["current_strategy_version"])

    def update_balance(self, balance: float) -> None:
        """Set balance only (open/close partial updates)."""

        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "UPDATE bot_state SET balance = ?, last_updated = ? WHERE id = 1",
            (balance, now),
        )

    def set_ws_connected(self, *, polymarket: bool | None = None, binance: bool | None = None) -> None:
        """Update WS connection flags on bot_state (ch10 §10.3)."""

        if polymarket is None and binance is None:
            return
        now = datetime.now(UTC).isoformat()
        if polymarket is not None and binance is not None:
            self._conn.execute(
                """
                UPDATE bot_state
                SET ws_polymarket_connected = ?, ws_binance_connected = ?, last_updated = ?
                WHERE id = 1
                """,
                (int(polymarket), int(binance), now),
            )
            return
        if polymarket is not None:
            self._conn.execute(
                """
                UPDATE bot_state
                SET ws_polymarket_connected = ?, last_updated = ?
                WHERE id = 1
                """,
                (int(polymarket), now),
            )
        if binance is not None:
            self._conn.execute(
                """
                UPDATE bot_state
                SET ws_binance_connected = ?, last_updated = ?
                WHERE id = 1
                """,
                (int(binance), now),
            )

    def update_balance_and_pnl(self, balance: float, daily_pnl: float) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "UPDATE bot_state SET balance = ?, daily_pnl = ?, last_updated = ? WHERE id = 1",
            (balance, daily_pnl, now),
        )
        self._conn.commit()

    def insert_price_tick(self, source: str, symbol: str, price: float, ts_iso: str) -> None:
        self._conn.execute(
            "INSERT INTO price_ticks (source, symbol, price, ts) VALUES (?, ?, ?, ?)",
            (source, symbol, price, ts_iso),
        )
        self._conn.commit()

    def insert_markov_snapshot(
        self,
        *,
        computed_at: str,
        window_size: int,
        matrix: dict[str, float],
        persistence: float,
        last_direction: str | None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO markov_state (
              computed_at, window_size, p_up_up, p_up_down, p_down_up, p_down_down,
              rolling_persistence, last_direction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                computed_at,
                window_size,
                matrix["p_up_up"],
                matrix["p_up_down"],
                matrix["p_down_up"],
                matrix["p_down_down"],
                persistence,
                last_direction,
            ),
        )
        self._conn.commit()

    def latest_markov_row(self) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM markov_state ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def markov_persistence_stats_24h(self) -> dict[str, float | None]:
        """Aggregate rolling_persistence over last 24h (ch15 §15.4.5)."""

        rows = self._conn.execute(
            """
            SELECT rolling_persistence FROM markov_state
            WHERE computed_at >= datetime('now', '-24 hours')
            ORDER BY computed_at
            """
        ).fetchall()
        if not rows:
            return {
                "avg_persistence_24h": None,
                "min_persistence_24h": None,
                "max_persistence_24h": None,
            }
        values = [float(r["rolling_persistence"]) for r in rows]
        return {
            "avg_persistence_24h": sum(values) / len(values),
            "min_persistence_24h": min(values),
            "max_persistence_24h": max(values),
        }

    def open_positions_total_size(self) -> float:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(size_usd), 0) AS total FROM positions WHERE status = 'OPEN'"
        ).fetchone()
        return float(row["total"]) if row else 0.0

    def count_open_positions(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS c FROM positions WHERE status = 'OPEN'"
        ).fetchone()
        return int(row["c"]) if row else 0

    def count_bot_state_rows(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS c FROM bot_state").fetchone()
        return int(row["c"]) if row else 0

    def count_open_positions_mode_mismatch(self, mode: Mode) -> int:
        row = self._conn.execute(
            """
            SELECT COUNT(*) AS c FROM positions p
            JOIN trades t ON t.id = p.trade_id
            WHERE p.status = 'OPEN' AND t.mode != ?
            """,
            (mode.value,),
        ).fetchone()
        return int(row["c"]) if row else 0

    def sum_closed_trade_pnl(self) -> float:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(pnl), 0) AS s FROM trades WHERE status = 'CLOSED'"
        ).fetchone()
        return float(row["s"]) if row else 0.0

    def sum_closed_trade_pnl_for_date(self, target_date: str) -> float:
        """Sum closed trade PnL for one calendar day (closed_at date, UTC)."""

        row = self._conn.execute(
            """
            SELECT COALESCE(SUM(pnl), 0) AS s FROM trades
            WHERE status = 'CLOSED'
              AND closed_at IS NOT NULL
              AND date(closed_at) = date(?)
            """,
            (target_date,),
        ).fetchone()
        return float(row["s"]) if row else 0.0

    def sum_closed_trade_pnl_today_utc(self) -> float:
        """Sum closed trade PnL for the current UTC calendar day."""

        row = self._conn.execute(
            """
            SELECT COALESCE(SUM(pnl), 0) AS s FROM trades
            WHERE status = 'CLOSED'
              AND closed_at IS NOT NULL
              AND date(closed_at) = date('now')
            """
        ).fetchone()
        return float(row["s"]) if row else 0.0

    def count_emergency_stops_last_24h_unrecovered(self) -> int:
        row = self._conn.execute(
            """
            SELECT COUNT(*) AS c FROM emergency_stops
            WHERE triggered_at >= datetime('now', '-24 hours')
              AND recovered_at IS NULL
            """
        ).fetchone()
        return int(row["c"]) if row else 0

    def insert_audit(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        resource_id: str | None,
        details: dict[str, Any] | None,
        result: str,
    ) -> None:
        ts = datetime.now(UTC).isoformat()
        self._conn.execute(
            """
            INSERT INTO audit_log (ts, actor, action, resource, resource_id, details_json, result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                actor,
                action,
                resource,
                resource_id,
                json.dumps(details or {}, ensure_ascii=False),
                result,
            ),
        )

    def fetch_trade(self, trade_id: int) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT entry_price, size_usd FROM trades WHERE id = ?",
            (trade_id,),
        ).fetchone()

    def insert_trade_open(
        self,
        *,
        market: str,
        side: str,
        size_usd: float,
        entry_price: float,
        mode: Mode,
        strategy_version: int,
        edge: float,
        persistence: float,
        opened_at: str,
        expires_at: str,
        markov_state_at_entry: str | None = None,
    ) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO trades (
              market, side, size_usd, entry_price, mode, strategy_version,
              markov_state_at_entry, edge_at_entry, persistence_at_entry,
              opened_at, expires_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """,
            (
                market,
                side,
                size_usd,
                entry_price,
                mode.value,
                strategy_version,
                markov_state_at_entry,
                edge,
                persistence,
                opened_at,
                expires_at,
            ),
        )
        trade_id = int(cur.lastrowid)
        self._conn.execute(
            """
            INSERT INTO positions (
              trade_id, market, side, size_usd, entry_price, opened_at, expires_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """,
            (trade_id, market, side, size_usd, entry_price, opened_at, expires_at),
        )
        return trade_id

    def close_trade(
        self,
        trade_id: int,
        *,
        exit_price: float,
        pnl: float,
        closed_at: str,
        status: str = "CLOSED",
    ) -> None:
        win = 1 if pnl > 0 else 0 if pnl < 0 else None
        self._conn.execute(
            """
            UPDATE trades SET exit_price = ?, pnl = ?, win = ?, closed_at = ?, status = ?
            WHERE id = ?
            """,
            (exit_price, pnl, win, closed_at, status, trade_id),
        )
        self._conn.execute("DELETE FROM positions WHERE trade_id = ?", (trade_id,))

    def trades_for_date(self, report_date: str, mode: Mode) -> list[sqlite3.Row]:
        return list(
            self._conn.execute(
                """
                SELECT * FROM trades
                WHERE date(opened_at) = date(?)
                  AND mode = ?
                """,
                (report_date, mode.value),
            )
        )

    def insert_daily_report(self, report_date: str, summary: dict[str, Any]) -> int:
        now = datetime.now(UTC).isoformat()
        cur = self._conn.execute(
            """
            INSERT INTO daily_reports (report_date, summary_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(report_date) DO UPDATE SET
              summary_json = excluded.summary_json,
              created_at = excluded.created_at
            """,
            (report_date, json.dumps(summary, ensure_ascii=False), now),
        )
        row = self._conn.execute(
            "SELECT id FROM daily_reports WHERE report_date = ?",
            (report_date,),
        ).fetchone()
        return int(row["id"]) if row else int(cur.lastrowid)

    def update_daily_report_proposed(
        self,
        report_date: str,
        proposed: dict[str, Any],
        *,
        applied_strategy_version: int | None = None,
    ) -> None:
        payload = json.dumps(proposed, ensure_ascii=False)
        if applied_strategy_version is not None:
            self._conn.execute(
                """
                UPDATE daily_reports
                SET proposed_strategy_json = ?, applied_strategy_version = ?
                WHERE report_date = ?
                """,
                (payload, applied_strategy_version, report_date),
            )
        else:
            self._conn.execute(
                """
                UPDATE daily_reports SET proposed_strategy_json = ?
                WHERE report_date = ?
                """,
                (payload, report_date),
            )

    def daily_report_id_for_date(self, report_date: str) -> int | None:
        row = self._conn.execute(
            "SELECT id FROM daily_reports WHERE report_date = ?",
            (report_date,),
        ).fetchone()
        return int(row["id"]) if row else None

    def ensure_strategy_version_seed(self, config_json: str, *, strategy_version: int) -> None:
        """Insert INITIAL strategy_versions row when table is empty (ch10 §10.3.9)."""

        row = self._conn.execute("SELECT COUNT(*) AS c FROM strategy_versions").fetchone()
        if row and int(row["c"]) == 0:
            self.insert_strategy_version(config_json, applied_by="INITIAL")
            self._conn.execute(
                "UPDATE bot_state SET current_strategy_version = ?, last_updated = ? WHERE id = 1",
                (strategy_version, datetime.now(UTC).isoformat()),
            )
            self._conn.commit()

    def fetch_strategy_version_row(self, version: int) -> Any | None:
        row = self._conn.execute(
            "SELECT * FROM strategy_versions WHERE version = ?",
            (version,),
        ).fetchone()
        return dict(row) if row else None

    def fetch_previous_strategy_version_row(self, before_version: int) -> Any | None:
        row = self._conn.execute(
            """
            SELECT * FROM strategy_versions
            WHERE version < ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (before_version,),
        ).fetchone()
        return dict(row) if row else None

    def insert_strategy_version(
        self,
        parameters_json: str,
        *,
        applied_by: str,
        performance_summary_json: str | None = None,
        rollback_reason: str | None = None,
    ) -> int:
        now = datetime.now(UTC).isoformat()
        cur = self._conn.execute(
            """
            INSERT INTO strategy_versions (
              parameters_json, applied_at, applied_by, performance_summary_json,
              rollback_reason
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (parameters_json, now, applied_by, performance_summary_json, rollback_reason),
        )
        version = int(cur.lastrowid)
        self._conn.execute(
            "UPDATE bot_state SET current_strategy_version = ?, last_updated = ? WHERE id = 1",
            (version, now),
        )
        return version
