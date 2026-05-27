# PHASE 2 着手キックオフテンプレ

> **目的**: PHASE 2（UI モック）の Composer 2.5 への引き渡しテンプレを SSOT 化する。  
> **作成**: 2026-05-27（ch15 APPROVED 直後、Opus 設計チャットから引き渡し）  
> **適用ルール**: [`.cursor/rules/52-yoruu-model-routing.mdc`](../../.cursor/rules/52-yoruu-model-routing.mdc) §1, §M2.1〜M2.3, §PHASE ゲート

> **PHASE 2 完了（2026-05-27）**: M2.1〜M2.3 完了（`c4e20a4` / `9b4ce17` / `4e2395b`）。本ファイル §2/§3 は **PHASE 4 転用時に差し替え** — 新規着手は [`PHASE4_KICKOFF_TEMPLATE.md`](./PHASE4_KICKOFF_TEMPLATE.md) を正本とする。

## 1. 着手前マスター判断（必須）

**2026-05-27 実行結論**: マスター判断 **(B) 並行** — M1.5a と PHASE 2 M2.1 を別チャットで実施し、PHASE 2 は同日完了。

Composer 2.5 への依頼前に、以下 2 点をマスターが明示すること:

| 判断 | 選択肢 |
|------|--------|
| **PHASE 1 残務との関係** | (A) 逐次（M1.5a→b→c→付録A 完了後）／(B) 並行（M1.5a と PHASE 2 M2.1 を別チャットで） |
| **モックデータシナリオ** | `normal` を既定で確定、`drawdown` / `winning_streak` の 2 シナリオを M2.1 時点で同梱するか PHASE 4 まで遅延するか |

並行（B）の場合、Cursor のチャット切替コストとマスターレビュー帯域がボトルネックになる。**既定推奨は (A) 逐次**（規約 §3）。

## 2. 引き渡し SSOT 一覧

Composer 2.5 が読むべき設計書（着手順、`@` で添付）:

| # | SSOT | 役割 |
|---|------|------|
| 1 | [`08_ui_mockup.md`](./08_ui_mockup.md) §8.25 | M2.1〜M2.3 実装順序・共通実装事項・検証チェックリスト |
| 2 | [`08_ui_mockup.md`](./08_ui_mockup.md) §8.4 / §8.5 / §8.6 / §8.7 / §8.8 / §8.9 / §8.22 | カラー・レイアウト・サイドバー・コマンドパレット・i18n・SSE・a11y |
| 3 | [`08_ui_mockup.md`](./08_ui_mockup.md) §8.11〜§8.21 | 各画面 11 件の仕様（ハブ + 10 画面） |
| 4 | [`14_i18n_design.md`](./14_i18n_design.md) §14.4 / §14.10 | 辞書配置・翻訳キー一覧 |
| 5 | [`15_nightly_review.md`](./15_nightly_review.md) §15.4.8 | 完全サンプル JSON（`mock-data.js` 固定値の元データ） |
| 6 | [`15_nightly_review.md`](./15_nightly_review.md) §15.6 / §15.7 / §15.12.4 | 提案 JSON 雛形・差分プレビュー仕様・PHASE 2 引き継ぎ |
| 7 | [`10_functions_data_model.md`](./10_functions_data_model.md) §10.3 / §10.6 | SSE 契約・REST スキーマ（モックは契約形だけ模倣） |
| 8 | [`12_mode_specification.md`](./12_mode_specification.md) | モードバッジ色（`--mode-paper/simmer/live/backtest`） |

## 3. Composer 2.5 への依頼テンプレ（コピペ用）

### 3.1 M2.1 — 共通基盤 + 主要画面

