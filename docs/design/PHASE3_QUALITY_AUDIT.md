# YoRuu 品質チェック + マイルストーン整合性 + 今後の作業設計

> **監査日**: 2026-05-28 07:20 JST  
> **監査主体**: Claude Opus 4.7（readonly、3 並列 explore subagent 経由）  
> **対象**: `f:\Cursor\YoRuu`（PHASE 3 scaffold 完了時点、commit `e6395a0`）  
> **方法**: PHASE 3 実装 / PHASE 2 モック / ドキュメントの 3 軸を独立並列調査。全件根拠ファイル行を引用。Karpathy §0「Trace, Don't Guess」遵守。  
> **目的**: 現状の SSOT 乖離を網羅し、PHASE 3 Exit Criteria 到達までの 4 トラック作業計画を SSOT として固定する。

---

## 0. 全体サマリ

| 監査領域 | HIGH | MED | LOW | 合計 |
|---|---:|---:|---:|---:|
| A. PHASE 3 実装 vs 設計 SSOT | **8** | 22 | 14 | 44 |
| B. PHASE 2 モック vs ch8/14/15 | **3** | 10 | 4 | 17 |
| C. ドキュメント・マイルストーン | **6** | 12 | 8 | 26 |
| **合計** | **17** | **44** | **26** | **87** |

**結論先出し**:

- コア骨格（enum / Markov / Kelly / SQLite テーブル名 / GitHub Dark / ch15 Apply UI）は SSOT と整合
- ブロッカー HIGH 17 件の内訳: PHASE 3 実装 8 件（夜間レポート JSON 完全性・不変条件網羅・StateMachine 遷移・Apply シーケンス・DDL 制約・流動性判定式）、PHASE 2 が 3 件（SSE 契約・i18n 矛盾・常時停止表示）、ドキュメントが 6 件（README 全面陳腐化・INDEX/ROADMAP 反映漏れ・日記欠落）
- 最重量タスクは **Track 1 T1.5（InvariantChecker 12 件 + hook 接続）**。安全装置が論理的に存在するが回路未接続

---

## A. PHASE 3 実装 vs 設計 SSOT 乖離

### A-HIGH（8 件 — 全件）

| # | 場所 | 問題 | 根拠 SSOT |
|---|------|------|-----------|
| A1 | `src/yoruu/data/schema.py:6-138` | DDL に **CHECK 制約と複数 INDEX が欠落**。`bot_state.state/mode`, `trades.side/mode/status/win`, `markov_state.last_direction`, `strategy_versions.applied_by`, `audit_log.actor/result` の CHECK 全欠、`idx_trades_mode_status`/`idx_markov_computed_at`/`idx_price_ticks_source_ts`/`idx_alerts_created_at`/`idx_audit_log_*` 未作成 | ch10 §10.3.3〜§10.3.12 |
| A2 | `src/yoruu/review/nightly_reporter.py:82-93` | `summary_json` が ch15 §15.4.8 と不一致。`current_strategy` に `constraints` を内包（SSOT はトップレベル）、`performance.by_state`/`markov_snapshot.history_summary`/`trade_breakdown.by_hour_jst`/`wait_reason_distribution` 未生成、`by_side` に `pnl_usd` なし | ch15 §15.4.3 / §15.4.4 / §15.4.5 / §15.4.6 / §15.4.8 |
| A3 | `src/yoruu/review/apply_validator.py:10-76` | Apply バリデーション不足。`rationale` 必須（1-500 字）未検証、トップレベル `constraints` 禁止時エラーコードが `E_NIGHTLY_006`（SSOT は `E_NIGHTLY_005`）、`version`/`metadata.*` のサイレント無視未実装、±10% 警告に `W_NIGHTLY_001` 紐付けなし、`StrategyApplyError` 未 raise | ch15 §15.6.2 / §15.6.3 / §15.7.4、ch18 |
| A4 | `src/yoruu/execution/fill_model.py:39-41` | 流動性判定が `size_usd > available * 0.5`、**SSOT は `book.ask_size_usd < size_usd`（全額必要）**。実運用で「行けるはずの注文が出せない」逆乖離 | ch13 §13.8.1 |
| A5 | `src/yoruu/safety/invariants.py:20-55` | `InvariantChecker` は 3 メソッドのみ（INV-D-03 / INV-R-01 / INV-S-02）。**ch16 定義 15 個のうち 12 個未実装**（INV-S-01/03/04/05, INV-D-01/02/04/05, INV-R-02/03/04/05, INV-M-01/02/03）。さらに `InvariantChecker` は **どこからも呼ばれていない**（grep 結果 0） | ch16 §16.2〜§16.5 |
| A6 | `src/yoruu/cli.py:172-187` + `review/nightly_reporter.py:20-96` | 夜間生成時に `StateMachine.transition(NIGHTLY_REVIEW)` が **一切呼ばれない**。SSOT は `IDLE↔NIGHTLY_REVIEW` 遷移 + 失敗時 audit | ch15 §15.3.2 / §15.3.3 / §15.3.5 |
| A7 | `src/yoruu/strategy/evaluator.py:25-122` + `cli.py:137-151` | ch11 §11.7.2 の **4 条件 AND の C4「RiskGuard.check_pre_trade」が evaluator 内にない**。CLI が evaluate 後に別途呼ぶ二段構成 → `wait_reason="risk_budget"` が evaluator 出力に出ない。実装層分担が SSOT と不一致 | ch11 §11.7.2 |
| A8 | `src/yoruu/cli.py:190-231` | `strategy apply` CLI が §15.8 Apply シーケンス未実装。`StateMachine` ガードなし、`daily_reports.proposed_strategy_json` 未更新、`performance_summary_json` 未保存、排他ロック / `E_NIGHTLY_013` なし、バックアップ失敗時 rollback / `E_NIGHTLY_011` なし | ch15 §15.8 |

