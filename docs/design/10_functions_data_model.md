# 第10章 関数・データモデル

- **バージョン**: v1.0.1
- **作成日**: 2026-05-27
- **最終更新**: 2026-05-27（v1.0.1: §10.3.11〜13 テーブル追加、§10.7.2 State 注記）
- **ステータス**: APPROVED
- **関連章**: 2（アーキテクチャ）, 4（データフロー）, 6（シーケンス）, 7（I/O 図）, 11（戦略ロジック）, 12（モード仕様）, 13（ペーパー約定）, 14（i18n）, 15（夜間レビュー）, 18（エラーハンドリング）, 19（キルスイッチ）
- **旧章統合**: 旧 ch11「Data Model」を §10.3（SQLite）／§10.4（`strategy.json`）に統合

## 10.1 目的・スコープ

### 10.1.1 目的

YoRuu の関数シグネチャ、REST API エンドポイント、SSE ペイロード、SQLite スキーマ、設定ファイル構造を **単一の真実（SSOT）** として確定する。PHASE 3（コア実装）と PHASE 4（UI 実装）の双方で参照される。

### 10.1.2 スコープ（含む）

- REST API エンドポイント一覧と JSON スキーマ（§10.2）
- SSE イベントと JSON ペイロード（§10.5）
- SQLite テーブル定義 11 件（§10.3）
- 設定ファイル `strategy.json`・`yoruu.yaml` の完全スキーマ（§10.4）
- 主要内部関数シグネチャ（§10.7〜§10.11、Part 2）
- データライフサイクル・保持期間（§10.12、Part 2）

### 10.1.3 スコープ外

- 戦略アルゴリズム実装詳細（→ 第11章）
- ペーパー約定エンジン内部（→ 第13章）
- 夜間レポートのプロンプト・LLM 連携（→ 第15章）
- HTML/CSS/JavaScript 実装（→ PHASE 2/4）
- インフラ・デプロイ（→ 第22章）

### 10.1.4 命名規約

- **関数**: `snake_case`（Python）
- **クラス**: `PascalCase`
- **定数**: `UPPER_SNAKE_CASE`
- **REST パス**: `/api/v1/<resource>`、複数形リソース
- **SSE イベント**: `snake_case`
- **DB テーブル**: 複数形 `snake_case`（例: `trades`, `bot_state`）
- **DB カラム**: `snake_case`
- **JSON キー**: `snake_case`

## 10.2 REST API 概要

### 10.2.1 ベース URL とバージョニング

- ベース: `http://127.0.0.1:8765/api/v1`
- ローカルバインドのみ（SSH トンネル前提、第5章 §5.2）
- バージョニングは URL パスに埋込（v1）、破壊的変更時に v2 を切る

### 10.2.2 共通レスポンス形式

成功:
```json
{
  "ok": true,
  "data": { ... },
  "meta": { "timestamp": "2026-05-27T14:32:48+09:00", "version": "v1" }
}
```

失敗:
```json
{
  "ok": false,
  "error": {
    "code": "E_ORDER_004",
    "message": "Insufficient liquidity",
    "severity": "ERROR",
    "details": { "market": "BTC_5MIN_UPDOWN", "side": "YES" }
  },
  "meta": { "timestamp": "2026-05-27T14:32:48+09:00", "version": "v1" }
}
```

エラーコード体系は第18章で定義。`severity` は `INFO|WARN|ERROR` の 3 種。

### 10.2.3 共通 HTTP ステータス

| コード | 用途 |
|-------|------|
| 200 | 成功（GET/POST 共通） |
| 201 | リソース作成成功（戦略バージョン追加等） |
| 400 | 入力バリデーション失敗 |
| 404 | リソース不在 |
| 409 | 状態競合（例: LIVE 中のモード変更） |
| 422 | スキーマ不整合（必須キー欠落等） |
| 500 | 内部エラー |
| 503 | 依存サービス停止（WebSocket 切断等） |

### 10.2.4 認証

- 認証なし（単一ユーザー、SSH トンネル前提、第5章 §5.2.3）
- 緊急停止のみ `X-Confirm-Stop: true` ヘッダ不要（ボタン直接発火、§9.8）
- 復帰のみ POST ボディの `confirm: true` を要求（§10.2.10）

## 10.3 SQLite テーブル定義（旧 ch11 統合）

### 10.3.1 DB ファイル

- パス: `data/yoruu.db`（`yoruu.yaml` で上書き可能）
- 形式: SQLite 3.40+、WAL モード有効
- バックアップ: 毎日 04:00 JST に `data/backup/yoruu_<YYYYMMDD>.db` へコピー（30 日保持）

### 10.3.2 テーブル一覧

| # | テーブル | 用途 | 保持期間 |
|---|---------|------|---------|
| 1 | `bot_state` | 現在状態 1 行のみ | 永続 |
| 2 | `trades` | 約定履歴 | 永続 |
| 3 | `positions` | オープン中ポジション | 永続（決済後 `trades` に追記） |
| 4 | `markov_state` | 直近 N 本のキャッシュ | 24 時間 |
| 5 | `price_ticks` | 価格ティック生データ | 7 日 |
| 6 | `alerts` | アラート履歴 | 90 日 |
| 7 | `strategy_versions` | 戦略パラメータ履歴 | 永続 |
| 8 | `daily_reports` | 夜間レポート | 永続 |
| 9 | `emergency_stops` | 緊急停止履歴 | 永続 |
| 10 | `audit_log` | 監査ログ | 永続 |
| 11 | `what_if_scenarios` | What-If シナリオ保存 | 永続（ユーザー削除可） |

### 10.3.3 `bot_state` テーブル

