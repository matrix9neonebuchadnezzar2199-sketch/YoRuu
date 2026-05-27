"""SQLite DDL (ch10 §10.3)."""

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS bot_state (
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

CREATE TABLE IF NOT EXISTS trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market TEXT NOT NULL,
  side TEXT NOT NULL,
  size_usd REAL NOT NULL,
  entry_price REAL NOT NULL,
  exit_price REAL,
  pnl REAL,
  win INTEGER,
  mode TEXT NOT NULL,
  strategy_version INTEGER NOT NULL,
  markov_state_at_entry TEXT,
  edge_at_entry REAL,
  persistence_at_entry REAL,
  opened_at TEXT NOT NULL,
  closed_at TEXT,
  expires_at TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON trades(opened_at);

CREATE TABLE IF NOT EXISTS positions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_id INTEGER NOT NULL,
  market TEXT NOT NULL,
  side TEXT NOT NULL,
  size_usd REAL NOT NULL,
  entry_price REAL NOT NULL,
  current_price REAL,
  unrealized_pnl REAL,
  opened_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS markov_state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  computed_at TEXT NOT NULL,
  window_size INTEGER NOT NULL,
  p_up_up REAL NOT NULL,
  p_up_down REAL NOT NULL,
  p_down_up REAL NOT NULL,
  p_down_down REAL NOT NULL,
  rolling_persistence REAL NOT NULL,
  last_direction TEXT
);

CREATE TABLE IF NOT EXISTS price_ticks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  price REAL NOT NULL,
  ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  details_json TEXT,
  created_at TEXT NOT NULL,
  read INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS strategy_versions (
  version INTEGER PRIMARY KEY AUTOINCREMENT,
  parameters_json TEXT NOT NULL,
  applied_at TEXT NOT NULL,
  applied_by TEXT NOT NULL,
  rollback_reason TEXT,
  performance_summary_json TEXT
);

CREATE TABLE IF NOT EXISTS daily_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_date TEXT NOT NULL UNIQUE,
  summary_json TEXT NOT NULL,
  proposed_strategy_json TEXT,
  applied_strategy_version INTEGER,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS emergency_stops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  triggered_at TEXT NOT NULL,
  trigger TEXT NOT NULL,
  state_before TEXT NOT NULL,
  mode_before TEXT NOT NULL,
  open_positions_closed INTEGER NOT NULL DEFAULT 0,
  daily_pnl_at_stop REAL,
  recovered_at TEXT,
  recovered_to_mode TEXT,
  log_archive_path TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  resource TEXT NOT NULL,
  resource_id TEXT,
  details_json TEXT,
  result TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS what_if_scenarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  period_from TEXT NOT NULL,
  period_to TEXT NOT NULL,
  parameters_json TEXT NOT NULL,
  result_json TEXT,
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL DEFAULT 'USER',
  notes TEXT
);
"""