### A-MED（22 件、抜粋 14）

| # | 場所 | 要点 |
|---|------|------|
| A9 | `types.py:41` | `CloseReason` に `SYSTEM_INVARIANT` 欠落（ch13 §13.4.2 は 4 値） |
| A10 | `data/database.py:196-228` | `insert_trade_open` が `markov_state_at_entry` を常に NULL（カラムは schema 存在） |
| A11 | `data/database.py:76-110` | `bot_state` 未初期化時に `RuntimeError`。ch18 は `YoRuuError` 系（`E_DB_*`）想定 |
| A12 | `strategy/markov.py:62` | フラット（`p[i] == p[i-1]`）時 `DOWN` 強制。SSOT は「前回方向を継承」 |
| A13 | `execution/fill_model.py:74-76` | close 側 `fill_price < 0.01` を `max(...,0.01)` でクリップ。SSOT は `E_FILL_004` 発火 |
| A14 | `execution/paper_executor.py:81-92` | open 時に `balance` から `size_usd` を差し引かない（close 時のみ加算）— 残高不整合リスク `[要確認: ch13/ch10]` |
| A15 | `config/settings.py:46-50` vs `execution/fill_model.py:28-32` | FillModel 既定値の二重 SSOT（ch13 §13.3.2 `0.001/150ms` vs ch22 `0.0001/80ms`）。実装は ch22 準拠 |
| A16 | `execution/paper_executor.py:55-103` | PAPER モードの `asyncio.sleep(latency)` 実待機なし。遅延後価格再取得もなし |
| A17 | `data/schema.py:42-54` | `positions.status` CHECK なし。実装は `'OPEN'` 固定 INSERT だが SSOT は `OPEN` / `CLOSING` |
| A18 | `core/state_machine.py:46-48` | `StateMachine.__init__(db)` のみ。SSOT は `event_bus: EventBus` 必須、SSE `state_changed` 未発火 |
| A19 | `safety/invariants.py:44-47` | INV-R-01 違反で `code="E_STATE_001"`。状態違反コードと混同（ch16 §16.6 は inv_id ベース） |
| A20 | `safety/invariants.py:35-38` | INV-D-03 version 不一致判定が二重条件で読み取りにくい |
| A21 | `execution/risk_guard.py:20-21` | `daily_loss_exceeded()` の値判定は SSOT 一致だが、`InvariantChecker`/`RiskGuard` から `EMERGENCY_STOP` 遷移未実装 |
| A22 | `errors.py:6-39` | 例外クラス 5 種のみ。ch18 カタログ（E_MODE_* / E_FILL_* / E_NIGHTLY_* / E_DB_*）に対応する typed exception / factory なし。`InvariantViolationError.code = "E_STATE_001"` で Invariant と State のコード衝突 |

残 8 件: NightlyReporter `pnl_usd` 集計の status フィルタ、`AppSettings` の ch22 セクション未モデル化、tests に invariants なし、etc.

### A-LOW（14 件、抜粋）

- `types.py:47-53` `WaitReason = Literal[...] | str` で **Literal 制約が完全無効化**
- `types.py:101-105` `OrderBook.source` に `"MOCK"` 追加（ch13 SSOT 不在）、`spread_ok` の `0.05` マジックナンバー
- `cli.py:32-33` `_default_strategy()` **参照ゼロの dead code**
- `cli.py:15` `YoRuuError` 未使用 import
- `cli.py:107-111` **22 close を CLI に固定埋込**（mock_market に移すべき）
- `errors.py:9` `E_YORUU_000` が ch18 カタログ未掲載
- `strategy/markov.py:30` / `cli.py:105` `window_size=20` が 2 箇所リテラル散在（定数化推奨）
- `types.py:105` / `fill_model.py:36` / `evaluator.py:102` `0.05` / `1.0` / `0.99` マジックナンバー散在

### enum 一致サマリ（参考）

| 列挙 | 判定 | 根拠 |
|------|------|------|
| `State` | 一致 | types.py:10-21 ≒ ch10 §10.7.2 L718-727 |
| `Mode` | 一致 | types.py:24-28 ≒ ch10 §10.3.3 L131 |
| `Side` | 一致 | types.py:31-33 ≒ ch10 trades CHECK L151 |
| `Direction` | 一致 | types.py:36-38 ≒ ch11 §11.3.1 |
| `CloseReason` | **不一致** | `SYSTEM_INVARIANT` 欠落（A9） |
| `WaitReason` | **型のみ不一致** | 値集合は概ね SSOT だが `\| str` で無効化 |

---

## B. PHASE 2 モック vs 設計 SSOT 乖離

### B-HIGH（3 件 — 全件）

| # | 場所 | 問題 |
|---|------|------|
| B1 | `shared/app.js:38-40`, `07_mode_switch.html:267`, `03_nightly_review.html:310`, `05_strategy_history.html:196` | **SSE ペイロードが ch10 §10.5.3 / ch8 §8.9 契約と不一致**。`emergency_stop_triggered` が `{at}` のみ（SSOT は `{trigger, timestamp, open_positions_closed}`）、`mode_changed` が小文字値、`strategy_applied` が `{version}` のみ（SSOT は `{new_version, previous_version, applied_by, diff}`）。PHASE 4 REST/SSE 接続時に **モックと本実装で契約が割れる** |
| B2 | `shared/i18n.js:26-30` vs §8.25.3 / §9.13.6 / §14.5.1 | **設計書内で二律背反**。§8.25.3 / §9.13.6 は「en は未翻訳でキー表示」、§14.5.1 は「ja フォールバック」。実装は §14.5 側に従い ja フォールバック → ch8/ch9 検証基準で FAIL |
| B3 | `shared/mock-data.js:597-602` | `getEmergencyStop()` が `emergencyStop: null` でも常に `EMERGENCY_ACTIVE_MOCK` を返す → `normal`/`winning_streak` シナリオで `08_emergency_stop.html` が常時「停止中」UI |

