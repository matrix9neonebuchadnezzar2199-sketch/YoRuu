# PHASE 5 Exit 宣言（観察・統合）— **DRAFT（未確定）**

> **日付**: 2026-05-28（起草） / **確定予定**: M5.6 lab 24h 完了後  
> **対象**: `f:\Cursor\YoRuu` / `main`  
> **前提コミット**: `99ba647`（M5.1 archive + M5.2 OHLC SSOT）  
> **ステータス**: **DRAFT** — M5.6 結果・v0.6.0 bump は未反映。本ファイルはコミット前ドラフト。

---

## 1. 宣言

**PHASE 5 の計画スコープ（M5.0〜M5.7）は完了**とする。

<!-- M5.6 完了後に確定文へ差し替え:
実装・自動テスト・lab 24h paper 実運用で検証可能な項目はすべて達成した。
-->

（M5.6 lab 24h 完了後に最終宣言文を記入）

---

## 2. Exit Criteria 対応表

| # | 基準 | 状態 | 根拠 |
|---|------|------|------|
| 1 | PHASE5 ロードマップ（M5.0） | ✅ | [`PHASE5_ROADMAP_v1.md`](./PHASE5_ROADMAP_v1.md) |
| 2 | ADR-001 + archive クリーンアップ（M5.1） | ✅ | `e383345` — ROLLING → `archive/principal-rollout-2026-05-28/` |
| 3 | ch10 OHLC SSOT §10.3.15（M5.2） | ✅ | `e383345` — v1.3.0、§10.6.14 |
| 4 | `GET /api/v1/ohlc` + `OhlcProvider`（M5.3） | ✅ | `9fb57a9` — ring buffer 60、lab seed |
| 5 | HUD SVG チャート + 5s polling（M5.4） | ✅ | `9fb57a9` — `00_hud.html`、`labOhlcBars` fallback |
| 6 | SSE 全 12 イベント `severity` 必須（M5.5） | ✅ | `9fb57a9` — models + fixtures |
| 7 | lab 24h paper **実運用**（M5.6） | ⏳ | レポート: `docs/operations/LAB_PAPER_24H_*.md`（**未実施**） |
| 8 | 行カバレッジ ≥ 80%（ch23） | ✅ | `pytest` **146** passed、≈**88%**（M5.7 確定時に再計測） |
| 9 | `pyproject.toml` v0.6.0 | ⏳ | M5.7 最終コミットで bump（現行 **0.5.0** のまま） |

### M5.6 実運用サマリ（24h 完了後に記入）

| Field | Value |
|-------|-------|
| Run ID | `<!-- YYYY-MM-DD-lab -->` |
| Start (UTC) | |
| End (UTC) | |
| Completed | |
| Cycles | `<!-- expected ≈ 288 at interval 300s -->` |
| INV violations | `<!-- expected 0 -->` |
| Critical errors | |
| Report path | `docs/operations/LAB_PAPER_24H_<!-- date -->.md` |
| `git rev-parse HEAD` | |

---

## 3. 主要コミット列（PHASE 5）

| コミット | マイルストン | 内容 |
|----------|-------------|------|
| `9fb57a9` | M5.3–M5.5 | OHLC API、HUD chart、SSE severity |
| `e383345` | M5.1–M5.2 | archive ROLLING、ch10 v1.3.0 OHLC SSOT |
| `aa85261` | — | 表記整理（オリジナル / 外部 AI） |
| `feaa328` | （PHASE 4） | v0.5.0、PHASE 4 Exit |
| `<!-- M5.7 commit -->` | M5.7 | Exit 宣言確定 + v0.6.0 |

---

## 4. 設計 SSOT 状態

| 項目 | 状態 |
|------|------|
| ch10 v1.3.0 | §10.3.15 OHLC、§10.6.14 REST |
| principal archive | `docs/design/archive/principal-rollout-2026-05-28/` |
| ADR-001 | Accepted、archive パス明記 |
| lab 24h テンプレ | [`../operations/LAB_PAPER_24H_TEMPLATE.md`](../operations/LAB_PAPER_24H_TEMPLATE.md) |

---

## 5. PHASE 6 への引き渡し

| 項目 | 状態 |
|------|------|
| HUD + OHLC | `yoruu serve` → `/pages/00_hud.html`、`GET /api/v1/ohlc` |
| paper 24h ハーネス | `yoruu paper-24h --hours 24 --interval-sec 300` |
| ペーパー運用 14 日 | PHASE 6 M6.1–M6.3（[`00_ROADMAP.md`](./00_ROADMAP.md)） |

**PHASE 6 候補（仮）**

- 実市場データでの paper 運用 + 日次夜間レビューサイクル
- OHLC 永続化 / Binance 本接続の要否判断
- 最大ドローダウン・勝率の運用 KPI 記録

---

## 6. 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-05-28 | DRAFT 初版（M5.6 結果欄プレースホルダ） |
| <!-- --> | M5.6 完了後: サマリ埋め込み、宣言確定、v0.6.0 |
