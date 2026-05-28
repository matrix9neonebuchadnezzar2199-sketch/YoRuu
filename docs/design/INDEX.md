# YoRuu 設計書 INDEX

> **目的**: 全24章の設計書ステータスと閲覧順序を管理する SSOT。各章の `APPROVED` 状態は `REVIEW_CHECKLIST_ch01-07.md` / [`REVIEW_CHECKLIST_ch08.md`](./REVIEW_CHECKLIST_ch08.md) / [`REVIEW_CHECKLIST_ch09.md`](./REVIEW_CHECKLIST_ch09.md) / [`REVIEW_CHECKLIST_ch10.md`](./REVIEW_CHECKLIST_ch10.md) / [`REVIEW_CHECKLIST_ch11.md`](./REVIEW_CHECKLIST_ch11.md) / [`REVIEW_CHECKLIST_ch12.md`](./REVIEW_CHECKLIST_ch12.md) 等で管理する。

**最終更新**: 2026-05-28  
**現在 PHASE**: **PHASE 4 着手** — M4.2 静的 UI 結線完了／PHASE 3 コード Exit（`3f17b1d`）／PHASE 1・2 **完了**  
**M1.5**: a/b/c すべて完了（2026-05-27）  
**関連**: [`00_ROADMAP.md`](./00_ROADMAP.md)、[`PHASE3_EXIT_DECLARATION.md`](./PHASE3_EXIT_DECLARATION.md)、[`PHASE3_QUALITY_AUDIT.md`](./PHASE3_QUALITY_AUDIT.md)、[`PHASE3_PARALLEL_CHAT_TEMPLATES.md`](./PHASE3_PARALLEL_CHAT_TEMPLATES.md)、[`PHASE1_M13_MIDPOINT_REVIEW.md`](./PHASE1_M13_MIDPOINT_REVIEW.md)、[`REVIEW_CHECKLIST_ch01-07.md`](./REVIEW_CHECKLIST_ch01-07.md) 〜 [`REVIEW_CHECKLIST_ch24.md`](./REVIEW_CHECKLIST_ch24.md)、[`REVIEW_CHECKLIST_appendix_a.md`](./REVIEW_CHECKLIST_appendix_a.md)、[`08_mockup_carryover.md`](./08_mockup_carryover.md)

### PHASE 3 進捗（2026-05-28）

| 指標 | 値 |
|------|-----|
| 設計書 APPROVED | **24 / 24** 章 + **付録 A** |
| UI モック | **11 / 11**（PHASE 2 完了） |
| Track 1〜4 + Exit A + テンプレ 9 | **コード完了** → [`PHASE3_EXIT_DECLARATION.md`](./PHASE3_EXIT_DECLARATION.md) |
| PHASE 4 M4.2 | **完了** — `web/static/` + `yoruu serve` + EventSource |
| PHASE 4 M4.3 | **完了** — ch10/13/16/18/22 ローリング済（`fca1306` 系 + 本バッチ） |
| PHASE 4 M4.4 | **完了** — PrincipalService + migrate + INV 拡張 |
| PHASE 4 M4.5 | **完了** — principal REST/CLI/SSE + FX API |
| PHASE 4 M4.6 | **✅ 完了** — mock-data principal/FX/HUD aggregates |
| PHASE 4 M4.7 | **✅ 完了** — `00_hud.html` 主入口 HUD |
| PHASE 4 M4.8 | **✅ 完了** — en i18n + 12 画面 serve |
| PHASE 4 M4.9 | **✅ 完了** — [`PHASE4_EXIT_DECLARATION.md`](./PHASE4_EXIT_DECLARATION.md) |
| PHASE 5 | **着手可** — ローソク足・lab 24h（仮） |
| pytest | **119** passed、カバレッジ **≈88%** |
| `fail_under` | **80**（Exit 到達、`pyproject.toml`） |
| INV 実装 | **19 / 19**（設計一致） |
| 運用残 | lab VM で **24h paper** 実運用（ハーネス済） |
| PHASE 4 前提 | `src/yoruu/web/` + `api/sse/` 前倒し済 → キックオフ [`PHASE4_KICKOFF_TEMPLATE.md`](./PHASE4_KICKOFF_TEMPLATE.md) |

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
| 3 | 状態遷移図 | [`03_state_diagram.md`](./03_state_diagram.md) | APPROVED | v1.0.1 · 2026-05-28 |
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
| 8 | UIモックアップ（11画面） | [`08_ui_mockup.md`](./08_ui_mockup.md) | APPROVED | v1.2.3 · 2026-05-28 |

</details>

<details>
<summary>第4部 詳細仕様（ch9〜14）</summary>