### §8.25.3 検証チェックリスト判定（10 項目）

| # | 項目 | 判定 |
|---|---|---|
| 1 | ダブルクリック起動 | 未検証（要マスター実機確認） |
| 2 | 外部 CDN/npm ゼロ | **PASS** |
| 3 | `Cmd/Ctrl+K` パレット | **PASS** |
| 4 | `?` ヘルプ | **PASS** |
| 5 | 緊急停止サイドバー最下部（全 10 画面） | **PASS** |
| 6 | 言語切替 ja→en→ja | **FAIL（ch8 基準）** / PASS（ch14 基準）— B2 |
| 7 | シナリオ切替 | **PASS** |
| 8 | フォーカスリング | **部分 FAIL**（`.btn-emergency-sidebar` に danger リング欠如） |
| 9 | Chrome/Firefox/Safari | 未検証 |
| 10 | ヘッダーコメント §8.2.3 | **PASS**（11/11 HTML） |

### B-MED（10 件、抜粋）

- `mock-data.js:112` `pnl_usd` が `5.1` で §15.4.8 サンプルの `5.10` と差分
- ハードコード文言（`Next`/`Current`/`別プロセス`/`(NG)` 等が `data-i18n` 未付与、§8.8 違反）
- §8.7.4 が dead reference（§8.7 内に節が存在しない）
- `shared/locales/ja.bundle.js` が ja.json と二重管理（自動同期スクリプト不在）
- `localStorage` キーが `yoruu_mock_lang`、SSOT は `yoruu_lang`
- §8.10 FAB「単色」解釈が CSS と不一致
- `08_emergency_stop.html` シナリオが 2 つのみ（他画面は 3）
- 11 SSE イベントのうちユーザー操作で擬似発火されるのは 4 種のみ

### B-LOW（4 件）

- 監査依頼の i18n カテゴリ表が SSOT §14.3.2 と不一致（11 名前空間: `nav|page|action|metric|state|mode|cmd|alert|error|tooltip|markov` + `a11y.*`）
- ヘルプモーダルに `g d`/`g l` のみ掲載、§8.22.3 全 9 シーケンス未列挙

### カテゴリ別 PASS サマリ

| カテゴリ | 判定 | 備考 |
|---|---|---|
| カラートークン §8.4.1 | PASS | `style.css:2-27`、旧ベージュ `#f5f1e8` 参照なし |
| i18n キー網羅 | 部分 PASS | `ja.json` 259 キー、`markov.wait.*` 6 値一致、`en.json` 空 `{}` 配置 |
| 03_nightly_review §15.4.8/§15.5/§15.6/§15.7/§15.8 | PASS（微差 1 件） | プロンプトコピー、JSON parse、差分プレビュー、Apply モーダル全て実装 |
| 08_emergency_stop / 07_mode_switch UI | PASS | LIVE 2 段階、EMERGENCY→LIVE 拒否、復帰確認モーダル |
| shared/nightly-review.js 責務分離 | PASS | PHASE 4 で UI 実装に流用可能 |

---

## C. ドキュメント・マイルストーン整合

### C-HIGH（6 件 — 全件）

| # | 場所 | 問題 |
|---|---|---|
| C1 | `README.md` 全面 | **PHASE 番号が ROADMAP と逆転**（README Phase 2=コア / Phase 3=Web、実態と逆）、`design_ch1-7_review` バッジ残存、L237「UI モック準備中」、L262 リポジトリ構成「予定」、`uv sync` / CLI 起動手順なし、`pyproject` v0.3.0 と完全不整合 |
| C2 | `INDEX.md:6` | ヘッダ「PHASE 1 完了／PHASE 2 完了」のみで **PHASE 3 着手未宣言**（L16 では PHASE 3 と書いてある自己矛盾）。最終更新 2026-05-27 のまま |
| C3 | `00_ROADMAP.md:264-274` | §6 変更履歴が `1117eca`（PHASE 1 完了）で **完全停止**。M2.1〜M2.3、PHASE 3 scaffold、data 修正の 5 コミット未記録 |
| C4 | `00_ROADMAP.md:20-26 vs §3 L232` | **同一ファイル内で依存関係が矛盾**。§1 Gantt は PHASE 3 を `after p2`（逐次）、§3 Mermaid は「PHASE 2/3 並行可」。git 現実は同日着手（並行） |
| C5 | `docs/2026-05-28_開発日記.html` 不在 | **本日日記欠落**（規約 `04-diary-workflow` 違反）。PHASE 3 追補コミット相当の作業が時系列ログに残らない |
| C6 | `pyproject.toml:70 vs ch23 §23.3` | **`fail_under = 50`** だが ch23 SSOT は **`≥80%`**。INDEX L17 も 80% を PHASE 3 Exit に明記 — 2 倍以上の乖離 |

### C-MED（12 件、抜粋）

- INDEX ch13〜24 + 付録 A の **コミット列が空欄**、関連リンクが ch15 まで
- ROADMAP L69-70 「PHASE 1 完了 5/31」「PHASE 2 着手 6/1 週」が **実績未反映**（実際は 5/27 完了・同日着手）
- `PHASE2_KICKOFF_TEMPLATE.md` §1 が「並行可否未定」のままだが実態は並行で実行済み
- `REVIEW_CHECKLIST_appendix_a.md` **存在しない**（付録 A APPROVED の独立記録なし）
- `REVIEW_CHECKLIST_ch21/22/24` が 1 行要約のみで 7 観点表なし
- 規約 §52: PHASE 3 実装は Composer 2.5 担当のはずだが、`005fdcd` が Opus 経由だった可能性（要確認）
- ROADMAP PHASE 1 節見出しに「完了」なし、L69-70 期間再見積が実績反映なし
- ROADMAP §M3.1〜§M3.6 状態は git 現実と一致（合格）

