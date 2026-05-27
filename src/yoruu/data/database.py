"""SQLite access layer (ch10 §10.3)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from yoruu.data.schema import SCHEMA_SQL
from yoruu.types import Mode, State


class Database:
    """Thin SQLite wrapper; one connection per instance."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self._conn.close()

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
    ) -> None:
        now = datetime.now(UTC).isoformat()
        row = self._conn.execute("SELECT id FROM bot_state WHERE id = 1").fetchone()
        if row is None:
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

    def get_state(self) -> State:
        row = self._conn.execute("SELECT state FROM bot_state WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError("bot_state not initialized")
        return State(row["state"])

    def set_state(self, state: State) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "UPDATE bot_state SET state = ?, last_updated = ? WHERE id = 1",
            (state.value, now),
        )
        self._conn.commit()

    def get_balance(self) -> float:
        row = self._conn.execute("SELECT balance FROM bot_state WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError("bot_state not initialized")
        return float(row["balance"])

    def get_mode(self) -> Mode:
        row = self._conn.execute("SELECT mode FROM bot_state WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError("bot_state not initialized")
        return Mode(row["mode"])

    def get_daily_pnl(self) -> float:
        row = self._conn.execute("SELECT daily_pnl FROM bot_state WHERE id = 1").fetchone()
        return float(row["daily_pnl"]) if row else 0.0

    def get_strategy_version(self) -> int:
        row = self._conn.execute(
            "SELECT current_strategy_version FROM bot_state WHERE id = 1"
        ).fetchone()
        if row is None:
            raise RuntimeError("bot_state not initialized")
        return int(row["current_strategy_version"])

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
    ) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO trades (
              market, side, size_usd, entry_price, mode, strategy_version,
              edge_at_entry, persistence_at_entry, opened_at, expires_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """,
            (
                market,
                side,
                size_usd,
                entry_price,
                mode.value,
                strategy_version,
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

    def insert_daily_report(self, report_date: str, summary: dict[str, Any]) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            """
            INSERT INTO daily_reports (report_date, summary_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(report_date) DO UPDATE SET
              summary_json = excluded.summary_json,
              created_at = excluded.created_at
            """,
            (report_date, json.dumps(summary, ensure_ascii=False), now),
        )

    def insert_strategy_version(
        self,
        parameters_json: str,
        *,
        applied_by: str,
    ) -> int:
        now = datetime.now(UTC).isoformat()
        cur = self._conn.execute(
            """
            INSERT INTO strategy_versions (parameters_json, applied_at, applied_by)
            VALUES (?, ?, ?)
            """,
            (parameters_json, now, applied_by),
        )
        version = int(cur.lastrowid)
        self._conn.execute(
            "UPDATE bot_state SET current_strategy_version = ?, last_updated = ? WHERE id = 1",
            (version, now),
        )
        return version
