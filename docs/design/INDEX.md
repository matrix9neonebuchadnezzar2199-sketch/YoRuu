# YoRuu 設計書 INDEX

> **目的**: 全24章の設計書ステータスと閲覧順序を管理する SSOT。各章の `APPROVED` 状態は `REVIEW_CHECKLIST_ch01-07.md` / [`REVIEW_CHECKLIST_ch08.md`](./REVIEW_CHECKLIST_ch08.md) / [`REVIEW_CHECKLIST_ch09.md`](./REVIEW_CHECKLIST_ch09.md) / [`REVIEW_CHECKLIST_ch10.md`](./REVIEW_CHECKLIST_ch10.md) / [`REVIEW_CHECKLIST_ch11.md`](./REVIEW_CHECKLIST_ch11.md) / [`REVIEW_CHECKLIST_ch12.md`](./REVIEW_CHECKLIST_ch12.md) 等で管理する。

**最終更新**: 2026-05-27  
**現在 PHASE**: PHASE 1（M1.5 設計）＋ **PHASE 2 M2.2 完了**（UI モック 6/11 画面）  
**関連**: [`00_ROADMAP.md`](./00_ROADMAP.md)、[`PHASE1_M13_MIDPOINT_REVIEW.md`](./PHASE1_M13_MIDPOINT_REVIEW.md)、[`REVIEW_CHECKLIST_ch01-07.md`](./REVIEW_CHECKLIST_ch01-07.md) 〜 [`REVIEW_CHECKLIST_ch15.md`](./REVIEW_CHECKLIST_ch15.md)、[`08_mockup_carryover.md`](./08_mockup_carryover.md)

### PHASE 1 進捗（設計書 APPROVED 章数）

| 指標 | 値 |
|------|-----|
| APPROVED | **15 / 24** 章（ch1〜15） |
| M1.3 進捗 | **6 / 6 完了**（ch9〜14） |
| M1.4 進捗 | **1 / 1 完了**（ch15 APPROVED） |
| 現在マイルストーン | **M1.5**（ch16〜24 + 付録 A）／PHASE 2 **M2.3 次** |
| 次の Exit | 全24章 APPROVED（PHASE 1 完了） |

---

## 凡例

| ステータス | 意味 |
|---|---|
| `APPROVED` | レビュー完了・承認済 |
| `REVIEW_PENDING` | レビュー待ち |
| `DRAFT` | 執筆中 |
| `PENDING` | 未着手 |

---

## メイン章一覧（ch1〜7）

| # | タイトル | ファイル | ステータス | コミット |
|---|----------|----------|-----------|----------|
| 1 | 概要 | [`01_overview.md`](./01_overview.md) | APPROVED | `2623330` |
| 2 | アーキテクチャ | [`02_architecture.md`](./02_architecture.md) | APPROVED | `2623330` |
| 3 | 状態遷移図 | [`03_state_diagram.md`](./03_state_diagram.md) | APPROVED | `2623330` |
| 4 | データフロー図 | [`04_data_flow.md`](./04_data_flow.md) | APPROVED | `2623330` |
| 5 | 信頼境界線図 | [`05_trust_boundary.md`](./05_trust_boundary.md) | APPROVED | `2623330` |
| 6 | シーケンス図 | [`06_sequence.md`](./06_sequence.md) | APPROVED | `2623330` |
| 7 | 入出力図 | [`07_io_diagram.md`](./07_io_diagram.md) | APPROVED | `2623330` |

---

## 後続章（ch8〜24）

<details>
<summary>第3部 UI設計（ch8）</summary>

| # | タイトル | ファイル | ステータス | コミット |
|---|----------|----------|-----------|----------|
| 8 | UIモックアップ（11画面） | [`08_ui_mockup.md`](./08_ui_mockup.md) | APPROVED | `832ad1e` |

</details>

<details>
<summary>第4部 詳細仕様（ch9〜14）</summary>

| # | タイトル | ファイル | ステータス | コミット |
|---|----------|----------|-----------|----------|
| 9 | ユーザー操作フロー | [`09_user_flow.md`](./09_user_flow.md) | APPROVED | `06c0398` |
| 10 | 関数呼び出し・データフォーマット・データモデル | [`10_functions_data_model.md`](./10_functions_data_model.md) | APPROVED | `1bdb84c` |
| 11 | 戦略ロジック（Markov + Kelly） | [`11_strategy_logic.md`](./11_strategy_logic.md) | APPROVED | `d405f0c` |
| 12 | モード仕様（backtest / paper / simmer / live） | [`12_mode_specification.md`](./12_mode_specification.md) | APPROVED | `b73fc18` |
| 13 | ペーパー約定エンジン | [`13_paper_execution.md`](./13_paper_execution.md) | APPROVED |
| 14 | i18n 設計 | [`14_i18n_design.md`](./14_i18n_design.md) | APPROVED |