### C-LOW（8 件、抜粋）

- ROADMAP PHASE 4 Exit Criteria に ch22 / ch10 引用なし（着手前に必要）
- 2026-05-27 日記 L759 obsolete pending callout 残存

---

## D. 設計書ローリング候補（横断、Opus 章ごと新チャット担当）

A/B/C の根に共通する **設計書側を直すべき** 項目を抽出:

| # | 章 | 修正内容 | 起源 |
|---|---|---|---|
| D1 | **ch3 v1.0.1** | `GENERATING_REPORT`/`AWAITING_APPLY`/`APPLYING_STRATEGY` → 単一 `NIGHTLY_REVIEW` に統合（or サブフェーズ enum 並立） | ch15 §15.3.2 / §15.12.3 `[要確認: ch3]` |
| D2 | **ch10 v1.1** | §10.6.8 に **`POST /api/v1/reports/regenerate`** 追記 | ch15 §15.10.5 / §15.12.3 `[要確認: ch10]` |
| D3 | **ch13 v1.0.x or ch22 v1.0.x** | FillModel 既定値の **二重 SSOT 解消**（`slippage_coeff` `0.001`/`0.0001`、`latency_ms` `150`/`80`）。「実行時は ch22 優先」を明記 | A の「ch13 vs ch22」MED |
| D4 | **ch13 v1.0.x** | `OrderBook.source` Literal に `"MOCK"` 追加 or `FALLBACK` マップ規約明記 | A の types.py:101 |
| D5 | **ch18 v1.0.x** | `W_NIGHTLY_001`（§15.7.4 警告コード）正式掲載、`E_YORUU_000` 基底コードの扱い | A3 / errors.py:9 |
| D6 | **ch8 §8.25.3 / ch9 §9.13.6 vs ch14 §14.5.1** | en 切替挙動の**設計内矛盾**を 1 本化（推奨: ja フォールバック側に統一） | B2 |
| D7 | **ch8 §8.7.4 新設** | 緊急停止のパレット短縮一致禁止ルール（現在 dead reference） | B-MED |
| D8 | **ch6 / ch7 cross-ref** | 旧 `GENERATING_REPORT` 等の参照を `NIGHTLY_REVIEW` 統合後に更新 | A・D1 連動 |
| D9 | **ch11 §11.7.2** | Evaluator 内 Risk 統合 / OM 層分離のどちらが SSOT か 1 段落明記 | A7 |
| D10 | **ch14 §14.4.1** | `ja.bundle.js` の存在・ja.json 同期手順を SSOT 化 | B-MED |

---

## E. 規約・運用整合

| # | 場所 | 問題 | 推奨 |
|---|---|---|---|
| E1 | `52-yoruu-model-routing.mdc:31, 58-60` | PHASE 3 実装は Composer 2.5 担当。`005fdcd` が Opus 経由だった場合は規約違反 → 要確認 + 以降は Composer 専用チャットへ移管 | チャット履歴で確認 |
| E2 | 同 L52-53 | 「設計チャットに git log・実装エラー・pytest を混ぜない」。本監査は **readonly 監査用途** のため Opus 許容範囲だが、規約 §1 に「監査タスクは Opus 可」と 1 行追記すべき | 規約 §1 追記 |
| E3 | `pyproject.toml:70` | `fail_under=50` を **明示的に「PHASE 3 中期暫定、Exit 80」** と README/ROADMAP に注記。Exit 前に 80 へ引上げ | C6 連動 |

---

## F. 今後の作業設計 — 4 トラック並列

### Track 1 — PHASE 3 SSOT 同期【最優先・Composer 2.5】

**目的**: A-HIGH 8 件 + A-MED 主要を解消し、PHASE 3 Exit Criteria（24h paper 稼働・カバレッジ 80%）に到達。

| ID | 内容 | 対象ファイル | 参照 SSOT |
|---|---|---|---|
| T1.1 | DDL CHECK 制約・INDEX 全件追加 | `data/schema.py` | ch10 §10.3.3〜12 |
| T1.2 | `NightlyReporter.generate()` を §15.4.8 完全準拠に書き直し | `review/nightly_reporter.py` | ch15 §15.4 |
| T1.3 | `ApplyValidator` に `rationale` 検証・`E_NIGHTLY_005` 訂正・`W_NIGHTLY_001`・`StrategyApplyError` 統一 | `review/apply_validator.py`, `errors.py` | ch15 §15.6/§15.7.4 |
| T1.4 | `FillModel.detect_liquidity_failure` 修正（`ask_size_usd < size_usd`） | `execution/fill_model.py` | ch13 §13.8.1 |
| T1.5 | `InvariantChecker` に 12 件追加 + 起動/遷移/取引/5分境界 hook で呼出し | `safety/invariants.py`, `core/state_machine.py`, `execution/paper_executor.py` | ch16 全 §16.2-5 |
| T1.6 | `nightly generate` で `IDLE↔NIGHTLY_REVIEW` 遷移 + 失敗時 audit | `cli.py`, `review/nightly_reporter.py` | ch15 §15.3.2/§15.3.5 |
| T1.7 | `strategy apply` を §15.8 シーケンスに準拠（StateMachine ガード・proposed_strategy_json 更新・排他ロック・rollback） | `cli.py`, `review/strategy_writer.py`, `data/database.py` | ch15 §15.8 |
| T1.8 | Evaluator vs RiskGuard の層分担を SSOT に合わせて再構成（C4 統合 or OM 層分離いずれか） | `strategy/evaluator.py`, `execution/risk_guard.py` | ch11 §11.7.2 + D9 |
| T1.9 | A-MED の DB / errors / Markov 各種修正（A9〜A22 等） | 各該当ファイル | ch10/ch11/ch13/ch18 |
| T1.10 | テスト追加: `tests/test_invariants.py`（全 15 件）、`tests/test_nightly_reporter_snapshot.py`（§15.4.8 固定 JSON snapshot）、`tests/test_apply_validator.py` 拡張（partial / rationale / 警告） | `tests/` | ch23 §23.2-4 |
| T1.11 | `pyproject.toml` `fail_under` を段階的に 50 → 70 → 80 へ引上げ | `pyproject.toml` | ch23 §23.3 |

