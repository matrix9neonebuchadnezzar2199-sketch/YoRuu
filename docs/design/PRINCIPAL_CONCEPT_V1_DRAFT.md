# 元本概念 v1 ドラフト（A-2 + B-2 確定）

**日付**: 2026-05-28  
**ステータス**: DRAFT — Opus による ch10/13/16/22 正式ローリング前の Composer 整理稿  
**関連**: [`PHASE4_ROADMAP_REVISION_DRAFT_2026-05-28.md`](./PHASE4_ROADMAP_REVISION_DRAFT_2026-05-28.md)、[`../mockups/REF_IMAGE_GAP_MATRIX_v2.md`](../mockups/REF_IMAGE_GAP_MATRIX_v2.md)

---

## 1. 用語定義（確定）

| 概念 | 定義 | 増減トリガ |
|------|------|-----------|
| **principal** | 累積入金 − 累積出金 | `DEPOSIT` / `WITHDRAW` のみ |
| **locked_principal** | オープンポジションが拘束する元本 | open ↑ / close ↓ |
| **withdrawable_principal** | principal − locked_principal | 派生（UI: 「追加可能元本」= **B-2** YoRuu 内の自由元本） |
| **balance** | principal + 累積 PnL（実現+未実現） | 約定・マーク |
| **累積 PnL** | balance − principal | 派生 |

**UI ヒーロー（2 段）**

- 主: **balance**（3 桁カンマ、巨大表示）
- 副: **withdrawable_principal** 併記 + **累積 PnL** 段

---

## 2. ch10 データモデル（ドラフト）

### bot_state 列追加

- `principal_jpy_cents` INTEGER NOT NULL DEFAULT 0
- `locked_principal_jpy_cents` INTEGER NOT NULL DEFAULT 0

（通貨は設定に追随。USD 運用時は `_usd_cents` に読み替え — 正式章で確定）

### 新規 `principal_transactions`

| 列 | 型 | 備考 |
|----|-----|------|
| id | INTEGER PK | |
| ts_utc | TEXT | ISO8601 |
| kind | TEXT | `DEPOSIT` \| `WITHDRAW` |
| amount_cents | INTEGER | 正 |
| balance_before_cents / balance_after_cents | INTEGER | 監査 |
| principal_before_cents / principal_after_cents | INTEGER | 監査 |
| note | TEXT | 任意 |

### SSE（M4.5 想定）

- 新規イベント `principal_changed` — B1 / `mock-data.js` / `api/sse/models.py` へ追補要

---

## 3. ch13 §13.2.5 D11 v2（ドラフト）

| イベント | principal | locked_principal | balance |
|----------|-----------|------------------|---------|
| 入金 | += amount | — | += amount |
| 出金 | -= amount（≤ withdrawable） | — | -= amount |
| オープン | — | += position.size | — |
| クローズ | — | -= position.size | += realized_pnl |

---

## 4. ch16 INV-D-06 v2（ドラフト）

**保存則**

`balance == principal + Σ(realized_pnl) + Σ(unrealized_pnl)`

**追加不変条件（案）**

- principal == Σ(DEPOSIT) − Σ(WITHDRAW)
- locked_principal == Σ(open position principal lock)
- withdrawable_principal == principal − locked_principal ≥ 0

---

## 5. ch22 設定（ドラフト）

| 旧 | 新 |
|----|-----|
| `initial_balance` | `initial_principal` |

起動時: 初期入金 1 行を `principal_transactions` に記録。旧キーは移行期間のみ受付。

---

## 6. REST / CLI（M4.5 スコープ）

| 種別 | パス / コマンド |
|------|----------------|
| REST | `POST /api/v1/principal/deposit`, `withdraw`, `GET /api/v1/principal` |
| CLI | `yoruu principal deposit|withdraw|show` |

---

## 7. 正式化ゲート

- [ ] Opus: ch10 v1.2 ローリング（severity 必須化を同梱可）
- [ ] Opus: ch13 D11 / ch16 INV / ch22 追補 APPROVED
- [ ] INDEX / cross-ref 整合
- [ ] 実装: M4.4〜M4.5（[`PHASE3_PARALLEL_CHAT_TEMPLATES.md`](./PHASE3_PARALLEL_CHAT_TEMPLATES.md) テンプレ 14）