```sql
CREATE TABLE bot_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  state TEXT NOT NULL CHECK (state IN (
    'INITIALIZING', 'IDLE', 'TRADING', 'MONITORING_POSITION',
    'NIGHTLY_REVIEW', 'EMERGENCY_STOP', 'ERROR', 'SHUTDOWN', 'BACKTEST'
  )),
  mode TEXT NOT NULL CHECK (mode IN ('BACKTEST', 'PAPER', 'SIMMER', 'LIVE')),
  balance REAL NOT NULL,
  daily_pnl REAL NOT NULL DEFAULT 0,
  daily_loss_limit REAL NOT NULL,
  ws_polymarket_connected INTEGER NOT NULL DEFAULT 0,
  ws_binance_connected INTEGER NOT NULL DEFAULT 0,
  current_strategy_version INTEGER NOT NULL,
  last_updated TEXT NOT NULL,
  started_at TEXT NOT NULL
);
```

シングルトン制約（`id = 1`）により 1 行のみ。`state` は第3章 §3.1 の 9 状態に加え補助状態（`ERROR` / `SHUTDOWN` / `BACKTEST`）を含む（§10.7.2 注記参照）。

### 10.3.4 `trades` テーブル

```sql
CREATE TABLE trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('YES', 'NO')),
  size_usd REAL NOT NULL,
  entry_price REAL NOT NULL,
  exit_price REAL,
  pnl REAL,
  win INTEGER CHECK (win IN (0, 1, NULL)),
  mode TEXT NOT NULL CHECK (mode IN ('PAPER', 'SIMMER', 'LIVE')),
  strategy_version INTEGER NOT NULL,
  markov_state_at_entry TEXT,
  edge_at_entry REAL,
  persistence_at_entry REAL,
  opened_at TEXT NOT NULL,
  closed_at TEXT,
  expires_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('OPEN', 'CLOSED', 'EXPIRED', 'CANCELLED'))
);
CREATE INDEX idx_trades_opened_at ON trades(opened_at);
CREATE INDEX idx_trades_mode_status ON trades(mode, status);
```

### 10.3.5 `positions` テーブル

```sql
CREATE TABLE positions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_id INTEGER NOT NULL REFERENCES trades(id),
  market TEXT NOT NULL,
  side TEXT NOT NULL,
  size_usd REAL NOT NULL,
  entry_price REAL NOT NULL,
  current_price REAL,
  unrealized_pnl REAL,
  opened_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('OPEN', 'CLOSING'))
);
```

決済成立時に `trades.exit_price`/`pnl`/`closed_at`/`status='CLOSED'` を更新し、`positions` から削除。

### 10.3.6 `markov_state` テーブル

```sql
CREATE TABLE markov_state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  computed_at TEXT NOT NULL,
  window_size INTEGER NOT NULL,
  p_up_up REAL NOT NULL,
  p_up_down REAL NOT NULL,
  p_down_up REAL NOT NULL,
  p_down_down REAL NOT NULL,
  rolling_persistence REAL NOT NULL,
  last_direction TEXT CHECK (last_direction IN ('UP', 'DOWN', NULL))
);
CREATE INDEX idx_markov_computed_at ON markov_state(computed_at);
```

5 分ごとに新行追加、24 時間超は cron で削除。

### 10.3.7 `price_ticks` テーブル

```sql
CREATE TABLE price_ticks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL CHECK (source IN ('BINANCE', 'POLYMARKET')),
  symbol TEXT NOT NULL,
  price REAL NOT NULL,
  ts TEXT NOT NULL
);
CREATE INDEX idx_price_ticks_source_ts ON price_ticks(source, ts);
```

7 日経過で cron 削除。バックテスト時は別ファイル `data/historical/` から読込。

### 10.3.8 `alerts` テーブル

```sql
CREATE TABLE alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('INFO', 'WARN', 'ERROR')),
  message TEXT NOT NULL,
  details_json TEXT,
  created_at TEXT NOT NULL,
  read INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
```

### 10.3.9 `strategy_versions` テーブル

```sql
CREATE TABLE strategy_versions (
  version INTEGER PRIMARY KEY AUTOINCREMENT,
  parameters_json TEXT NOT NULL,
  applied_at TEXT NOT NULL,
  applied_by TEXT NOT NULL CHECK (applied_by IN ('USER', 'NIGHTLY_REVIEW', 'ROLLBACK', 'INITIAL')),
  rollback_reason TEXT,
  performance_summary_json TEXT
);
```

`parameters_json` は §10.4 の `strategy.json` 全体。

### 10.3.10 `daily_reports` テーブル

```sql
CREATE TABLE daily_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_date TEXT NOT NULL UNIQUE,
  summary_json TEXT NOT NULL,
  proposed_strategy_json TEXT,
  applied_strategy_version INTEGER REFERENCES strategy_versions(version),
  created_at TEXT NOT NULL
);
```

### 10.3.11 `emergency_stops` テーブル

```sql
CREATE TABLE emergency_stops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  triggered_at TEXT NOT NULL,
  trigger TEXT NOT NULL CHECK (trigger IN (
    'dashboard_button', 'sidebar_button', 'command_palette',
    'keyboard_shortcut', 'api_call', 'system_invariant'
  )),
  state_before TEXT NOT NULL,
  mode_before TEXT NOT NULL,
  open_positions_closed INTEGER NOT NULL DEFAULT 0,
  daily_pnl_at_stop REAL,
  recovered_at TEXT,
  recovered_to_mode TEXT,
  log_archive_path TEXT
);
CREATE INDEX idx_emergency_stops_triggered_at ON emergency_stops(triggered_at);
```

ch9 §9.8.7 の「ログ zip ダウンロード」「復帰履歴」「トリガ別集計」に対応。`emergency_stop_triggered` SSE 発火時にレコード作成、`emergency/recover` 時に `recovered_at` を更新。

### 10.3.12 `audit_log` テーブル

