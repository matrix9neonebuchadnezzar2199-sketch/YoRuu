# 元本概念 v1（ADOPTED — H-1 / U-2）

**日付**: 2026-05-28  
**ステータス**: **ADOPTED** — ch10 v1.2 / ch13 v1.0.5 にローリング済  
**正本**: [`10_functions_data_model.md`](./10_functions_data_model.md) §10.3.3/§10.3.14、[`13_paper_execution.md`](./13_paper_execution.md) §13.2.5/§13.2.6

---

## 1. 用語（A-2 + B-2 + H-1）

| 概念 | 定義 | DB |
|------|------|-----|
| **principal** | 累積入金 − 累積出金 | `bot_state.principal` |
| **balance** | 自由資金（v1 維持、open で減算） | `bot_state.balance` |
| **locked_principal** | オープン size 合計 | **派生**（列なし） |
| **withdrawable_principal** | `balance` | 派生 |
| **total_assets** | `balance + locked_principal` | 派生（HUD ヒーロー） |
| **累積 PnL** | `total_assets − principal` | 派生 |

**U-2**: 金額は REAL（USD）。cents 化は PHASE 5 以降の別マイルストン候補。

---

## 2. D11 v2（H-1）

| イベント | balance | principal |
|---------|---------|-----------|
| open | `-= size_usd` | — |
| close | `+= size_usd + pnl` | — |
| deposit | `+= amount` | `+= amount` |
| withdraw | `-= amount` | `-= amount` |

---

## 3. UI（E-1 / F-2）

- 内部: USD のみ
- HUD: JPY/USD 表示トグル + `GET /api/v1/fx/usd_jpy`

---

## 4. 次: ch16 INV-D-06 v2

ch16 ローリング追補で正式化（M4.3 継続）。
