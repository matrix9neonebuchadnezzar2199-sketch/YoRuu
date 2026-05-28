# PHASE 4 着手キックオフテンプレ

> **目的**: PHASE 4（FastAPI + 実 Web UI）の Composer 2.5 引き渡し SSOT。  
> **前提**: PHASE 2 モック 11/11 完了、PHASE 3 **コード実装 Exit**（[`PHASE3_EXIT_DECLARATION.md`](./PHASE3_EXIT_DECLARATION.md) `3f17b1d`）。lab 24h paper 実運用は並行可。  
> **並列チャット**: Q3 残高のみ先行する場合は [`PHASE3_PARALLEL_CHAT_TEMPLATES.md`](./PHASE3_PARALLEL_CHAT_TEMPLATES.md) §2（**Q3-MOCK**）。§F **T4.1 SSE** は別投入。

## 1. 着手前マスター判断

| 判断 | 内容 |
|------|------|
| Track 4 完了 | B-HIGH 3 件クローズ、§8.25.3 10/10 PASS |
| PHASE 3 Exit（コード） | カバレッジ 80%・INV 19/19・WS/CLOB/API/SSE — **達成**（`dea96e0`） |
| PHASE 3 Exit（運用） | lab 24h `yoruu paper-24h` — **未実施**（ハーネス済） |
| PHASE 3 前倒し | `src/yoruu/web/` + `api/sse/` 既存。M4.1 は静的 UI 移植が残 |
| モデル | FastAPI / SSE は Composer 2.5、設計ローリングは Opus |

## 2. 引き渡し SSOT（`@` 添付）

| # | SSOT | 役割 |
|---|------|------|
| 1 | [`08_ui_mockup.md`](./08_ui_mockup.md) | 画面・SSE・a11y |
| 2 | [`10_functions_data_model.md`](./10_functions_data_model.md) §10.3 / §10.5.3 / §10.6 | REST + SSE 契約 |
| 3 | [`14_i18n_design.md`](./14_i18n_design.md) | i18n キー |
| 4 | [`15_nightly_review.md`](./15_nightly_review.md) §15.4.8 / §15.8 | レポート + Apply |
| 5 | [`16_invariants.md`](./16_invariants.md) | INV-* |
| 6 | [`17_risk_matrix.md`](./17_risk_matrix.md) 〜 [`19_kill_switch.md`](./19_kill_switch.md) | 安全 |
| 7 | [`22_config_spec.md`](./22_config_spec.md) | 設定 |
| 8 | [`24_polymarket_clob.md`](./24_polymarket_clob.md) | CLOB |
| 9 | `docs/mockups/` | モック HTML（契約整合後） |

## 3. Composer 依頼テンプレ（コピペ用）

```
[実装] PHASE 4 M4.2: 静的モック → Web UI 結線（FastAPI 骨格は PHASE 3 済）。

スコープ: docs/mockups/ の HTML/JS を yoruu/web/static へ移植、EventSource → /api/v1/events/stream。
SSOT: @docs/design/08_ui_mockup.md @docs/design/10_functions_data_model.md @src/yoruu/api/sse/
完了基準: ダッシュボードで SSE 11 イベント受信、B1 契約とバイト一致。
設計変更は Opus に返す。commit + push まで実施。
```

## 4. 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-05-28 | 初版（T3.9 新規） |
| 2026-05-28 | PHASE 3 コード Exit 反映、M4.1 前倒し注記、依頼テンプレを M4.2 結線に更新 |