**完了基準**: A-HIGH 8 件全クローズ + テストカバレッジ 80% 達成 + ペーパー 24h 連続稼働。

### Track 2 — 設計書ローリング【Opus、章ごと新チャット】

D1〜D10 を 4 つの Opus 設計チャットに分割。各チャットで章を直接編集（執筆 + 配置までは Opus、commit / push は Composer 2.5 が代行可）。

| サブ | 章 | 内容 | 起源 |
|---|---|---|---|
| **2A** | ch3 v1.0.1 + ch6 / ch7 cross-ref 同期 | NIGHTLY_REVIEW 統合 + 旧 3 細分状態の扱い決定 | D1, D8 |
| **2B** | ch10 v1.1 | `POST /api/v1/reports/regenerate` 追加 + `event_bus` パラメータ言及 | D2、A18 |
| **2C** | ch13 v1.0.x + ch22 v1.0.x | FillModel 既定値の二重 SSOT 解消、`OrderBook.source MOCK` 規約、ch22 PaperSettings の優先順位明記 | D3, D4 |
| **2D** | ch18 v1.0.x + ch8 §8.7.4 新設 + ch14 §14.4.1 + ch11 §11.7.2 + ch8/9 vs 14 矛盾解消 | エラーコード追補 + en 切替仕様統一 + Evaluator 層分担 | D5, D6, D7, D9, D10 |

### Track 3 — ドキュメント現状反映【Composer 2.5】

| ID | 内容 | 対象 |
|---|---|---|
| T3.1 | **README.md 全面書き直し** — PHASE 番号 ROADMAP 準拠、`uv sync` / `yoruu config validate` / `yoruu db init` / `yoruu paper evaluate-once` の Quick Start、v0.3.0 状態反映、古いバッジ削除 | `README.md` |
| T3.2 | **INDEX.md 更新** — L6 ヘッダに PHASE 3 着手宣言、最終更新日 2026-05-28、ch13〜24 + 付録 A のコミット列を CHECKLIST から転記、関連リンクに ch16〜24 追加 | `INDEX.md` |
| T3.3 | **00_ROADMAP.md 更新** — §6 変更履歴に M2.1/M2.2/M2.3/PHASE 3 scaffold/data fix の 5 行追加、§1 Gantt と §3 Mermaid の依存矛盾解消、PHASE 1/2 節見出しに「— 完了（2026-05-27）」、PHASE 3 Exit Criteria を「行カバレッジ ≥ 80% (ch23 §23.3)」「ペーパー 24h 連続稼働」「INV-* assertion 全件 pass」に具体化 | `00_ROADMAP.md` |
| T3.4 | **2026-05-28_開発日記.html 新規作成** — `04-diary-workflow` テンプレ準拠、本日エントリ（監査結果サマリ、Track 1〜4 着手宣言）を時系列で記録 | `docs/2026-05-28_開発日記.html` |
| T3.5 | **`fail_under` の段階引上げ計画書記** — README / ROADMAP に「現状 50（暫定）、Track 1 完了時 70、PHASE 3 Exit 時 80」と明記 | `README.md`, `00_ROADMAP.md` |
| T3.6 | **`REVIEW_CHECKLIST_appendix_a.md` 新規作成** — 付録 A 用語集の独立チェックリスト（承認日 2026-05-27、コミット `1117eca`、7 観点判定表）、INDEX からリンク | `docs/design/REVIEW_CHECKLIST_appendix_a.md` |
| T3.7 | **ch21 / ch22 / ch24 のレビュー記録拡充** — 現状 1 行要約 → ch17 形式の 7 観点表 | `REVIEW_CHECKLIST_ch21/22/24.md` |
| T3.8 | **`PHASE2_KICKOFF_TEMPLATE.md` 終了処理** — §1 に「2026-05-27 並行 (B) で実行済み」結論追記、冒頭に「PHASE 2 完了、§2/§3 は PHASE 4 転用時に差し替え」注記 | `PHASE2_KICKOFF_TEMPLATE.md` |
| T3.9 | **`PHASE4_KICKOFF_TEMPLATE.md` 新規作成** — Composer 2.5 引き渡し用、SSOT は ch8 / ch10 / ch14 / ch15 / ch22 / ch24 / ch16-19 を網羅 | `docs/design/PHASE4_KICKOFF_TEMPLATE.md` |

### Track 4 — PHASE 2 モック後修正【Composer 2.5、PHASE 4 着手前必須】

B-HIGH 3 件 + B-MED 主要を解消し、PHASE 4（FastAPI + SSE 接続）でモックをそのまま流用できる契約整合を確立。**Track 1 と並列可だが、PHASE 4 着手の前提条件**。

