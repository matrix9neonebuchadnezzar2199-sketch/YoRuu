# YoRuu UI Mockups — CHANGELOG

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
