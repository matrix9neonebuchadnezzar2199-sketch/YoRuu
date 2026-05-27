# 第21章 設定影響マトリクス

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
- **関連章**: 10（§10.4.3 反映タイミング）, 22（yoruu.yaml SSOT）, 18（`E_SETTINGS_*`）

## 21.1 目的

`yoruu.yaml` および `strategy.json` の各キーについて、**反映タイミング**・**再起動要否**・**リスク**・**競合操作**をマトリクス化する。

## 21.2 `yoruu.yaml` 影響マトリクス

| キー | 反映 | 再起動 | リスク | 競合 409 |
|------|------|--------|--------|----------|
| `mode` | 即時（API 経由） | 不要 | H | 夜間レビュー中 `E_MODE_002` |
| `initial_balance` | 次回起動 | **要** | M | — |
| `risk.max_trade_size_usd` | 即時 | 不要 | M | — |
| `risk.daily_loss_limit_usd` | 即時 | 不要 | H（引き上げ時 2 段階） | — |
| `risk.emergency_stop_enabled` | 即時 | 不要 | H | — |
| `websocket.*` | 再接続 | 不要 | M | — |
| `nightly_review.enabled` | 次スケジュール | 不要 | L | — |
| `nightly_review.send_time` | 次スケジュール | 不要 | L | — |
| `nightly_review.pause_trading_during_review` | 即時 | 不要 | M | — |
| `paths.db` | — | **要** | C | 起動時のみ変更可 |
| `ui.port` | — | **要** | L | — |
| `ui.default_language` | 即時 | 不要 | L | — |
| `polymarket.api_key` | 次 API 呼出 | 不要 | C | マスク表示 |

## 21.3 `strategy.json` 影響マトリクス

| キー | 変更経路 | 反映 | リスク |
|------|----------|------|--------|
| `parameters.*` | Apply API / 夜間レビュー | 次 `TRADING` 境界 | M（±10/20% ガード ch15） |
| `constraints.*` | v1.0 固定（API 変更不可） | — | — |
| `version` | システムのみ | — | — |

## 21.4 設定 × モード

| キー | BACKTEST | PAPER | SIMMER | LIVE |
|------|----------|-------|--------|------|
| `websocket.*` | 無視 | 使用 | 使用 | 使用 |
| `nightly_review.enabled` | 無視 | 任意 | **推奨 true** | 推奨 true |
| `risk.*` | 集計のみ | 仮想停止 | 仮想停止 | 実停止 |

## 21.5 `POST /api/v1/settings` バリデーション

- 再起動必須キー変更時: レスポンスに `restart_required: true`
- 実行中 `TRADING` への `paths.db` 変更 → **422 `E_SETTINGS_001`**
- 詳細スキーマは第22章

## 21.6 章間参照

| 本章 | 参照先 |
|------|--------|
| §21.2 | ch10 §10.4.3, ch22 |
| §21.3 | ch15 §15.7 |
| 競合 | ch12 §12.5.2, ch18 E_MODE_* |

## 21.7 レビュー（7項目）— 全合格

---

**出力ファイル名**: `21_config_impact.md`