```sql
CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL CHECK (actor IN ('USER', 'SYSTEM', 'NIGHTLY_REVIEW', 'SCHEDULER')),
  action TEXT NOT NULL,
  resource TEXT NOT NULL,
  resource_id TEXT,
  details_json TEXT,
  result TEXT NOT NULL CHECK (result IN ('SUCCESS', 'FAILURE', 'PARTIAL'))
);
CREATE INDEX idx_audit_log_ts ON audit_log(ts);
CREATE INDEX idx_audit_log_resource ON audit_log(resource, resource_id);
```

監査対象: モード切替、戦略 Apply/Rollback、設定変更、緊急停止、復帰、手動ポジションクローズ。保持期間は永続（§10.12.1）。

### 10.3.13 `what_if_scenarios` テーブル

```sql
CREATE TABLE what_if_scenarios (
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
CREATE INDEX idx_what_if_scenarios_created_at ON what_if_scenarios(created_at);
```

§8.21 / §10.6.9 の「シナリオ保存」に対応。PHASE 2 では空テーブルでモック対応可。

## 10.4 設定ファイルスキーマ（旧 ch11 統合）

### 10.4.1 `strategy.json` 完全スキーマ

```json
{
  "version": 3,
  "parameters": {
    "MIN_PROB": 0.87,
    "MIN_EDGE": 0.06,
    "KELLY_FRACTION": 0.65,
    "PERSISTENCE_THRESHOLD": 0.72
  },
  "constraints": {
    "MIN_PROB": { "min": 0.80, "max": 0.95 },
    "MIN_EDGE": { "min": 0.03, "max": 0.15 },
    "KELLY_FRACTION": { "min": 0.10, "max": 1.00 },
    "PERSISTENCE_THRESHOLD": { "min": 0.50, "max": 0.90 }
  },
  "metadata": {
    "applied_at": "2026-05-26T04:15:00+09:00",
    "applied_by": "NIGHTLY_REVIEW",
    "previous_version": 2
  }
}
```

範囲外は §10.6 のバリデーションで拒否。範囲・推奨値は第7章 §7.2 と第11章 §11.4 と同期。

### 10.4.2 `yoruu.yaml` 完全スキーマ

```yaml
mode: PAPER  # BACKTEST | PAPER | SIMMER | LIVE
initial_balance: 1000.0
currency: USD

market:
  id: BTC_5MIN_UPDOWN
  source: POLYMARKET
  binance_symbol: BTCUSDT

risk:
  max_trade_size_usd: 10.0
  daily_loss_limit_usd: 30.0
  emergency_stop_enabled: true

websocket:
  polymarket_url: wss://ws-subscriptions-clob.polymarket.com/ws/
  binance_url: wss://stream.binance.com:9443/ws/btcusdt@trade
  reconnect_interval_sec: 5
  max_reconnect_attempts: 10

nightly_review:
  enabled: true
  send_time: "04:00"
  timezone: Asia/Tokyo
  pause_trading_during_review: true

paths:
  db: data/yoruu.db
  strategy: config/strategy.json
  logs: logs/
  historical: data/historical/

ui:
  bind_host: 127.0.0.1
  port: 8765
  default_language: ja  # ja | en

logging:
  level: INFO
  rotate_mb: 50
  retain_days: 30
```

### 10.4.3 設定変更の反映タイミング

| キー | 即時反映 | 再起動必須 |
|------|--------|----------|
| `mode` | – | ✓ |
| `initial_balance` | – | ✓ |
| `market.*` | – | ✓ |
| `risk.*` | ✓ | – |
| `websocket.*` | – | ✓ |
| `nightly_review.*` | ✓ | – |
| `ui.default_language` | ✓ | – |
| `logging.*` | ✓ | – |

`strategy.json` は常に即時反映（次回エントリー判定から有効）。

## 10.5 SSE イベント仕様

### 10.5.1 エンドポイント

- パス: `GET /api/v1/events/stream`
- Content-Type: `text/event-stream`
- 再接続: クライアント側で 3 秒後リトライ、`Last-Event-ID` で再開
- ハートビート: 15 秒ごとに `:keepalive` コメント送信

### 10.5.2 イベント一覧（11 件）

第8章 §8.9 と同期。

| # | イベント名 | 用途 | 発火頻度 |
|---|----------|------|---------|
| 1 | `state_changed` | 状態遷移 | 状態変化時 |
| 2 | `markov_update` | Markov 更新 | 5 分ごと |
| 3 | `health_degraded` | WS 切断等 | 異常検知時 |
| 4 | `health_recovered` | 復旧 | 正常復帰時 |
| 5 | `position_opened` | 新規約定 | 約定時 |
| 6 | `position_closed` | 決済 | 決済時 |
| 7 | `nightly_report_ready` | 夜間レポ生成 | 04:00 JST |
| 8 | `mode_changed` | モード切替 | モード変更時 |
| 9 | `emergency_stop_triggered` | 緊急停止 | ボタン押下時 |
| 10 | `alert_added` | アラート発生 | 都度 |
| 11 | `strategy_applied` | 戦略適用 | Apply 時 |

### 10.5.3 ペイロード例

**`state_changed`**:
```
event: state_changed
data: {"from":"TRADING","to":"MONITORING_POSITION","timestamp":"2026-05-27T14:32:48+09:00","reason":"position_opened"}
```

**`markov_update`**:
```
event: markov_update
data: {
  "computed_at": "2026-05-27T14:35:00+09:00",
  "window_size": 20,
  "matrix": {"p_up_up":0.578,"p_up_down":0.422,"p_down_up":0.388,"p_down_down":0.612},
  "rolling_persistence": 0.595,
  "last_direction": "UP",
  "threshold_met": false
}
```

**`health_degraded`**:
```
event: health_degraded
data: {"component":"polymarket_ws","reason":"disconnected","retry_count":2,"timestamp":"2026-05-27T14:32:48+09:00"}
```

