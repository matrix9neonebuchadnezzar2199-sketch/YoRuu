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
| 5 | ローソク足: **後続フェーズ**、HUD はプレースホルダのみ |

### 元本概念（A-2 + B-2 確定）

| 概念 | 定義 |
|------|------|
| **principal** | 累積入金 − 累積出金（入出金操作のみ増減） |
| **locked_principal** | オープンポジションが消費中の元本 |
| **withdrawable_principal** | principal − locked_principal（YoRuu 内でポジションに振り向け可能な元本） |
| **balance** | principal + 累積 PnL（実現 + 未実現） |
| **累積 PnL** | balance − principal（派生） |

設計章ドラフト: [`../design/PRINCIPAL_CONCEPT_V1_DRAFT.md`](../design/PRINCIPAL_CONCEPT_V1_DRAFT.md)

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

## 未決（ロードマップ確定時に閉じる）

| ID | 論点 | 推奨 |
|----|------|------|
| **C** | 現行 `00_ROADMAP.md` の PHASE 4 定義範囲 | **回答済み** — 下記 |
| **D** | `index.html` vs `00_hud.html` | **I-1 推奨**（Hub 温存 + HUD リンク 1 行） |

### 確認事項 C — 回答（リポジトリ実態）

`00_ROADMAP.md` PHASE 4 には **二重定義** がある。

1. **進捗表**（2026-05-28 更新）: M4.1〜M4.2 ✅、**M4.3「REST 初期データ結線」が次**
2. **旧マイルストーン表**（L182-190）: M4.2=ダッシュボード+Markov、M4.3=夜間 Apply… の **PHASE 2 時代の分割**

→ **M4.2 までがコード上完了**。M4.3 以降は **案 Z 改訂（M4.3〜M4.9）で置換**する。詳細: [`../design/PHASE4_ROADMAP_REVISION_DRAFT_2026-05-28.md`](../design/PHASE4_ROADMAP_REVISION_DRAFT_2026-05-28.md)

---

## 次ステップ（案 Z）

1. ロードマップ改訂草案の承認  
2. テンプレ 14 投入（設計章追補 → 実装マイルストン）  
3. ch10/13/16/22 正式ローリング（Opus）  
4. `mock-data.js` 拡張 → `00_hud.html` スケルトン
