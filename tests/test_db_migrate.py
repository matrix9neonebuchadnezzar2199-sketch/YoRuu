"""yoruu db migrate (ch22 §22.9)."""

from __future__ import annotations

from pathlib import Path

from yoruu.data.database import Database
from yoruu.data.migrate import plan_migration, run_migration


def _legacy_db(path: Path) -> Database:
    db = Database(path)
    db.connection.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE bot_state (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          state TEXT NOT NULL,
          mode TEXT NOT NULL,
          balance REAL NOT NULL,
          daily_pnl REAL NOT NULL DEFAULT 0,
          daily_loss_limit REAL NOT NULL,
          ws_polymarket_connected INTEGER NOT NULL DEFAULT 0,
          ws_binance_connected INTEGER NOT NULL DEFAULT 0,
          current_strategy_version INTEGER NOT NULL,
          last_updated TEXT NOT NULL,
          started_at TEXT NOT NULL
        );
        """
    )
    now = "2026-05-28T00:00:00+00:00"
    db.connection.execute(
        """
        INSERT INTO bot_state (
          id, state, mode, balance, daily_pnl, daily_loss_limit,
          ws_polymarket_connected, ws_binance_connected,
          current_strategy_version, last_updated, started_at
        ) VALUES (1, 'IDLE', 'PAPER', 990, 0, 30, 0, 0, 1, ?, ?)
        """,
        (now, now),
    )
    db.connection.execute(
        """
        CREATE TABLE positions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          trade_id INTEGER NOT NULL,
          market TEXT NOT NULL,
          side TEXT NOT NULL,
          size_usd REAL NOT NULL,
          entry_price REAL NOT NULL,
          opened_at TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          status TEXT NOT NULL
        )
        """
    )
    db.connection.execute(
        """
        INSERT INTO positions (
          trade_id, market, side, size_usd, entry_price, opened_at, expires_at, status
        ) VALUES (1, 'BTC_5MIN_UPDOWN', 'YES', 10, 0.5, ?, ?, 'OPEN')
        """,
        (now, now),
    )
    db.connection.commit()
    return db


def test_migrate_adds_principal_and_seed_tx(tmp_path: Path) -> None:
    db = _legacy_db(tmp_path / "legacy.sqlite")
    plan = plan_migration(db)
    assert plan.add_principal_column is True
    assert plan.create_principal_transactions is True

    run_migration(db, initial_principal=1000.0, dry_run=False)
    assert db.has_column("bot_state", "principal")
    assert db.get_principal() == 1000.0
    row = db.connection.execute(
        "SELECT note FROM principal_transactions LIMIT 1"
    ).fetchone()
    assert row is not None
    assert row["note"] == "migration:v1.2_initial"
    db.close()