**`position_opened`**:
```
event: position_opened
data: {
  "trade_id": 71,
  "market": "BTC_5MIN_UPDOWN",
  "side": "YES",
  "size_usd": 7.10,
  "entry_price": 0.62,
  "expires_at": "2026-05-27T14:37:00+09:00",
  "edge_at_entry": 0.071,
  "persistence_at_entry": 0.72
}
```

**`position_closed`**:
```
event: position_closed
data: {
  "trade_id": 71,
  "exit_price": 1.00,
  "pnl": 4.35,
  "win": true,
  "closed_at": "2026-05-27T14:37:00+09:00"
}
```

**`nightly_report_ready`**:
```
event: nightly_report_ready
data: {"report_date":"2026-05-27","report_id":7,"summary_url":"/api/v1/reports/7"}
```

**`mode_changed`**:
```
event: mode_changed
data: {"from":"PAPER","to":"SIMMER","timestamp":"2026-05-27T14:32:48+09:00"}
```

**`emergency_stop_triggered`**:
```
event: emergency_stop_triggered
data: {"trigger":"dashboard_button","timestamp":"2026-05-27T14:32:48+09:00","open_positions_closed":1}
```

**`alert_added`**:
```
event: alert_added
data: {"id":143,"code":"W_HEALTH_001","severity":"WARN","message":"WebSocket reconnected after 8s","created_at":"2026-05-27T14:32:48+09:00"}
```

**`strategy_applied`**:
```
event: strategy_applied
data: {"new_version":4,"previous_version":3,"applied_by":"NIGHTLY_REVIEW","diff":{"MIN_PROB":[0.87,0.89]}}
```

**`health_recovered`**: `health_degraded` と同形式、`component` と `recovery_duration_sec` を含む。

## 10.6 REST API エンドポイント一覧

### 10.6.1 状態・ヘルス系

**`GET /api/v1/state`**
- 用途: 現在のボット状態取得
- レスポンス `data`: `bot_state` テーブル 1 行を JSON 化
- 例:
```json
{
  "ok": true,
  "data": {
    "state": "TRADING",
    "mode": "PAPER",
    "balance": 1042.18,
    "daily_pnl": 8.42,
    "daily_loss_limit": 30.0,
    "ws_polymarket_connected": true,
    "ws_binance_connected": true,
    "current_strategy_version": 3,
    "started_at": "2026-05-27T09:00:00+09:00",
    "last_updated": "2026-05-27T14:32:48+09:00"
  }
}
```

**`GET /api/v1/health`**
- 用途: 軽量ヘルスチェック（200 = OK、503 = degraded）
- レスポンス: `{"ok": true, "data": {"status": "healthy", "checks": {"db": true, "ws_polymarket": true, "ws_binance": true}}}`

### 10.6.2 取引系

**`GET /api/v1/trades?from=&to=&mode=&limit=&offset=`**
- 用途: 取引履歴フィルタ取得
- クエリ: ISO 8601 日時、`mode` は省略可、`limit` 上限 500（デフォルト 100）
- レスポンス `data.items`: `trades` 行の配列、`data.total` は総件数

**`GET /api/v1/trades/{id}`**
- 用途: 単一取引詳細

**`GET /api/v1/trades/export?format=csv|json&from=&to=`**
- 用途: 取引履歴ダウンロード
- レスポンス: `Content-Disposition: attachment` 付き

**`GET /api/v1/positions`**
- 用途: オープン中ポジション一覧

### 10.6.3 Markov 系

**`GET /api/v1/markov/current`**
- 用途: 最新 Markov 状態取得
- レスポンス: §10.5.3 `markov_update` のペイロードと同形式

**`GET /api/v1/markov/history?from=&to=&limit=`**
- 用途: Markov 履歴（グラフ描画用）

### 10.6.4 戦略系

**`GET /api/v1/strategy/current`**
- 用途: 現在の `strategy.json` 取得

**`GET /api/v1/strategy/versions?limit=`**
- 用途: バージョン履歴一覧

**`GET /api/v1/strategy/versions/{version}`**
- 用途: 特定バージョン詳細（パラメータ + パフォーマンスサマリ）

**`POST /api/v1/strategy/apply`**
- 用途: 新規戦略適用（Apply）
- リクエストボディ:
```json
{
  "parameters": {"MIN_PROB":0.89,"MIN_EDGE":0.06,"KELLY_FRACTION":0.65,"PERSISTENCE_THRESHOLD":0.72},
  "applied_by": "NIGHTLY_REVIEW",
  "source_report_id": 7
}
```
- バリデーション: §10.4.1 の `constraints` 範囲、±10% 警告超過時は `confirm_large_change: true` 必須
- レスポンス: 新 `version` を含む `strategy_versions` 行

**`POST /api/v1/strategy/rollback`**
- 用途: 過去バージョンへのロールバック（新バージョンとして適用）
- リクエストボディ: `{"target_version": 1, "reason": "v3 で勝率低下"}`
- 24 時間内の連続ロールバック検出時は `confirm_repeated: true` 必須

### 10.6.5 モード系

**`POST /api/v1/mode/switch`**
- 用途: モード切替
- リクエストボディ: `{"target_mode": "LIVE", "confirm_text": "LIVE", "checklist": {"ws_ok": true, "balance_ok": true, "loss_limit_ok": true, "emergency_ok": true}}`
- LIVE 切替時のみ `confirm_text` と全 checklist 項目を要求（§9.7.4）
- 状態が `TRADING` または `MONITORING_POSITION` の場合は 409 を返す

### 10.6.6 緊急停止系