| # | タイトル | ファイル | ステータス | コミット |
|---|----------|----------|-----------|----------|
| 9 | ユーザー操作フロー | [`09_user_flow.md`](./09_user_flow.md) | APPROVED | `06c0398` |
| 10 | 関数呼び出し・データフォーマット・データモデル | [`10_functions_data_model.md`](./10_functions_data_model.md) | APPROVED | v1.2 · 2026-05-28 |
| 11 | 戦略ロジック（Markov + Kelly） | [`11_strategy_logic.md`](./11_strategy_logic.md) | APPROVED | v1.0.2 · 2026-05-28 |
| 12 | モード仕様（backtest / paper / simmer / live） | [`12_mode_specification.md`](./12_mode_specification.md) | APPROVED | `b73fc18` |
| 13 | ペーパー約定エンジン | [`13_paper_execution.md`](./13_paper_execution.md) | APPROVED | v1.0.5 · 2026-05-28 |
| 14 | i18n 設計 | [`14_i18n_design.md`](./14_i18n_design.md) | APPROVED | v1.0.2 · 2026-05-28 |

</details>

<details>
<summary>第5部 安全設計（ch15〜19）</summary>

| # | タイトル | ファイル | ステータス | コミット |
|---|----------|----------|-----------|----------|
| 15 | 夜間レビューフロー | [`15_nightly_review.md`](./15_nightly_review.md) | APPROVED | v1.0.2 · 2026-05-28 |
| 16 | 不変条件 | [`16_invariants.md`](./16_invariants.md) | APPROVED | v1.0.3 · 2026-05-28 |
| 17 | リスクマトリクス | [`17_risk_matrix.md`](./17_risk_matrix.md) | APPROVED | `ec08886` |
| 18 | エラーハンドリング + ログトリアージ | [`18_error_handling.md`](./18_error_handling.md) | APPROVED | v1.1.1 · 2026-05-28 |
| 19 | キルスイッチ + 2段階確認 | [`19_kill_switch.md`](./19_kill_switch.md) | APPROVED | `ec08886` |

</details>

<details>
<summary>第6部 運用設計（ch20〜24）</summary>

| # | タイトル | ファイル | ステータス | コミット |
|---|----------|----------|-----------|----------|
| 20 | 監査ログ | [`20_audit_log.md`](./20_audit_log.md) | APPROVED | `7ef71ba` |
| 21 | 設定影響マトリクス | [`21_config_impact.md`](./21_config_impact.md) | APPROVED | `1117eca` |
| 22 | 設定仕様（yoruu.yaml） | [`22_config_spec.md`](./22_config_spec.md) | APPROVED | v1.0.5 · 2026-05-28 |
| 23 | テスト戦略（デプロイ・ロールバック統合） | [`23_test_strategy.md`](./23_test_strategy.md) | APPROVED | `7ef71ba` |
| 24 | Polymarket CLOB クライアント詳細 | [`24_polymarket_clob.md`](./24_polymarket_clob.md) | APPROVED | `1117eca` |

</details>

<details>
<summary>付録</summary>

| 付録 | タイトル | ファイル | ステータス | コミット |
|------|----------|----------|-----------|----------|
| A | 用語集 | [`appendix_a_glossary.md`](./appendix_a_glossary.md) | APPROVED | `1117eca` |

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
- ch8〜15: [`REVIEW_CHECKLIST_ch08.md`](./REVIEW_CHECKLIST_ch08.md) 〜 [`REVIEW_CHECKLIST_ch15.md`](./REVIEW_CHECKLIST_ch15.md)
- ch16〜20: 各章末尾 + M1.5 コミット列（上表）
- ch3: [`REVIEW_CHECKLIST_ch03.md`](./REVIEW_CHECKLIST_ch03.md)
- ch21 / ch22 / ch24: [`REVIEW_CHECKLIST_ch21.md`](./REVIEW_CHECKLIST_ch21.md)、[`REVIEW_CHECKLIST_ch22.md`](./REVIEW_CHECKLIST_ch22.md)、[`REVIEW_CHECKLIST_ch24.md`](./REVIEW_CHECKLIST_ch24.md)
- 付録 A: [`REVIEW_CHECKLIST_appendix_a.md`](./REVIEW_CHECKLIST_appendix_a.md)
- ロードマップ: [`00_ROADMAP.md`](./00_ROADMAP.md)
- PHASE 3 監査: [`PHASE3_QUALITY_AUDIT.md`](./PHASE3_QUALITY_AUDIT.md)

**2026-05-27 補助レビュー反映**（ch1〜7 本文）: 第3章 3.3、第7章 7.2.1、第6章 StateMachine → コミット `49fccec`  
**2026-05-27 一次レビュー**: ch1〜7 `APPROVED` → コミット `2623330`  
**2026-05-27 M1.0**: 24章再編・ロードマップ SSOT → `bce8a03`  
**2026-05-27 M1.2**: 第8章 `APPROVED`（v1.2.1、§8.26.5 7項目）→ `832ad1e`  
**2026-05-27 M1.3**: 第9章 `APPROVED`（§9.16.5 7項目）→ `06c0398`