```
[実装] PHASE 2 M2.1: 共通基盤 + ハブ + Dashboard + 取引履歴。

スコープ:
- docs/mockups/shared/{style.css, i18n.js, mock-data.js, sidebar.js, palette.js}
- docs/mockups/index.html（ハブ）
- docs/mockups/01_dashboard.html
- docs/mockups/02_trade_log.html

SSOT:
@docs/design/08_ui_mockup.md §8.4 §8.5 §8.6 §8.7 §8.8 §8.9 §8.22 §8.25
@docs/design/14_i18n_design.md §14.4 §14.10
@docs/design/PHASE2_KICKOFF_TEMPLATE.md

制約:
- 外部 CDN / npm ゼロ（オフライン動作）
- Vanilla JS、Vanilla CSS（フレームワーク禁止）
- ヘッダーコメント規約 §8.2.3 を全 HTML に
- mock-data.js は `normal` シナリオを既定、他は枠だけ確保
- 各 HTML は data-i18n 属性必須、ja 辞書のみ実体、en は空 JSON

完了基準: §8.25.3 検証チェックリスト 10 項目すべて pass。
仕上げ: 開発日記追記 + commit + push。
```

### 3.2 M2.2 — レビュー・分析系

```
[実装] PHASE 2 M2.2: 03_nightly_review + 05_strategy_history + 09_markov_live。

スコープ:
- docs/mockups/03_nightly_review.html
- docs/mockups/05_strategy_history.html
- docs/mockups/09_markov_live.html
- docs/mockups/shared/mock-data.js（dailyReport / strategyVersions / markovLive 追加）

SSOT:
@docs/design/08_ui_mockup.md §8.14 §8.16 §8.20
@docs/design/15_nightly_review.md §15.4.8 §15.5.2 §15.6 §15.7 §15.12.4
@docs/design/PHASE2_KICKOFF_TEMPLATE.md

03_nightly_review の必達:
- §15.4.8 完全サンプル JSON を mock-data.js の dailyReport.normal に固定値で埋め込み
- §15.5.2 プロンプト雛形をコピーボタンで取得可能
- §15.6 提案 JSON 貼付テキストエリア + JSON.parse バリデーション
- §15.7 差分プレビュー（±10% 警告 / ±20% 拒否の活性条件可視化）
- §15.8 Apply 確認モーダル（二重承認 UI のみ、書込なし）

完了基準: §8.25.3 + §15.12.4 PHASE 2 項目すべて pass。
仕上げ: 開発日記追記 + commit + push。
```

### 3.3 M2.3 — 設定・運用系

```
[実装] PHASE 2 M2.3: 04_settings + 06_alerts + 07_mode_switch + 08_emergency_stop + 10_what_if。

SSOT:
@docs/design/08_ui_mockup.md §8.15 §8.17 §8.18 §8.19 §8.21
@docs/design/12_mode_specification.md
@docs/design/PHASE2_KICKOFF_TEMPLATE.md

完了基準: §8.25.3、緊急停止 2 箇所配置、live モード復帰の確認モーダル。
```

## 4. 共通の Composer 側ガード

- **設計変更を伴う場合は止めて Opus に投げ返す**（モック実装中に §8.x の仕様矛盾を発見しても、勝手に書き換えない）
- **`shared/i18n.js` の翻訳キーは §14.10 から逸脱しない**（追加が必要なら ch14 v1.0.2 ローリング候補に積む）
- **SSE イベント名・REST パスは §10.3 / §10.6 と一致**（PHASE 4 で繋ぐとき再利用する契約）
- **JSON サンプルは §15.4.8 をそのままコピー**（PHASE 3 で `NightlyReporter.generate()` の出力サンプルとしても利用）

## 5. ロードマップ更新タイミング

| 完了マイルストーン | 更新先 |
|---|---|
| M2.1 完了 | `00_ROADMAP.md` PHASE 2 進捗、`INDEX.md` PHASE 注記 |
| M2.2 完了 | 同上 + 開発日記に夜間レビュー画面のスクショ説明 |
| M2.3 完了 | PHASE 2 全体 100%、PHASE 3 着手判断 |