**`POST /api/v1/emergency/stop`**
- 用途: 即時停止（確認なし、ボタン直接発火）
- リクエストボディ: `{"trigger": "dashboard_button|sidebar_button|command_palette|keyboard_shortcut"}`
- レスポンス: 停止前状態、クローズしたポジション数

**`POST /api/v1/emergency/recover`**
- 用途: 復帰（確認あり）
- リクエストボディ: `{"confirm": true, "target_mode": "PAPER"}`
- `confirm: true` 必須、復帰先モードは LIVE 不可（一度 PAPER/SIMMER を経由）

**`GET /api/v1/emergency/logs?from=&to=`**
- 用途: 緊急停止時のログ zip ダウンロード

### 10.6.7 アラート系

**`GET /api/v1/alerts?severity=&read=&limit=&offset=`**
- 用途: アラート一覧
- レスポンス `data.items`: `alerts` 行配列、`data.unread_count` を含む

**`POST /api/v1/alerts/{id}/read`**
- 用途: 既読化
- リクエストボディ: なし

**`POST /api/v1/alerts/read-all`**
- 用途: 一括既読化

### 10.6.8 夜間レビュー系

**`GET /api/v1/reports?from=&to=&limit=`**
- 用途: 夜間レポート一覧

**`GET /api/v1/reports/{id}`**
- 用途: 夜間レポート詳細（サマリ + 提案 + 適用済バージョン）

**`POST /api/v1/reports/{id}/preview-apply`**
- 用途: Apply 前の差分プレビュー
- リクエストボディ: `{"proposed_strategy": { ... }}`
- レスポンス: 現在版との差分、警告フラグ（±10% 超等）

### 10.6.9 What-If 系（PHASE 4 で実装、PHASE 2 はモック）

**`POST /api/v1/whatif/simulate`**
- 用途: パラメータ変更時の過去シミュレーション
- リクエストボディ: `{"from":"2026-05-20","to":"2026-05-26","parameters":{...}}`
- レスポンス: 取引数、勝率、累積 P&L、最大 DD、Sharpe
- PHASE 2 では固定シナリオを返す（§8.21）

**`GET /api/v1/whatif/scenarios`**
- 用途: 保存済シナリオ一覧

**`POST /api/v1/whatif/scenarios`**
- 用途: シナリオ保存

### 10.6.10 設定系

**`GET /api/v1/settings`**
- 用途: `yoruu.yaml` 現在値取得（パス・秘密値はマスク）

**`POST /api/v1/settings`**
- 用途: 設定更新
- リクエストボディ: 部分更新可（変更キーのみ送信）
- レスポンス: 適用結果と `restart_required: true|false`

### 10.6.11 i18n 系

**`GET /api/v1/i18n/{lang}`**
- 用途: 翻訳辞書取得（`lang` は `ja`|`en`）
- レスポンス: フラットなキー→値のオブジェクト
- 詳細は第14章

---

## 10.7 内部関数シグネチャ

### 10.7.1 命名・配置規約

- モジュール配置: `src/yoruu/<layer>/<module>.py`（layer 例: `core`, `strategy`, `execution`, `data`, `ui`, `infra`）
- Python 3.11+、型ヒント必須、`from __future__ import annotations` を全モジュールで使用
- 例外は `src/yoruu/errors.py` に集約（`YoRuuError` を基底）
- 日時は全て `datetime`（UTC 内部保持、UI 表示時に JST 変換）

### 10.7.2 StateMachine（`src/yoruu/core/state_machine.py`）

第6章で合意した 3 メソッド体系。状態遷移の単一の真実。

```python
class State(str, Enum):
    INITIALIZING = "INITIALIZING"
    IDLE = "IDLE"
    TRADING = "TRADING"
    MONITORING_POSITION = "MONITORING_POSITION"
    NIGHTLY_REVIEW = "NIGHTLY_REVIEW"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"
    BACKTEST = "BACKTEST"

class StateMachine:
    def __init__(self, db: Database, event_bus: EventBus) -> None: ...

    def current(self) -> State:
        """現在状態を取得（bot_state テーブルから読込）"""

    def require_state(self, *allowed: State) -> None:
        """許可状態でなければ StateViolationError を送出"""

    def transition(
        self,
        to: State,
        reason: str,
        actor: str = "system",
    ) -> StateTransition:
        """状態遷移実行。bot_state 更新 + state_changed イベント発火"""

    def ack(self, transition_id: str) -> None:
        """OM 等の呼び出し元へ遷移完了を確認応答"""

    def allowed_transitions(self, from_state: State) -> list[State]:
        """第3章 §3.2 の遷移表に基づく許可遷移リスト"""
```

**State Enum と第3章の関係**: 第3章 §3.1 の 9 状態（`INITIALIZING` 〜 `EMERGENCY_STOP`）に加え、本章 `State` Enum では補助状態 `ERROR` / `SHUTDOWN` / `BACKTEST` を定義する。`BACKTEST` は StateMachine の外側で完結（§10.7.8・第3章 §3.3）。`ERROR` / `SHUTDOWN` は `bot_state.state` の CHECK 制約および第3章 §3.2 遷移表で使用。

`StateViolationError` は `severity=ERROR` のアラートを生成し、第18章 `E_STATE_001` に対応。

### 10.7.3 OrderManager（`src/yoruu/execution/order_manager.py`）

第6章 §6.2 で StateMachine 経由に変更済。`OM` は状態保持しない。

```python
class OrderManager:
    def __init__(
        self,
        sm: StateMachine,
        executor: Executor,           # PaperExecutor | LiveExecutor
        risk: RiskGuard,
        db: Database,
    ) -> None: ...

    def evaluate_and_open(
        self,
        signal: TradeSignal,
    ) -> OrderResult:
        """シグナルを受け取り、リスクチェック後に約定試行"""

    def close_position(
        self,
        position_id: int,
        reason: CloseReason,
    ) -> OrderResult:
        """ポジション決済（成行 or 満期）"""

    def cancel_all_open(self) -> int:
        """全オープン注文キャンセル（緊急停止時）。戻り値: キャンセル件数"""

    def force_close_all(self) -> int:
        """全ポジション成行クローズ（緊急停止時）。戻り値: クローズ件数"""
```

