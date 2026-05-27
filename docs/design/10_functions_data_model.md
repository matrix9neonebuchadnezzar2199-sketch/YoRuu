# 第10章 関数・データモデル

- **バージョン**: v1.0（Part 1/2 ドラフト）
- **作成日**: 2026-05-27
- **ステータス**: DRAFT（Part 2 統合後に REVIEW_PENDING へ）
- **関連章**: 2（アーキテクチャ）, 4（データフロー）, 6（シーケンス）, 7（I/O 図）, 11（戦略ロジック）, 12（モード仕様）, 13（ペーパー約定）, 14（i18n）, 15（夜間レビュー）, 18（エラーハンドリング）, 19（キルスイッチ）
- **旧章統合**: 旧 ch11「Data Model」を §10.3（SQLite）／§10.4（`strategy.json`）に統合

## 10.1 目的・スコープ

### 10.1.1 目的

YoRuu の関数シグネチャ、REST API エンドポイント、SSE ペイロード、SQLite スキーマ、設定ファイル構造を **単一の真実（SSOT）** として確定する。PHASE 3（コア実装）と PHASE 4（UI 実装）の双方で参照される。

### 10.1.2 スコープ（含む）

- REST API エンドポイント一覧と JSON スキーマ（§10.2）
- SSE イベントと JSON ペイロード（§10.5）
- SQLite テーブル定義 8 件（§10.3）
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

### 10.3.3 `bot_state` テーブル

```sql
CREATE TABLE bot_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  state TEXT NOT NULL CHECK (state IN (
    'INIT', 'IDLE', 'TRADING', 'MONITORING_POSITION',
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

シングルトン制約（`id = 1`）により 1 行のみ。`state` は第3章 §3.1 の 9 状態と一致。

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

**Part 1/2 完了**。本パートでは API 共通仕様（§10.2）、SQLite 8 テーブル（§10.3）、設定ファイルスキーマ（§10.4）、SSE 11 イベント（§10.5）、REST 全 28 エンドポイント（§10.6）を確定しました。総量約 620 行相当。

**Part 2/2 で扱う内容**:
- §10.7 内部関数シグネチャ（StateMachine、OrderManager、StrategyEvaluator、PaperExecutor 等）
- §10.8 WebSocket クライアント関数
- §10.9 Markov エンジン関数
- §10.10 夜間レビュー関数
- §10.11 バリデーション・ユーティリティ関数
- §10.12 データライフサイクル・保持期間まとめ
- §10.13 章間相互参照表
- §10.14 品質チェック

Part 2 はこの後に渡します。
