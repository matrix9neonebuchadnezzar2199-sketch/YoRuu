# 第22章 設定仕様（yoruu.yaml）

- **バージョン**: v1.0.5
- **作成日**: 2026-05-27
- **ローリング更新**: 2026-05-28（v1.0.5: `principal` / `display.fx`、§22.9 マイグレーション CLI）
- **v1.0.5 追補正本**: [`ch22_v1.0.5_ROLLING_DRAFT.md`](./ch22_v1.0.5_ROLLING_DRAFT.md)
- **承認日**: 2026-05-27
- **ステータス**: APPROVED（ローリング更新、再レビュー不要）
- **関連章**: 10（§10.4.2 ドラフト）, 21（影響マトリクス）, 24（Polymarket 認証）

> ch10 §10.4.2 の完全スキーマは**本章が SSOT**。ch10 は API・DB 中心のため、設定ファイルの運用詳細は本章を参照する。

## 22.1 ファイル配置

| ファイル | 既定パス | 権限 |
|----------|----------|------|
| `yoruu.yaml` | `config/yoruu.yaml` | 0600（秘密含む） |
| `strategy.json` | `config/strategy.json` | 0644 |
| 環境変数オーバーライド | `YORUU_*` | §22.6 |

## 22.2 完全スキーマ（v1.0）

```yaml
# YoRuu 設定 SSOT — 第22章
mode: PAPER  # BACKTEST | PAPER | SIMMER | LIVE
initial_principal: 1000.0   # 推奨。initial_balance は後方互換（§22.2.2）
currency: USD

principal:
  max_deposit_per_tx: 100000.0
  max_withdraw_per_tx: 100000.0
  require_confirm_on_withdraw: true

display:
  fx:
    enabled: true
    provider: exchangerate_host
    cache_ttl_sec: 900
    stale_after_sec: 1800
    fallback_rate: 150.0

market:
  id: BTC_5MIN_UPDOWN
  source: POLYMARKET
  binance_symbol: BTCUSDT
  # 5分バイナリ市場の内部識別子（実マーケット ID は lab 設定のみ）

risk:
  max_trade_size_usd: 10.0
  daily_loss_limit_usd: 30.0
  emergency_stop_enabled: true
  consecutive_fail_limit: 3
  consecutive_fail_window_min: 15

websocket:
  polymarket_url: wss://ws-subscriptions-clob.polymarket.com/ws/
  binance_url: wss://stream.binance.com:9443/ws/btcusdt@trade
  reconnect_interval_sec: 5
  max_reconnect_attempts: 10
  stale_tick_sec: 30

nightly_review:
  enabled: true
  send_time: "04:00"
  timezone: Asia/Tokyo
  pause_trading_during_review: true

polymarket:
  # LIVE / SIMMER の実 API 利用時のみ必須（lab 環境）
  api_key_env: YORUU_POLY_API_KEY      # 環境変数名（値を yaml に書かない）
  api_secret_env: YORUU_POLY_API_SECRET
  chain_id: 137
  signature_type: EIP712
  clob_host: https://clob.polymarket.com

paths:
  db: data/yoruu.db
  strategy: config/strategy.json
  logs: logs/
  historical: data/historical/
  reports: reports/

ui:
  bind_host: 127.0.0.1
  port: 8765
  default_language: ja

logging:
  level: INFO
  rotate_mb: 50
  retain_days: 30

paper:
  # FillModel SSOT（§22.2.1）— 実装: src/yoruu/config/settings.py PaperSettings
  spread_assumed: 0.02      # BACKTEST / WS 欠落時フォールバック（ch13 §13.3.3）
  slippage_coeff: 0.0001
  slippage_max: 0.02
  latency_ms_mean: 80
  latency_ms_std: 20
```

### 22.2.1 FillModel パラメータ SSOT（Q2 確定）

**本章 `paper.*` が FillModel の唯一の数値 SSOT**。第13章 §13.3.2 は重複定義を持たず、本章への参照のみとする。

| キー（`yoruu.yaml`） | lab / 開発用初期値 | 許容範囲（目安） | 用途 |
|---------------------|-------------------|-----------------|------|
| `paper.spread_assumed` | **0.02** | 0.01〜0.05 | BACKTEST またはベスト気配取得不可時の固定スプレッド |
| `paper.slippage_coeff` | **0.0001** | 0.0〜0.01 | サイズ比例スリッページ（USD あたり） |
| `paper.slippage_max` | **0.02** | 0.01〜0.05 | スリッページ上限 |
| `paper.latency_ms_mean` | **80** | 50〜500 | 約定遅延の平均（ms） |
| `paper.latency_ms_std` | **20** | 0〜200 | 遅延の標準偏差（ms、正規分布） |

**対応 B（マスター判定）**: 上表の値は **lab / 開発用初期値** である。本番運用での再校正（スプレッド・遅延の強度調整）は第13章 §13.9.2「保守的パラメータ原則」および運用ノートに従い、`yoruu.yaml` を更新する。ch13 本文に数値を再掲しない。

**実装マッピング**: `FillModel(settings: PaperSettings)`（`f499778`）。`spread_assumed` は PHASE 3 CLI では `OrderBook` 生成時に利用（BACKTEST / モック）。