戻り値の `OrderResult` は `success: bool`, `trade_id: int | None`, `error: ErrorPayload | None` を含む。

### 10.7.4 StrategyEvaluator（`src/yoruu/strategy/evaluator.py`）

第11章で詳細化、本章ではシグネチャのみ。

```python
class StrategyEvaluator:
    def __init__(
        self,
        markov: MarkovEngine,
        strategy: StrategyConfig,
    ) -> None: ...

    def evaluate(
        self,
        market_state: MarketState,
    ) -> EvaluationResult:
        """エントリー判定。シグナル生成 or 待機"""

    def reload(self, new_version: int) -> None:
        """strategy.json リロード（Apply 直後）"""
```

`EvaluationResult` は `should_enter: bool`, `side: Side | None`, `size_usd: float`, `edge: float`, `persistence: float`, `reason: str` を含む。

### 10.7.5 RiskGuard（`src/yoruu/execution/risk_guard.py`）

```python
class RiskGuard:
    def __init__(self, config: RiskConfig, db: Database) -> None: ...

    def check_pre_trade(
        self,
        signal: TradeSignal,
    ) -> RiskCheckResult:
        """事前チェック: 日次損失上限、最大取引サイズ、残高"""

    def daily_pnl(self) -> float:
        """当日損益（JST 00:00 リセット）"""

    def daily_loss_exceeded(self) -> bool:
        """日次損失上限超過判定"""

    def remaining_budget(self) -> float:
        """残予算（日次損失上限 - 既存損失）"""
```

### 10.7.6 PaperExecutor（`src/yoruu/execution/paper_executor.py`）

第13章で詳細化、本章ではシグネチャのみ。

```python
class PaperExecutor(Executor):
    def __init__(self, db: Database, fill_model: FillModel) -> None: ...

    def open(self, request: OpenRequest) -> FillResult:
        """ペーパー約定（スプレッド/スリッページモデル適用）"""

    def close(self, request: CloseRequest) -> FillResult:
        """ペーパー決済（満期 or 成行）"""
```

### 10.7.7 LiveExecutor（`src/yoruu/execution/live_executor.py`）

```python
class LiveExecutor(Executor):
    def __init__(self, polymarket: PolymarketClient, db: Database) -> None: ...

    def open(self, request: OpenRequest) -> FillResult: ...
    def close(self, request: CloseRequest) -> FillResult: ...
```

`Executor` プロトコル経由で OrderManager は Paper/Live を等価に扱う。

### 10.7.8 BacktestExecutor（`src/yoruu/execution/backtest_executor.py`）

```python
class BacktestExecutor:
    def __init__(
        self,
        historical_loader: HistoricalLoader,
        strategy: StrategyConfig,
    ) -> None: ...

    def run(
        self,
        period: DateRange,
        parameters: dict[str, float] | None = None,
    ) -> BacktestResult:
        """過去データで戦略を再実行。状態機械は使用しない"""
```

第3章 §3.3 で確定通り、`StateMachine` の外側で完結。

## 10.8 WebSocket クライアント関数

### 10.8.1 PolymarketClient（`src/yoruu/infra/polymarket_ws.py`）

```python
class PolymarketClient:
    def __init__(self, url: str, event_bus: EventBus) -> None: ...

    async def connect(self) -> None:
        """接続 + 自動再接続ループ起動"""

    async def disconnect(self) -> None: ...

    async def subscribe(self, market_id: str) -> None: ...

    def is_connected(self) -> bool: ...

    def on_message(self, callback: Callable[[PolymarketTick], None]) -> None: ...
```

再接続: 指数バックオフ（1s, 2s, 4s, 8s, 最大 30s）、10 回連続失敗で `health_degraded` を発火し `ERROR` 状態へ遷移。

### 10.8.2 BinanceClient（`src/yoruu/infra/binance_ws.py`）

```python
class BinanceClient:
    def __init__(self, url: str, symbol: str, event_bus: EventBus) -> None: ...

    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    def is_connected(self) -> bool: ...
    def on_tick(self, callback: Callable[[PriceTick], None]) -> None: ...
```

## 10.9 Markov エンジン関数

### 10.9.1 MarkovEngine（`src/yoruu/strategy/markov.py`）

```python
class MarkovEngine:
    def __init__(self, window_size: int = 20, db: Database = ...) -> None: ...

    def update(self, tick: PriceTick) -> None:
        """新ティック受信時に行列再計算（5 分足クローズ時のみ）"""

    def current_matrix(self) -> TransitionMatrix:
        """直近行列を取得"""

    def rolling_persistence(self) -> float:
        """min(P(UP→UP), P(DOWN→DOWN))"""

    def predict_next(self, current_direction: Direction) -> Prediction:
        """次方向の確率分布"""

    def history(self, limit: int = 100) -> list[MarkovSnapshot]: ...
```

`TransitionMatrix` は `p_up_up`, `p_up_down`, `p_down_up`, `p_down_down` を持つ frozen dataclass。

### 10.9.2 Persistence 計算

```python
def compute_persistence(matrix: TransitionMatrix) -> float:
    """min(P(UP→UP), P(DOWN→DOWN)) を返す。0.50〜0.90 想定"""
```

第7章 §7.2.1 で確定した方式（α 案）。第11章 §11.4 で詳細。

## 10.10 夜間レビュー関数

### 10.10.1 NightlyReporter（`src/yoruu/core/nightly_reporter.py`）

