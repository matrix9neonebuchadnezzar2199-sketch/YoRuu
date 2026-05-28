# PHASE 4 Exit 宣言（HUD + 元本 + 静的 UI）

> **日付**: 2026-05-28  
> **対象**: `f:\Cursor\YoRuu` / `main`  
> **前提コミット**: `feaa328`（M4.8–M4.9 Exit）

---

## 1. 宣言

**PHASE 4 の計画スコープ（M4.1〜M4.9）は完了**とする。

実装・自動テスト・静的 UI serve で検証可能な項目はすべて達成した。設計章ドラフト（ch10 v1.2 / ch13 v1.0.5 / ch16 v1.0.3 / ch18 v1.1.1 / ch22 v1.0.5）の**本体ファイルへの最終マージ**は PHASE 5 内 ADR で扱う（W-2 ローリングドラフトは M4.3 で承認済み）。

---

## 2. Exit Criteria 対応表

| # | 基準 | 状態 | 根拠 |
|---|------|------|------|
| 1 | FastAPI + SSE 契約（M4.1） | ✅ | `dea96e0` — 12 SSE events、Pydantic registry |
| 2 | 静的モック + EventSource（M4.2） | ✅ | `02edfa0` / `build_web_static.py` |
| 3 | 設計章追補・元本概念（M4.3） | ✅ | `cbe24f3` — ch10/13/16/18/22 ローリングドラフト |
| 4 | 元本コア（M4.4） | ✅ | `b5c942f` — migrate / PrincipalService / INV-D-06 v2 + 07/08/09 |
| 5 | principal REST/CLI/SSE + FX API（M4.5） | ✅ | `87747cb` — principal/fx routes、CLI、SSE #12 |
| 6 | `mock-data.js` 拡張（M4.6） | ✅ | `18e5e14` — principal 5 値、FX mock、HUD aggregates |
| 7 | `00_hud.html` 主入口 HUD（M4.7） | ✅ | `a555097` — I-1 相互リンク、チャート placeholder |
| 8 | en i18n 完備 + serve smoke（M4.8） | ✅ | en.json 手訳、`build_locales --check` placeholder lint、12 画面 200 |
| 9 | 行カバレッジ ≥ 80%（ch23） | ✅ | `pytest` **142** passed、≈**88%** |
| 10 | Hub 温存（I-1） | ✅ | `index.html` + `00_hud.html` 双方向リンク |
| 11 | lab 24h paper **実運用** | ⏳ PHASE 5 | ハーネスは PHASE 3 完了（`yoruu paper-24h`） |
| 12 | ローソク足 + エントリーマーカー | ⏳ PHASE 5 | HUD placeholder のみ |

---

## 3. 主要コミット列（PHASE 4）

| コミット | マイルストン | 内容 |
|----------|-------------|------|
| `dea96e0` | M4.1 | FastAPI + SSE 契約 |
| `02edfa0` | M4.2 | 静的モック EventSource |
| `cbe24f3` | M4.3 | 設計章ローリング |
| `b5c942f` | M4.4 | 元本コア |
| `87747cb` | M4.5 | principal API/CLI/SSE/FX |
| `18e5e14` | M4.6 | mock-data principal/FX |
| `a555097` | M4.7 | `00_hud.html` |
| `feaa328` | M4.8–M4.9 | en i18n、serve、Exit 宣言、v0.5.0 |

---

## 4. 設計 SSOT（ローリング状態）

| 章 | ドラフト | 本体反映 |
|----|----------|----------|
| ch10 v1.2 | `archive/principal-rollout-2026-05-28/ch10_v1.2_ROLLING_DRAFT.md` | M4.3 本体反映済み、M5.1 archive |
| ch13 v1.0.5 | `archive/.../ch13_v1.0.5_ROLLING_DRAFT.md` | 同上 |
| ch16 v1.0.3 | `archive/.../ch16_v1.0.3_ROLLING_DRAFT.md` | 同上 |
| ch18 v1.1.1 | `archive/.../ch18_v1.1.1_ROLLING_DRAFT.md` | 同上 |
| ch22 v1.0.5 | `archive/.../ch22_v1.0.5_ROLLING_DRAFT.md` | 同上 |

正本ロードマップ: [`PHASE4_ROADMAP_v1.md`](./PHASE4_ROADMAP_v1.md)（案 P / I-1 / W-2 / X-2 確定）

---

## 5. PHASE 5 への引き渡し

| 項目 | 状態 |
|------|------|
| `docs/mockups/00_hud.html` | **主入口**（`yoruu serve` → `/` → `/pages/00_hud.html`） |
| `docs/mockups/shared/mock-data.js` | principal / FX / SSE #12 mock 完備 |
| `src/yoruu/execution/principal_service.py` | REST/CLI/SSE 接続済 |
| `GET /api/v1/fx/usd_jpy` | 実 API + mock 整合 |
| 設計ドラフト | 本体マージは PHASE 5 最初の ADR で実施推奨 |

**PHASE 5 候補（仮）**

- M5.x ローソク足 + HUD チャート枠の実データ
- lab 24h paper + HUD 観察セット
- ch10 全 SSE `severity` 必須化（PHASE 3 繰越）

---

## 6. 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-05-28 | 初版（PHASE 4 Exit 宣言） |