</details>

<details>
<summary>第5部 安全設計（ch15〜19）</summary>

| # | タイトル | ファイル | ステータス |
|---|----------|----------|-----------|
| 15 | 夜間レビューフロー | [`15_nightly_review.md`](./15_nightly_review.md) | APPROVED |
| 16 | 不変条件 | `16_invariants.md` | PENDING |
| 17 | リスクマトリクス | `17_risk_matrix.md` | PENDING |
| 18 | エラーハンドリング + ログトリアージ | `18_error_handling.md` | PENDING |
| 19 | キルスイッチ + 2段階確認 | `19_kill_switch.md` | PENDING |

</details>

<details>
<summary>第6部 運用設計（ch20〜24）</summary>

| # | タイトル | ファイル | ステータス |
|---|----------|----------|-----------|
| 20 | 監査ログ | `20_audit_log.md` | PENDING |
| 21 | 設定影響マトリクス | `21_config_impact.md` | PENDING |
| 22 | 設定仕様（yoruu.yaml） | `22_config_spec.md` | PENDING |
| 23 | テスト戦略（デプロイ・ロールバック統合予定） | `23_test_strategy.md` | PENDING |
| 24 | Polymarket CLOB クライアント詳細 | `24_polymarket_clob.md` | PENDING |

</details>

<details>
<summary>付録</summary>

| 付録 | タイトル | ファイル | ステータス |
|------|----------|----------|-----------|
| A | 用語集 | [`appendix_a_glossary.md`](./appendix_a_glossary.md) | PENDING |

> ch1 §1.6 は要約。用語の SSOT は付録 A（中間レビュー案 Y、2026-05-27）。

</details>

---

## 旧→新 章番号対応表（2026-05-27 再編）

> **背景**: i18n を独立章として ch14 に新設、旧 ch11「データモデル」を ch10 に統合。

| 旧章 | 旧タイトル | 新章 | 新タイトル | 備考 |
|------|------------|------|------------|------|
| 8 | UIモック | 8 | UIモックアップ（11画面） | 画面数 9 → 10 + ハブ |
| 9 | 操作フロー | 9 | ユーザー操作フロー | 変更なし |
| 10 | 関数+フォーマット | 10 | 関数呼び出し・データフォーマット・**データモデル** | データモデル節を統合 |
| 11 | データモデル | — | — | **ch10 に統合** |
| 12 | 戦略 | 11 | 戦略ロジック（Markov + Kelly） | 章番号 -1 |
| 13 | モード | 12 | モード仕様 | 章番号 -1 |
| 14 | ペーパー約定 | 13 | ペーパー約定エンジン | 章番号 -1 |
| — | — | **14** | **i18n 設計** | **新規** |
| 15〜24 | 安全・運用 | 15〜24 | 同左 | 番号維持 |
| 24 | デプロイ + ロールバック | 24 | Polymarket CLOB クライアント詳細 | 案 Y（2026-05-27） |
| — | — | 付録 A | 用語集（ch1 §1.6 から分離） | 新規 |
| 24（旧）デプロイ | — | ch23 | テスト戦略に統合予定（§23.x） | M1.5b 執筆時 |

### ch1〜7 内の cross-ref 更新（実施済み）

| 対象ファイル | 旧参照 | 新参照 | 文脈 |
|--------------|--------|--------|------|
| `01_overview.md` | 第12章 | **第11章** | persistence_threshold 用語集 |
| `03_state_diagram.md` | 第14章 | **第13章** | ペーパー約定・滞在時間 |
| `03_state_diagram.md` | 第13章 | **第12章** | backtest / mode 直交 |
| `08_mockup_carryover.md` | 第13章 | **第12章** | backtest 分離 |

---

## レビュー基準

- ch1〜7: [`REVIEW_CHECKLIST_ch01-07.md`](./REVIEW_CHECKLIST_ch01-07.md)
- ch8: [`REVIEW_CHECKLIST_ch08.md`](./REVIEW_CHECKLIST_ch08.md)
- ch9: [`REVIEW_CHECKLIST_ch09.md`](./REVIEW_CHECKLIST_ch09.md)
- ロードマップ: [`00_ROADMAP.md`](./00_ROADMAP.md)

**2026-05-27 補助レビュー反映**（ch1〜7 本文）: 第3章 3.3、第7章 7.2.1、第6章 StateMachine → コミット `49fccec`  
**2026-05-27 一次レビュー**: ch1〜7 `APPROVED` → コミット `2623330`  
**2026-05-27 M1.0**: 24章再編・ロードマップ SSOT → `bce8a03`  
**2026-05-27 M1.2**: 第8章 `APPROVED`（v1.2.1、§8.26.5 7項目）→ `832ad1e`  
**2026-05-27 M1.3**: 第9章 `APPROVED`（§9.16.5 7項目）→ `06c0398`