| ID | 内容 | 対象 |
|---|---|---|
| T4.1 | **SSE 固定フィクスチャ整備** — `mock-data.js` に `SSE_PAYLOADS` 定数（11 イベント分、ch10 §10.5.3 例をバイト一致で転記）。各 `mockSSE()` 呼び出しを定数参照に書き換え | `shared/mock-data.js`, `shared/app.js`, 各画面 HTML |
| T4.2 | **en 切替の挙動修正** — D6（Track 2D）の方針確定後に実装側を合わせる。Track 2D 完了待ち | `shared/i18n.js` |
| T4.3 | **`getEmergencyStop()` 修正** — `emergencyStop===null` 時は未停止プレースホルダ表示。`drawdown` シナリオでのみ停止フロー検証 | `shared/mock-data.js`, `08_emergency_stop.html` |
| T4.4 | **§15.4.8 サンプル 1 フィールド差解消** — `DAILY_REPORT_NORMAL.by_side.YES.pnl_usd: 5.1 → 5.10`（バイト一致） | `shared/mock-data.js:112` |
| T4.5 | **i18n / a11y ハードコード解消** — 8 箇所の文言に `data-i18n` 付与、`ja.json` にキー追加、ja.bundle.js 再生成 | `07_mode_switch.html`, `03_nightly_review.html`, `06_alerts.html`, `shared/locales/*` |
| T4.6 | **緊急停止サイドバーボタンに danger フォーカスリング** — `.btn-emergency-sidebar:focus-visible` を `.fab-emergency:focus-visible` と同等化 | `shared/style.css:250-264` |
| T4.7 | **ヘルプモーダル拡充** — `g r/s/h/m/w/a/x` 計 9 シーケンスを表示（§8.22.3 全件） | `shared/app.js:59-64` |
| T4.8 | **`08_emergency_stop.html` シナリオ追加** — `winning_streak` を含めて 3 シナリオに揃える | `08_emergency_stop.html:69-72` |
| T4.9 | **ja.bundle.js 自動生成スクリプト** — `tools/build_locales.py` で ja.json → ja.bundle.js 同期、pre-commit で実行 | `tools/build_locales.py` |

**完了基準**: B-HIGH 3 件全クローズ、§8.25.3 検証チェックリスト 10/10 PASS（マスター実機確認込み）。

---

## G. 推奨アクション順序

### 即日（5/28）

| 順 | 担当 | 内容 | 工数 |
|---|------|------|------|
| 1 | Composer 2.5（**新規 `PHASE3-fix` チャット**） | T1.1 DDL CHECK + INDEX 追加（ch10 §10.3 写経で機械的） | 1h |
| 2 | Composer 2.5（**新規 `docs-sync` チャット**） | T3.4 日記作成 + T3.1 README 書き直し | 1h |
| 3 | Opus（**新規 `ch3-rolling` チャット**） | Track 2A: ch3 v1.0.1 ドラフト | 30min |

### 2 日目（5/29）

| 順 | 担当 | 内容 |
|---|------|------|
| 4 | Composer 2.5（`PHASE3-fix` 継続） | T1.2 NightlyReporter 全面準拠 + T1.3 ApplyValidator 拡張 |
| 5 | Composer 2.5（`docs-sync` 継続） | T3.2 INDEX + T3.3 ROADMAP + T3.6/3.7 CHECKLIST 拡充 |
| 6 | Opus（**新規 `ch10-v11` チャット**） | Track 2B: ch10 v1.1 で regenerate 追記 |

### 3 日目（5/30）

| 順 | 担当 | 内容 |
|---|------|------|
| 7 | Composer 2.5 | T1.4 FillModel + T1.5 InvariantChecker 全件 + T1.6/T1.7 StateMachine 統合 |
| 8 | Opus（`ch13-22-sync` / `ch18-ch8-ch14-fix` チャット） | Track 2C + 2D 並列 |
| 9 | Composer 2.5（**新規 `phase2-fix` チャット**） | Track 4 T4.1 SSE フィクスチャ + T4.3 emergency 修正 |

### 4 日目（5/31）— PHASE 3 ブロッカー解消完了

| 順 | 担当 | 内容 |
|---|------|------|
| 10 | Composer 2.5（`PHASE3-fix`） | T1.10 テスト追加・T1.11 `fail_under` 80 引上げ・T1.8 層分担再構成 |
| 11 | Composer 2.5（`phase2-fix`） | Track 4 残: T4.2（D6 確定後）・T4.4〜T4.9 |
| 12 | マスター | PHASE 3 Exit Criteria 確認: `uv run pytest --cov` ≥ 80% / `yoruu paper evaluate-once` 動作 / INV-* assert 全件 pass |

### 5 日目（6/1）— PHASE 3 24h ペーパー稼働開始

| 順 | 担当 | 内容 |
|---|------|------|
| 13 | Composer 2.5（**新規 `paper-24h` チャット**） | `yoruu paper run --duration 24h` 相当のループ実装、`MockMarketProvider` の連続データ供給、SQLite 連続書込安定性確認 |
| 14 | マスター | 24h 完走確認 → PHASE 4（FastAPI UI）着手判断 |

### 6 日目以降（6/2〜）— PHASE 4 着手

| 順 | 担当 | 内容 |
|---|------|------|
| 15 | Composer 2.5（`docs-sync`） | T3.8 PHASE2_KICKOFF 終了処理 + T3.9 PHASE4_KICKOFF テンプレ作成 |
| 16 | Composer 2.5（**新規 `PHASE4-fastapi` チャット**） | M4.1 FastAPI 基盤 + SSE（mock-data.js の SSE_PAYLOADS をそのまま流用） |

---

## H. 並列性と依存関係

```
Track 1 (PHASE 3 SSOT) ──┬─ T1.1〜T1.9 互いに依存少、並列可
                         └─ T1.10/T1.11 は T1.1〜T1.9 完了後

Track 2 (設計ローリング) ─┬─ 2A/2B/2C/2D 完全並列
                          └─ 2D の D6 確定が Track 4 T4.2 のブロッカー

Track 3 (ドキュメント)   ── 全 T3.x 並列可、Track 1/2 と独立

Track 4 (PHASE 2 後修正) ─┬─ T4.1/3/4/5/6/7/8/9 並列可
                          └─ T4.2 は Track 2D 完了待ち
```

