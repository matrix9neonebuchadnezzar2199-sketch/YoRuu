# YoRuu UI Mockups — CHANGELOG

## 2026-05-28 — §F T4.1 SSE_PAYLOADS（B1）

**スコープ**: 監査 B1。ch10 §10.5.3 / ch8 §8.9 とモック SSE 契約を一致。

| イベント | 修正要点 |
|----------|----------|
| `emergency_stop_triggered` | `{at}` のみ廃止 → `trigger` / `timestamp` / `open_positions_closed` |
| `mode_changed` | `from` / `to` を大文字モード（`PAPER` 等） |
| `strategy_applied` | `{version}` 廃止 → `new_version` / `previous_version` / `applied_by` / `applied_at` / `diff` |

**変更ファイル**

- `shared/mock-data.js` — `SSE_PAYLOADS`（11 件）、`ssePayload()`、`mockSSE` 統合
- `shared/app.js` — 緊急停止 FAB
- `03_nightly_review.html` / `05_strategy_history.html` / `07_mode_switch.html`

**申し送り**: T4.2（`nightly-review.js` の `W_NIGHTLY_001`、`error.e_nightly_008`、パレット、`build_locales.py`）は別チャット。

## 2026-05-28 — Q3-MOCK 残高整合

**スコープ**: `Q3-MOCK`（監査書 §F T4.1 SSE とは別）。PaperExecutor（`f499778` / ch13 §13.2.5）とモック残高を一致。

| 項目 | 内容 |
|------|------|
| open 成功 | `balance -= size_usd` |
| close 成功 | `balance += size_usd + pnl` |
| INV-D-06 | `balance + Σ(open.size_usd) ≈ initial + Σ(closed.pnl)` |

**変更ファイル**

- `shared/mock-data.js` — ランタイム台帳、`mockSSE` で `position_opened` / `position_closed` 時に残高更新、`runQ3BalanceDemo()` 追加
- `shared/app.js` — `onBalanceChange` コールバック
- `01_dashboard.html` / `02_trade_log.html` — 残高表示と SSE 後の即時再描画

**手動確認**: ブラウザコンソールで `YoRuuMockData.runQ3BalanceDemo()`（3 open → 3 close、`console.table` 出力）。

**申し送り**: §F **T4.1**（`SSE_PAYLOADS` / B1）は別チャット `phase2-sse` 等で実施。