```python
class NightlyReporter:
    def __init__(self, db: Database, sm: StateMachine, event_bus: EventBus) -> None: ...

    def generate(self, target_date: date) -> NightlyReport:
        """指定日のレポート生成（DB 集計のみ、LLM は呼ばない）"""

    def schedule_daily(self, time: str = "04:00", tz: str = "Asia/Tokyo") -> None:
        """毎日定刻に generate() を呼ぶスケジューラ登録"""

    def latest(self) -> NightlyReport | None: ...
```

LLM 連携はユーザー手動（コピペ）で行い、ボット側は受信のみ。詳細は第15章。

### 10.10.2 StrategyApplier（`src/yoruu/strategy/applier.py`）

```python
class StrategyApplier:
    def __init__(self, db: Database, validator: StrategyValidator) -> None: ...

    def preview_diff(
        self,
        current: dict[str, float],
        proposed: dict[str, float],
    ) -> StrategyDiff:
        """差分プレビュー（変化率、警告フラグ含む）"""

    def apply(
        self,
        proposed: dict[str, float],
        applied_by: ApplySource,
        force_large_change: bool = False,
    ) -> int:
        """新バージョン作成。戻り値: 新 version 番号"""

    def rollback(
        self,
        target_version: int,
        reason: str,
        force_repeated: bool = False,
    ) -> int: ...
```

## 10.11 バリデーション・ユーティリティ関数

### 10.11.1 StrategyValidator（`src/yoruu/strategy/validator.py`）

```python
class StrategyValidator:
    def __init__(self, constraints: dict[str, Range]) -> None: ...

    def validate(self, parameters: dict[str, float]) -> ValidationResult:
        """必須キー4件、範囲チェック、±10% 警告判定"""

    def is_within_range(self, key: str, value: float) -> bool: ...
    def is_large_change(self, key: str, old: float, new: float) -> bool:
        """変化率 ±10% 超で True"""
```

### 10.11.2 EventBus（`src/yoruu/core/event_bus.py`）

```python
class EventBus:
    def subscribe(self, event_name: str, handler: Callable) -> SubscriptionId: ...
    def unsubscribe(self, sub_id: SubscriptionId) -> None: ...
    def publish(self, event_name: str, payload: dict) -> None:
        """SSE エンドポイントと内部リスナー双方に配信"""
```

### 10.11.3 Database（`src/yoruu/data/database.py`）

```python
class Database:
    def __init__(self, path: Path) -> None: ...

    def connect(self) -> None: ...
    def migrate(self) -> None:
        """スキーマ migration（§10.3 のテーブル作成）"""

    def execute(self, sql: str, params: tuple = ()) -> Cursor: ...
    def fetch_one(self, sql: str, params: tuple = ()) -> dict | None: ...
    def fetch_all(self, sql: str, params: tuple = ()) -> list[dict]: ...

    @contextmanager
    def transaction(self) -> Iterator[Connection]: ...

    def backup(self, target: Path) -> None:
        """SQLite Online Backup API 使用、04:00 JST に実行"""
```

### 10.11.4 ConfigLoader（`src/yoruu/infra/config.py`）

```python
class ConfigLoader:
    @staticmethod
    def load_yaml(path: Path) -> YoRuuConfig:
        """yoruu.yaml 読込 + スキーマ検証"""

    @staticmethod
    def load_strategy(path: Path) -> StrategyConfig:
        """strategy.json 読込 + 制約検証"""

    @staticmethod
    def save_yaml(path: Path, config: YoRuuConfig) -> None: ...
```

### 10.11.5 I18n（`src/yoruu/ui/i18n.py`）

```python
class I18n:
    def __init__(self, default_lang: str = "ja") -> None: ...

    def load(self, lang: str) -> dict[str, str]:
        """src/yoruu/ui/locales/<lang>.json を読込"""

    def t(self, key: str, lang: str | None = None, **vars: Any) -> str:
        """翻訳取得。フォールバック: ja → en → key そのまま"""

    def available_languages(self) -> list[str]: ...
```

第14章で詳細化。サーバー側は API レスポンスを言語非依存に保ち、表示変換は UI 側で行う。

## 10.12 データライフサイクル・保持期間

### 10.12.1 保持期間まとめ

| データ種別 | 保持期間 | 削除方式 | 備考 |
|----------|---------|---------|------|
| `bot_state` | 永続 | 削除なし | 単一行 |
| `trades` | 永続 | 削除なし | エクスポート可 |
| `positions` | クローズ即時削除 | アプリ側 | `trades` に集約 |
| `markov_state` | 24 時間 | cron（毎時 00 分） | 履歴は集計済のため |
| `price_ticks` | 7 日 | cron（04:00 JST） | バックテスト用は別管理 |
| `alerts` | 90 日 | cron（04:00 JST） | 重大は別エクスポート可 |
| `strategy_versions` | 永続 | 削除なし | 監査用 |
| `daily_reports` | 永続 | 削除なし | LLM 提案含む |
| `emergency_stops` | 永続 | 削除なし | 監査用 |
| `audit_log` | 永続 | 削除なし | 監査用 |
| `what_if_scenarios` | 永続 | ユーザー削除可 | UI から手動削除 |
| `data/backup/*.db` | 30 日 | cron（04:30 JST） | ローテーション |
| ログファイル | `logging.retain_days`（既定 30 日） | logrotate 相当 | 50MB ローテート |

### 10.12.2 ライフサイクル状態遷移

各レコードの基本状態：

- **`trades`**: `OPEN` → `CLOSED`（決済成立）または `EXPIRED`（満期）または `CANCELLED`（緊急停止時）
- **`positions`**: `OPEN` → `CLOSING` → 削除
- **`alerts`**: 作成（`read=0`）→ 既読（`read=1`）→ 90 日後削除
- **`strategy_versions`**: `applied_by` で起源を識別、削除なし