**並列度の限界**: Cursor の同時アクティブチャット数 + マスターのレビュー帯域。推奨は **3 チャット同時** までに抑える（`PHASE3-fix` / `docs-sync` / Opus 1 つ）。

**クリティカルパス**: Track 1 T1.5（InvariantChecker 12 件実装 + hook 接続）が **最重量タスク**（推定 4-6h）。ここを最初に Composer に投げて並列で他を進めるのが最短。

---

## I. リスクと未確認事項

### `[要確認: file]` 系（断定不可、マスター判断要）

| # | 項目 | 影響 | 確認方法 |
|---|---|---|---|
| I1 | A14: PaperExecutor の open 時 balance 更新タイミングが ch10/ch13 で SSOT 化されているか | 残高不整合の根本判定 | ch10 §10.10 / ch13 §13.6 全文読解 |
| I2 | A15「ch13 vs ch22 FillModel 既定値」優先順位 | T1.x 着手前に方針確定必要 | ch13 §13.3.2 / ch22 §22.2 を Opus でレビュー |
| I3 | A3 の `W_NIGHTLY_001` が ch18 に正式掲載されているか | エラーコード整合 | ch18 全文 grep |
| I4 | E1: PHASE 3 scaffold commit `005fdcd` が Composer 2.5 経由か Opus 経由か | 規約遵守判定 | git log の Co-authored-by 確認、または該当チャット履歴 |
| I5 | A の cli.py `paper evaluate-once` 22 close ハードコードが「デモ専用」か「本番 evaluate パス」か | T1.x の優先度判定 | マスター意図確認 |

### 隠れリスク

- **Markov.add_close でフラット時 DOWN 強制（A12）**: 数日連続でフラット相場（5min OHLC 同値）が続くと持続的に DOWN バイアスが生じ、Kelly サイジングが NO 側に偏る可能性。バックテストで顕在化するまで気付きにくい
- **InvariantChecker 12 件未実装 + 呼出ゼロ（A5）**: 「安全装置が論理的には存在するが、回路がつながっていない」状態。実運用で `daily_loss_limit` 等の境界条件で停止しない事故シナリオが現実的。Track 1 T1.5 を最優先で
- **SSE 契約乖離（B1）**: PHASE 4 で FastAPI 実装時、モックの SSE 形と本実装の SSE 形が違うと、フロントエンドを書き直しになる。Track 4 T4.1 を **PHASE 4 着手前必須** に格上げ
- **README 全面陳腐化（C1）**: 外部から見て「実装前のプロジェクト」と誤認される。git push 済みの README が古いのは公開リポジトリ運用上のリスク

---

## J. Composer 2.5 / Opus 依頼テンプレ集

### J.1 Composer 2.5: Track 1（PHASE 3 SSOT 同期）

```
[実装] PHASE 3 SSOT 同期 (Track 1)。
スコープ: T1.1〜T1.11 を順序通り、各タスク後に pytest 実行。
SSOT: @docs/design/PHASE3_QUALITY_AUDIT.md
      @docs/design/10_functions_data_model.md (§10.3)
      @docs/design/11_strategy_logic.md (§11.7)
      @docs/design/13_paper_execution.md (§13.4, §13.8)
      @docs/design/15_nightly_review.md (§15.3, §15.4, §15.6, §15.7, §15.8)
      @docs/design/16_invariants.md
      @docs/design/18_error_handling.md
      @docs/design/23_test_strategy.md
依頼内容: PHASE3_QUALITY_AUDIT.md §F Track 1 全件。HIGH 8 件は分割 commit 推奨。
完了基準: pytest --cov pass, fail_under=80, paper evaluate-once 動作確認。
全部おまかせ（commit/push/日記まで）。
```

### J.2 Composer 2.5: Track 3（ドキュメント現状反映）

```
[配置] PHASE 3 着手後のドキュメント現状反映 (Track 3)。
T3.1〜T3.9 を順次。各 T 単位で commit、最後にまとめて push。
SSOT: @docs/design/PHASE3_QUALITY_AUDIT.md
重要: 既存 APPROVED 章本文は触らない（ローリングは Track 2 で別途）。
更新対象は INDEX / ROADMAP / README / 日記 / CHECKLIST のみ。
完了基準: INDEX に PHASE 3 進捗反映、README に Quick Start、日記 5/28 作成。
```

### J.3 Composer 2.5: Track 4（PHASE 2 モック後修正）

```
[実装] PHASE 2 モック後修正 (Track 4)。
スコープ: T4.1〜T4.9（T4.2 は Track 2D 完了待ち）。
SSOT: @docs/design/PHASE3_QUALITY_AUDIT.md
      @docs/design/08_ui_mockup.md (§8.25.3)
      @docs/design/10_functions_data_model.md (§10.5.3)
      @docs/design/15_nightly_review.md (§15.4.8)
重要: 既存 11 画面の構造・配色は変更しない。SSE 契約整合と i18n/a11y 修正のみ。
完了基準: B-HIGH 3 件全クローズ、§8.25.3 検証 10/10 PASS。
```

### J.4 Opus: Track 2A（ch3 v1.0.1 ローリング）

