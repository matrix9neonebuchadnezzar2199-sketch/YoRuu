# YoRuu UI Mockups — CHANGELOG

## 2026-05-28 — M4.6 `mock-data.js` principal / FX / HUD aggregates

| 項目 | 内容 |
|------|------|
| principal | 5 値スナップショット、`principal_transactions`、INV-D-06 v2 / D-07 / D-09 監視 |
| SSE | `SSE_PAYLOADS.principal_changed` + `mockSSE` ledger 更新 |
| FX | `getFxRate()` / `formatMoney()`、stale は `drawdown` シナリオ |
| HUD 用 | `signal_counts` / `trade_stats` / `system_panels` / `nightly_countdown_sec` |
| 手動 | `runQ3PrincipalDemo()`、`simulatePrincipalDeposit/Withdraw` |
| 互換 | 既存 10 画面の `balance.*` API 不変 |

## 2026-05-28 — ch10 v1.2 / ch13 v1.0.5 設計ローリング（H-1）

| 項目 | 内容 |
|------|------|
| ch10 | principal、principal_transactions、SSE #12、severity、principal/fx API |
| ch13 | D11 v2 入出金、PrincipalService |
| 会計 | H-1（balance=自由資金、total_assets=balance+locked） |

## 2026-05-28 — I-1 / 案 P 確定・PHASE4 ロードマップ v1 採用

| 項目 | 内容 |
|------|------|
| I-1 | Hub + HUD 温存、主入口 `00_hud.html` |
| 案 P | M4.6 → M4.7 順序維持 |
| 正本 | `PHASE4_ROADMAP_v1.md`、`00_ROADMAP` 本表差し替え |

## 2026-05-28 — 突き合わせ v2 + HUD/元本方針確定

| 項目 | 内容 |
|------|------|
| `REF_IMAGE_GAP_MATRIX_v2.md` | アプローチ B、A-2/B-2、00_hud 配置表 |
| 設計ドラフト | `docs/design/PRINCIPAL_CONCEPT_V1_DRAFT.md` |
| ロードマップ | `PHASE4_ROADMAP_REVISION_DRAFT_2026-05-28.md`、テンプレ 14 |

## 2026-05-28 — 参照画像 ↔ 01_dashboard 突き合わせ初版

| 項目 | 内容 |
|------|------|
| ドキュメント | `REF_IMAGE_GAP_MATRIX_v1.md` |
| 参照画像 | `reference/hermes-hud-ref.png` |
| 論点 | シングル HUD vs 10 画面分散、アプローチ A/B、判断 5 項目 |

## 2026-05-28 — §F T4.2 i18n / パレット / nightly 整合

**スコープ**: Track 2D 実装適用。`W_NIGHTLY_001` 廃止、`E_NIGHTLY_008` 二段義（10% WARN / 20% ERROR）。

| 項目 | 内容 |
|------|------|
| `nightly-review.js` | 警告/拒否とも `E_NIGHTLY_008` + `:WARN` / `:ERROR` サフィックス |
| i18n | `error.e_nightly_008.warn` / `.error`、ja→en→key フォールバック |
| パレット | `--severity-error-color` / `--severity-warn-color`、`severity.js` 完全一致判定 |
| CI | `tools/build_locales.py --check`、`.github/workflows/mock-locales.yml` |

**変更ファイル**: `nightly-review.js`, `i18n.js`, `style.css`, `severity.js`, `app.js`, `03_nightly_review.html`, `locales/*`, `tools/build_locales.py`

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