### 10.12.3 バックアップ・リストア手順

- バックアップ: `Database.backup()` を 04:00 JST 直後に実行（夜間レビュー生成後）
- リストア: ボット停止 → `data/yoruu.db` を退避 → バックアップを配置 → 再起動
- 詳細手順は第22章（運用）で規定

### 10.12.4 タイムゾーン規約

- DB 保存: 全て ISO 8601 + `+09:00`（JST）
- 集計境界: 「日次」= JST 00:00〜23:59:59（夜間レビューは 04:00 JST の 1 サイクル）
- UI 表示: 既定 JST、`yoruu.yaml` に `display_timezone` を追加する場合は v1.1 で検討

## 10.13 章間相互参照表

| 本章節 | 参照先 | 内容 |
|-------|--------|------|
| §10.2.4 認証 | 第5章 §5.2 | SSH トンネル前提 |
| §10.3 SQLite | 第2章 §2.4 | データ層配置 |
| §10.3.3 `bot_state` | 第3章 §3.1, §10.7.2 | 9 状態 + 補助 3 状態 |
| §10.3.11 `emergency_stops` | 第9章 §9.8.7 | 緊急停止履歴 |
| §10.3.12 `audit_log` | 第18章 | 監査ログ |
| §10.3.13 `what_if_scenarios` | 第8章 §8.21, §10.6.9 | What-If 保存 |
| §10.4.1 `strategy.json` | 第7章 §7.2, 第11章 §11.4 | パラメータ範囲 |
| §10.4.3 反映タイミング | 第9章 §9.9 | 設定画面操作 |
| §10.5 SSE | 第8章 §8.9 | UI 側受信 |
| §10.6.5 mode/switch | 第9章 §9.7, 第12章 | LIVE 2 段階確認 |
| §10.6.6 emergency | 第9章 §9.8, 第6章 §6.7 | 非対称設計 |
| §10.6.9 What-If | 第8章 §8.21, 第11章 §11.7 | PHASE 4 で実計算 |
| §10.7.2 StateMachine | 第6章 §6.2-§6.7 | require_state/transition/ack |
| §10.7.4 Evaluator | 第11章 §11.4-§11.5 | アルゴリズム |
| §10.7.6 PaperExecutor | 第13章 | 約定モデル |
| §10.9 Markov | 第7章 §7.2.1, 第11章 §11.4 | Persistence α 案 |
| §10.10 夜間レポート | 第15章 | LLM 連携手順 |
| §10.11.5 I18n | 第14章 | 翻訳キー体系 |
| §10.12 ライフサイクル | 第22章 | 運用手順 |
| §10.13 エラー | 第18章 | エラーコード体系 |

## 10.14 品質チェック

### 10.14.1 章末チェックリスト

- [ ] §10.1 目的・スコープ明示（含む／含まない両方）
- [ ] §10.2 共通レスポンス形式と HTTP ステータス定義
- [x] §10.3 SQLite 11 テーブル全て CREATE 文付き（v1.0.1 で §10.3.11〜13 追加）
- [ ] §10.3 旧 ch11「Data Model」統合完了
- [ ] §10.4 `strategy.json` 完全スキーマ + 範囲制約
- [ ] §10.4 `yoruu.yaml` 完全スキーマ + 反映タイミング表
- [ ] §10.5 SSE イベント 11 件全てペイロード例付き
- [ ] §10.6 REST エンドポイント 28 件揃う（11 グループ）
- [ ] §10.7 StateMachine 3 メソッド体系（require_state/transition/ack）
- [ ] §10.7 BacktestExecutor が StateMachine 外側であることを明示
- [ ] §10.8 WebSocket 再接続戦略明記
- [ ] §10.9 Markov Persistence が α 案（0.50〜0.90、既定 0.70）
- [ ] §10.10 夜間レビューが LLM 非連携（ユーザー手動コピペ）
- [ ] §10.11 バリデーション・ユーティリティ揃う
- [ ] §10.12 保持期間まとめ + タイムゾーン規約
- [ ] §10.13 相互参照表に新章番号で整合
- [ ] Mermaid コードフェンス全て閉じている（本章は SQL/JSON のみ、Mermaid なし）

### 10.14.2 一次レビュー観点（7 項目）

1. API 共通仕様（§10.2）が PHASE 4 実装で迷いなく適用できるか
2. SQLite スキーマ（§10.3）が旧 ch11 を完全に包含し、整合性制約が網羅されているか
3. 設定ファイルスキーマ（§10.4）の反映タイミング表が運用に十分か
4. SSE 11 イベント（§10.5）が第8章 §8.9 と完全一致するか
5. REST 28 エンドポイント（§10.6）が UI 11 画面の全操作を満たすか
6. 関数シグネチャ（§10.7〜§10.11）が第6章のシーケンスと整合するか
7. データライフサイクル・保持期間（§10.12）が運用章（第22章）の前提と矛盾しないか

### 10.14.3 既知の未確定事項

- `display_timezone` の `yoruu.yaml` 追加は v1.1 で検討
- バックアップの暗号化（オフサイト送信時）は第22章で検討
- What-If 計算ロジック（§10.6.9）は第11章 §11.7 で詳細化
- LLM 連携の完全自動化（§10.10）は将来機能（PHASE 7 以降）

### 10.14.4 PHASE 引き継ぎ

- **PHASE 2（UI モック）**: §10.5 SSE ペイロード例・§10.6 レスポンス例を `mock-data.js` の固定値ソースとして使用
- **PHASE 3（コア実装）**: §10.3 マイグレーション、§10.7〜§10.11 関数を実装
- **PHASE 4（UI 実装）**: §10.5・§10.6 を REST/SSE クライアントの仕様として使用
- **PHASE 5（統合テスト）**: §10.14.2 の 7 観点をテスト設計の基礎とする