```
[設計執筆] ch3 v1.0.1 ローリング + ch6/ch7 cross-ref 同期。

背景: ch15 §15.3.2 / §15.12.3 の `[要確認: ch3]` を解消する。
  - ch10 / ch12 / ch15 / types.py / state_machine.py は単一 NIGHTLY_REVIEW を採用済み
  - ch3 §3.1 (L16-18) のみ GENERATING_REPORT / AWAITING_APPLY / APPLYING_STRATEGY の3細分が残存
  - ch6 / ch7 cross-ref に旧細分状態の参照あり

タスク:
1. ch3 §3.1 を NIGHTLY_REVIEW 単一に統合 (v1.0.1)
   - 内部実装上のサブフェーズとして残すなら enum 並立で記述
2. ch6 / ch7 の cross-ref を更新
3. REVIEW_CHECKLIST_ch3 を更新（v1.0.1 注記）
4. ch15 §15.12.3 の `[要確認: ch3]` 行削除

SSOT: @docs/design/03_state_diagram.md
      @docs/design/06_sequence.md
      @docs/design/07_io_diagram.md
      @docs/design/10_functions_data_model.md §10.7
      @docs/design/15_nightly_review.md §15.3
      @docs/design/PHASE3_QUALITY_AUDIT.md §D1, §D8

配置・commit・push は Composer 2.5 別チャットで実施。本チャットは Markdown 出力まで。
```

### J.5 Opus: Track 2B（ch10 v1.1）

```
[設計執筆] ch10 v1.1 — regenerate API 追加 + event_bus 引数言及。

背景: ch15 §15.10.5 で PHASE 3 実装対象とされる `POST /api/v1/reports/regenerate`
が ch10 §10.6.8 に未掲載。`[要確認: ch10]` 解消が必要。

タスク:
1. ch10 §10.6.8 に regenerate エンドポイント追加（preview-apply の隣）
   - リクエスト/レスポンス JSON、認可、再生成のトランザクション扱い
2. §10.7.2 StateMachine.__init__ シグネチャに event_bus: EventBus を明記
3. ch15 §15.12.3 / §15.10.5 の `[要確認: ch10]` 行削除
4. REVIEW_CHECKLIST_ch10 v1.1 注記

SSOT: @docs/design/10_functions_data_model.md
      @docs/design/15_nightly_review.md §15.10.5
      @docs/design/PHASE3_QUALITY_AUDIT.md §D2

配置・commit・push は Composer 2.5。
```

### J.6 Opus: Track 2C（ch13 + ch22 FillModel SSOT 統一）

```
[設計執筆] ch13 + ch22 — FillModel 既定値の二重 SSOT 解消、OrderBook.source MOCK 規約。

背景: PHASE 3 監査で以下の乖離発覚。
  - ch13 §13.3.2: slippage_coeff=0.001, latency_ms=150
  - ch22 §22.2:   slippage_coeff=0.0001, latency_ms=80
  - 実装は ch22 準拠。どちらが優先か明文化なし
  - types.py:101 で OrderBook.source に "MOCK" 追加されているが ch13 §13.4.4 SSOT に存在しない

タスク:
1. ch22 §22.2 を SSOT に確定、ch13 §13.3.2 に「実行時は ch22 paper.* を優先」明記
   （または逆方向で統一、マスター判断）
2. ch13 §13.4.4 の OrderBook.source Literal に "MOCK" 追加（lab/mock 用途）
   または FALLBACK へのマップ規約を明記
3. REVIEW_CHECKLIST_ch13/22 に v1.0.x 注記

SSOT: @docs/design/13_paper_execution.md
      @docs/design/22_config_spec.md
      @docs/design/PHASE3_QUALITY_AUDIT.md §D3, §D4

配置・commit・push は Composer 2.5。
```

### J.7 Opus: Track 2D（ch18 + ch8 §8.7.4 + ch14 §14.4.1 + ch11 §11.7.2 + en 切替矛盾）

```
[設計執筆] Track 2D 5 件まとめ — エラーコード追補・dead ref 解消・bundle 規約・層分担・en 矛盾解消。

スコープ:
1. ch18: W_NIGHTLY_001（§15.7.4 警告コード）正式掲載、E_YORUU_000 基底コード扱い
2. ch8 §8.7.4 新設: 緊急停止のパレット短縮一致禁止（現在 dead ref）
3. ch14 §14.4.1: ja.bundle.js の存在・ja.json 同期手順を SSOT 化
4. ch11 §11.7.2: Evaluator 内 Risk 統合 / OM 層分離のどちらが SSOT か 1 段落明記
5. ch8 §8.25.3 / ch9 §9.13.6 vs ch14 §14.5.1 矛盾解消（推奨: ja フォールバック側へ統一、ch8/9 を更新）

各章 v1.0.x ローリング、REVIEW_CHECKLIST に 1 行追記。

SSOT: @docs/design/18_error_handling.md
      @docs/design/08_ui_mockup.md §8.7 §8.25
      @docs/design/09_user_flow.md §9.13
      @docs/design/14_i18n_design.md §14.4 §14.5
      @docs/design/11_strategy_logic.md §11.7
      @docs/design/15_nightly_review.md §15.7.4
      @docs/design/PHASE3_QUALITY_AUDIT.md §D5-D7, §D9-D10

配置・commit・push は Composer 2.5。
```

---

## K. マスター向け 3 行サマリ

1. **コア骨格は SSOT 整合、ブロッカーは HIGH 17 件**（実装 8 / モック 3 / ドキュメント 6）。最重量は **InvariantChecker 12 件未実装 + 呼出ゼロ**（A5）— 安全装置が回路未接続
2. **4 トラック並列で 4 日**（5/28〜5/31）で PHASE 3 Exit Criteria 到達可能。クリティカルパスは Track 1 T1.5。Track 2/3/4 は独立並列
3. **未確認 5 件**（I1〜I5）は Composer に投げる前にマスター判断必要。特に I4（規約遵守判定）と I2（ch13 vs ch22 優先順位）

---

## 変更履歴

| 日付 | バージョン | 内容 |
|------|----------|------|
| 2026-05-28 | v1.0 | 初版作成（3 並列 explore 監査、HIGH 17 件、4 トラック作業計画） |
