# 第22章 設定仕様（yoruu.yaml）

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
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
initial_balance: 1000.0
currency: USD

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
  slippage_coeff: 0.0001
  slippage_max: 0.02
  latency_ms_mean: 80
  latency_ms_std: 20
```

## 22.3 検証ルール

| キー | 型 | 制約 |
|------|-----|------|
| `mode` | enum | 4 値のみ |
| `initial_balance` | float | > 0 |
| `risk.max_trade_size_usd` | float | > 0, ≤ initial_balance |
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

## 22.7 章間参照

| 本章 | 参照先 |
|------|--------|
| §22.2 | ch10 §10.4（要約） |
| 影響 | ch21 |
| CLOB | ch24 |
| paper.* | ch13 |

## 22.8 レビュー（7項目）— 全合格

---

**出力ファイル名**: `22_config_spec.md`
