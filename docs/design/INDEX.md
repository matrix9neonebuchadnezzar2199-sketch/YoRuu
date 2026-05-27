# YoRuu 設計書 INDEX

> このファイルは設計書全体の目次である。各章のステータスとファイル名を一覧化する。

## 凡例

| ステータス | 意味 |
|---|---|
| `DRAFT` | 執筆中・未確認 |
| `REVIEW_PENDING` | レビュー待ち |
| `APPROVED` | レビュー完了・承認済 |
| `NOT_STARTED` | 未着手 |

## 現在生成済みの章 (第1〜7章)

| 章 | タイトル | ファイル | ステータス | サマリ |
|---|---|---|---|---|
| 1 | 概要 | [`01_overview.md`](./01_overview.md) | APPROVED | システム目的・スコープ・用語集 |
| 2 | アーキテクチャ概観 | [`02_architecture.md`](./02_architecture.md) | APPROVED | 層構造・技術スタック・ディレクトリ |
| 3 | 状態遷移図 | [`03_state_diagram.md`](./03_state_diagram.md) | APPROVED | 9状態の定義と遷移ルール |
| 4 | データフロー図 (DFD) | [`04_data_flow.md`](./04_data_flow.md) | APPROVED | DFD レベル0/1、データ寿命表 |
| 5 | 信頼境界線図 | [`05_trust_boundary.md`](./05_trust_boundary.md) | APPROVED | 4ゾーン定義、境界検証ルール |
| 6 | シーケンス図 | [`06_sequence.md`](./06_sequence.md) | APPROVED | 7ユースケースの時系列 |
| 7 | インプット/アウトプット図 | [`07_io_diagram.md`](./07_io_diagram.md) | APPROVED | 30 I/O 項目、検証マトリクス |

## 今後の章 (第8〜24章)

<details>
<summary>未着手の章一覧をクリックで展開</summary>

| 章 | タイトル | ステータス |
|---|---|---|
| 8 | UI モックアップ一式 | NOT_STARTED |
| 9 | ユーザー操作フロー | NOT_STARTED |
| 10 | 関数呼び出し図 + データフォーマット | NOT_STARTED |
| 11 | データモデル | NOT_STARTED |
| 12 | 戦略ロジック詳細 | NOT_STARTED |
| 13 | 動作モード仕様 | NOT_STARTED |
| 14 | ペーパー約定エンジン仕様 | NOT_STARTED |
| 15 | 夜間レビューフロー | NOT_STARTED |
| 16 | 不変条件一覧 | NOT_STARTED |
| 17 | リスク・セーフガード一覧表 | NOT_STARTED |
| 18 | エラーハンドリング図 + ログレベル | NOT_STARTED |
| 19 | キル・スイッチ + 二重承認設計 | NOT_STARTED |
| 20 | 監査ログ設計 | NOT_STARTED |
| 21 | 設定変更影響範囲マトリクス | NOT_STARTED |
| 22 | 設定ファイル仕様 | NOT_STARTED |
| 23 | テスト戦略マトリクス | NOT_STARTED |
| 24 | デプロイ・ロールバック手順 | NOT_STARTED |

</details>

## レビュー基準

各章は [REVIEW_CHECKLIST_ch01-07.md](./REVIEW_CHECKLIST_ch01-07.md) の12観点で評価する。

**2026-05-27 補助レビュー反映**: 第3章 3.3（backtest ガード）、第7章 7.2.1（PERSISTENCE 案α）、第6章 StateMachine 参加者、第8章 UI 予約 → [`08_mockup_carryover.md`](./08_mockup_carryover.md)。

**2026-05-27 一次レビュー**: 第1〜7章を `APPROVED` に昇格（折衷案: マスター目視確認後）。次: M1.0 ロードマップ整備 → 第8章設計（PHASE 1 M1.2）。