# 参照画像 ↔ HUD 突き合わせ表（確定版 v2）

**日付**: 2026-05-28  
**ステータス**: 確定 — マスター方針反映済み（アプローチ B・A-2/B-2・案 Z）  
**参照画像**: [`reference/hermes-hud-ref.png`](reference/hermes-hud-ref.png)  
**初版**: [`REF_IMAGE_GAP_MATRIX_v1.md`](REF_IMAGE_GAP_MATRIX_v1.md)

---

## 確定方針サマリ

| # | 確定内容 |
|---|---------|
| 1 | **新規 `00_hud.html` 追加、既存 10 画面温存**。HUD は既存パーツの集約ビューア（ロジック重複なし） |
| 2 | ヒーロー: **残高（追加可能元本併記）+ 累積 PnL** の 2 段表示 |
| 3 | 夜間ループ: **カウントダウンのみ**、詳細は `03_nightly_review.html` |
| 4 | 通知枠: **SSE 接続 / システム稼働 / その他** を複数枠で全部表示（Telegram 不採用） |
| 5 | ローソク足: **PHASE 5**、HUD はプレースホルダのみ |
| **D** | **I-1 確定**: Hub（`index.html`）と HUD（`00_hud.html`）温存・相互リンク。**主入口は `00_hud.html`**（README/ブックマーク運用） |

### 元本概念（A-2 + B-2 確定）

| 概念 | 定義 |
|------|------|
| **principal** | 累積入金 − 累積出金（入出金操作のみ増減） |
| **locked_principal** | オープンポジションが消費中の元本 |
| **withdrawable_principal** | principal − locked_principal（YoRuu 内でポジションに振り向け可能な元本） |
| **balance** | principal + 累積 PnL（実現 + 未実現） |
| **累積 PnL** | balance − principal（派生） |

設計章ドラフト: [`../design/PRINCIPAL_CONCEPT_V1_DRAFT.md`](../design/PRINCIPAL_CONCEPT_V1_DRAFT.md)  
ロードマップ: [`../design/PHASE4_ROADMAP_v1.md`](../design/PHASE4_ROADMAP_v1.md)

---

## HUD 配置 ↔ データソース（`00_hud.html`）

| HUD 配置 | 参照画像要素 | データソース（既存パーツ） | 難度 |
|----------|-------------|---------------------------|------|
| ヘッダー | ブランド / BTC 5分足 / 現在時刻 | 静的 + `Date`（ET 表示） | 低 |
| ヒーロー | 巨大残高 + 追加可能元本併記 + PnL 段 | `mock-data.js` `balance.*` + 新規 principal 系 | 中 |
| 統計 4 枚 | 取引回数 / 勝率 / 最大勝利 / 平均取引額 | `win_rate` + 新規累計フィールド | 中 |
| マルコフ | 遷移図 / p / 持続性 / ρ / ギャップ / リワード | `markov.*` + `09_markov_live` 表示流用 | 中 |
| 戦略式 | Q=P-q>e / Kelly / ウィンドウ説明 | 静的 + `current_position` 数値 | 低 |
| シグナル | シグナル / エントリー済 / 期限切れ | **新規** `signal_counts` | 中 |
| チャート枠 | ローソク | **プレースホルダ** "Coming soon" | 極低 |
| システム複数枠 | 頭脳 / 本体 / 環境 / SSE+稼働+その他 | 静的 + `EventSource.readyState` 等 | 中 |
| 夜間 CD | 次回レビュー | `hub_meta.nightly_*` + 03 リンク | 低 |
| トレードミニ | オンライン + 約定行 | `recent_trades` | 低 |
| 入金ボタン（Q3） | 参照画像外・必須 | `POST /api/v1/principal/deposit` | 中 |
| フッターティッカー | BTC/ETH/SOL + システム指標 | 新規（市場価格ソースは後続） | 中 |

**実装原則**: `shared/mock-data.js` を正本参照。`01`〜`10` の DOM/JS は変更しない。HUD はレイアウト再配置のみ。

---

## 初版からのギャップ評価（01_dashboard 参照）

初版 10 行表の **×/△** 評価は維持。対応方針は **01 の改修ではなく `00_hud` 新設** に集約。

---

## 確定済み（2026-05-28）

| ID | 論点 | 結果 |
|----|------|------|
| **C** | `00_ROADMAP` PHASE 4 範囲 | M4.3〜M4.9 に再編、`00_ROADMAP` 本表差し替え済 |
| **D** | Hub vs HUD | **I-1 確定**（上表） |
| **P/Q** | M4.6/M4.7 順序 | **案 P**（M4.6 → M4.7、案 Q 不採用） |

---

## 次ステップ

1. **M4.3** Opus: ch10 v1.2 ローリング追補（principal スキーマ + severity）  
2. M4.4〜M4.9 テンプレ 14 順次投入