**cross-ref**: 第13章 §13.3.2（参照のみ）、§13.2.5（残高）、第16章 INV-D-06 v2。

### 22.2.2 元本設定（v1.0.5）

| キー | 型 | 既定 | 説明 |
|------|-----|------|------|
| `initial_principal` | float | 1000.0 | 初回起動時の `bot_state.principal` |
| `initial_balance` | float | — | **非推奨**。`initial_principal` 未設定時のみ読み取り（DeprecationWarning） |
| `principal.max_deposit_per_tx` | float | 100000.0 | 1 回入金上限（USD） |
| `principal.max_withdraw_per_tx` | float | 100000.0 | 1 回出金上限（USD） |
| `principal.require_confirm_on_withdraw` | bool | true | `confirm: true` 必須（`E_PRINCIPAL_004`） |

**cross-ref**: ch10 §10.6.12、ch13 §13.2.6、ch16 INV-D-06〜09、ch18 `E_PRINCIPAL_*`。

### 22.2.3 表示換算（FX）（v1.0.5）

| キー | 型 | 既定 | 説明 |
|------|-----|------|------|
| `display.fx.enabled` | bool | true | HUD JPY/USD トグル |
| `display.fx.provider` | enum | `exchangerate_host` | 許容: `exchangerate_host` のみ（v1.0.5） |
| `display.fx.cache_ttl_sec` | int | 900 | キャッシュ有効（15 分） |
| `display.fx.stale_after_sec` | int | 1800 | stale 注記閾値 |
| `display.fx.fallback_rate` | float | 150.0 | 取得失敗時固定レート |

**フォールバック 5 段階**: (1) キャッシュ (2) `fallback_rate` (3) stale 表示継続 (4) USD 固定 (5) トグル無効化。詳細は `docs/design/FX_RATE_AUTO_FETCH_DRAFT.md`（M4.7）。

**cross-ref**: ch10 §10.6.13、ch18 `E_FX_*`。

## 22.3 検証ルール

| キー | 型 | 制約 |
|------|-----|------|
| `mode` | enum | 4 値のみ |
| `initial_principal` | float | > 0 |
| `initial_balance` | float | > 0（非推奨、principal 未設定時） |
| `principal.max_deposit_per_tx` | float | > 0 |
| `principal.max_withdraw_per_tx` | float | > 0 |
| `display.fx.fallback_rate` | float | > 0 |
| `risk.max_trade_size_usd` | float | > 0, ≤ initial_principal（または balance 基準） |
| `risk.daily_loss_limit_usd` | float | > 0 |
| `nightly_review.send_time` | HH:MM | 00:00〜23:59 |
| `ui.port` | int | 1024〜65535 |
| `polymarket.chain_id` | int | 137（Polygon） |

`yoruu config validate` CLI が本章ルールを実装（PHASE 3）。

## 22.4 モード別必須キー

| モード | 必須セクション |
|--------|----------------|
| BACKTEST | `market`, `paths.historical` |
| PAPER | `websocket` |
| SIMMER | `websocket`, `nightly_review.enabled=true` 推奨 |
| LIVE | `websocket`, `polymarket`, `risk` |

## 22.5 SIGKILL / 停止時（ch12 ローリング）

- 未決済ポジション: `close(reason=EXPIRED)` を次回起動時に試行（v1.0）
- `paths.db` の WAL: 正常終了時 checkpoint

## 22.6 環境変数

| 変数 | 対応キー |
|------|----------|
| `YORUU_MODE` | `mode` |
| `YORUU_DB_PATH` | `paths.db` |
| `YORUU_POLY_API_KEY` | polymarket（本文非格納） |

優先順位: 環境変数 > yaml > ビルトイン既定。

## 22.9 DB マイグレーション CLI（v1.0.5）

```bash
yoruu db migrate [--dry-run] [--db PATH]
```

| ステップ | 内容 |
|----------|------|
| 1 | `bot_state` に `principal REAL` 追加（NULL 許容） |
| 2 | `principal_transactions` テーブル作成（ch10 §10.3.14） |
| 3 | `principal IS NULL` 行を `initial_principal`（または `initial_balance`）で埋める |
| 4 | `principal` を NOT NULL 化 |

`--dry-run`: DDL と件数のみ表示。既存 `balance` / `trades` は変更しない。

**cross-ref**: ch10 §10.3.14、ch13 §13.2.6、M4.4 実装。

## 22.10 章間参照（v1.0.5 追加分）

| 本章 | 参照先 |
|------|--------|
| §22.2.2 | ch10 §10.6.12、ch16 INV-D-06〜09 |
| §22.2.3 | ch10 §10.6.13、ch18 `E_FX_*` |
| §22.9 | ch10 §10.3.14 |

## 22.7 章間参照

| 本章 | 参照先 |
|------|--------|
| §22.2 | ch10 §10.4（要約） |
| 影響 | ch21 |
| CLOB | ch24 |
| §22.2.1 FillModel | ch13 §13.3（参照のみ）、`fill_model.py` |
| paper.* | ch13 §13.2.5 残高は別 SSOT |

## 22.8 レビュー（7項目）— 全合格

---

**出力ファイル名**: `22_config_spec.md`
