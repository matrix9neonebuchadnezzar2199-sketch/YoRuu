"""SQLite migrations for principal v1.2 (ch10 / ch22 §22.9)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from yoruu.data.database import Database


@dataclass(frozen=True)
class MigrationPlan:
    """Steps to run (dry-run reports only)."""

    add_principal_column: bool
    create_principal_transactions: bool
    backfill_principal_rows: int
    seed_migration_tx: bool


def plan_migration(db: Database) -> MigrationPlan:
    """Inspect DB and return pending migration steps."""

    conn = db.connection
    bot_cols = {row[1] for row in conn.execute("PRAGMA table_info(bot_state)")}
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    add_principal = "principal" not in bot_cols
    create_tx = "principal_transactions" not in tables
    backfill = 0
    if not add_principal:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM bot_state WHERE principal IS NULL OR principal = 0"
        ).fetchone()
        backfill = int(row["c"]) if row else 0
    seed = False
    if "principal_transactions" in tables:
        row = conn.execute("SELECT COUNT(*) AS c FROM principal_transactions").fetchone()
        seed = bool(row and int(row["c"]) == 0)
    elif create_tx:
        seed = True
    return MigrationPlan(
        add_principal_column=add_principal,
        create_principal_transactions=create_tx,
        backfill_principal_rows=backfill,
        seed_migration_tx=seed,
    )


def run_migration(
    db: Database,
    *,
    initial_principal: float,
    dry_run: bool = False,
) -> MigrationPlan:
    """Apply principal schema migration (ch22 §22.9)."""

    plan = plan_migration(db)
    if dry_run:
        return plan

    conn = db.connection
    if plan.add_principal_column:
        conn.execute("ALTER TABLE bot_state ADD COLUMN principal REAL")
    if plan.create_principal_transactions:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS principal_transactions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts_utc TEXT NOT NULL,
              kind TEXT NOT NULL CHECK (kind IN ('DEPOSIT', 'WITHDRAW')),
              amount REAL NOT NULL CHECK (amount > 0),
              balance_before REAL NOT NULL,
              balance_after REAL NOT NULL,
              principal_before REAL NOT NULL,
              principal_after REAL NOT NULL,
              note TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_principal_tx_ts ON principal_transactions(ts_utc);
            CREATE INDEX IF NOT EXISTS idx_principal_tx_kind ON principal_transactions(kind);
            """
        )

    row = conn.execute("SELECT balance FROM bot_state WHERE id = 1").fetchone()
    if row is not None:
        open_row = conn.execute(
            "SELECT COALESCE(SUM(size_usd), 0) AS total FROM positions WHERE status = 'OPEN'"
        ).fetchone()
        open_total = float(open_row["total"]) if open_row else 0.0
        balance = float(row["balance"])
        target_principal = balance + open_total
        conn.execute(
            """
            UPDATE bot_state
            SET principal = ?
            WHERE id = 1 AND (principal IS NULL OR principal = 0)
            """,
            (target_principal,),
        )

    tx_count_row = conn.execute("SELECT COUNT(*) AS c FROM principal_transactions").fetchone()
    tx_count = int(tx_count_row["c"]) if tx_count_row else 0
    if tx_count == 0:
        bot = conn.execute("SELECT balance, principal FROM bot_state WHERE id = 1").fetchone()
        if bot is not None:
            now = datetime.now(UTC).isoformat()
            principal_val = float(bot["principal"] or initial_principal)
            balance_val = float(bot["balance"])
            conn.execute(
                """
                INSERT INTO principal_transactions (
                  ts_utc, kind, amount, balance_before, balance_after,
                  principal_before, principal_after, note
                ) VALUES (?, 'DEPOSIT', ?, ?, ?, 0, ?, ?)
                """,
                (
                    now,
                    principal_val,
                    balance_val,
                    balance_val,
                    principal_val,
                    "migration:v1.2_initial",
                ),
            )

    conn.commit()
    return plan_migration(db)
