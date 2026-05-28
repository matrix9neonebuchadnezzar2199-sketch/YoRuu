# PHASE 3 並列チャット — 貼り付け用テンプレ（修正版）

> **目的**: `PHASE3_QUALITY_AUDIT.md` §F / §J.2 / §J.3 / §L と ID 衝突しないよう調整した **そのまま貼れる** 依頼文。  
> **運用**: Track 3 先行 + `phase2-fix` は **Q3-MOCK のみ**（監査書 **T4.1 SSE とは別スコープ**）を `docs-sync` と並列可。  
> **正本**: 監査書 §F の T3.1〜T3.9 / T4.1〜T4.9。本ファイルのチャット用 ID は §F と **1:1 対応表** で併記する。

### 投入チャット索引（テンプレ 7〜13）

| # | ID | 状態 | 前提コミット | 触る領域 | 備考 |
|---|----|------|--------------|----------|------|
| 7 | `phase2-sse` | **完了** | `7cbfd49` | `docs/mockups/shared/` | §F T4.1 / B1 スリム |
| 8 | `PHASE3-fix`（継続） | **完了** | `579402f` | `tests/**`, `src/yoruu/safety/` 等 | Track 1 第二フェーズ |
| 9 | `PHASE3-sse-contract` | **完了** | `dea96e0` | `src/yoruu/api/sse/` | FastAPI SSE 契約 |
| 10 | `phase2-i18n-palette` | **完了** | `55d1682` | `docs/mockups/shared/` | §F T4.2 |
| 11 | `PHASE3-fix-inv-d02` | **完了** | `a2b6081` | `database.py`, `invariants.py` | INV-D-02 |
| 12 | `PHASE3-exit-route-a` | **完了** | `18fb05c` | `infra/**`, `web/**` | Exit 戦略 A |
| 13 | `phase4-m42-static-ui` | **完了** | `48c47f4` | `web/static/`, `tools/build_web_static.py` | PHASE 4 M4.2 |

**並列推奨（§L ≤ 3）**: テンプレ 7〜13（PHASE 3 Exit + M4.2）は完了。PHASE 4 本番 UI は M4.3 以降。

---

## 調整メモ（貼り付け前チェック）

| # | 論点 | 対応 |
|---|------|------|
| 1 | マスター案の T3.x が §F と別定義になりうる | テンプレ 1 は **§F ID 列** を必須。完了報告に §F ID を併記 |
| 2 | `phase2-fix` の「T4.1」表記 | **Q3-MOCK** と命名。監査 **T4.1 = SSE_PAYLOADS（B1）** は別チャット |
| 3 | モックパス | `sse-mock.js` / `dashboard.html` 等は **実リポジトリに無し** → `app.js` / `01_dashboard.html` 等 |
| 4 | INV-D-06 | `balance + Σ(open.size_usd) ≈ initial + Σ(closed.pnl)`（open 減算・close 加算） |
| 5 | INV-D-02 集計パス | テンプレ 11: `persistence/` は未採用 → **`src/yoruu/data/database.py`** に日次集計を追加 |
| 6 | i18n bundle パス | テンプレ 10: `docs/locales/` ではなく **`docs/mockups/shared/locales/`** |

**その他**: A-HIGH は **8 件**（+ MED 多数）。`fail_under` Track 1 後は **55**（`pyproject.toml`）。段階は **55 → 70 → 80**。§J.2 の「各 T 単位 commit」は本テンプレ 1 では **1 commit まとめ可（マスター上書き）**。§F **T3.4** 日記新規は **完了済**（`f499778` / `a2f2a0e`）→ **追記のみ**。

---

## §F Track 3 — 厳密対応表（完了報告用）

| §F ID | 内容 | 本テンプレでの扱い |
|-------|------|-------------------|
| T3.1 | README 全面 + Quick Start | テンプレ 1 実施 |
| T3.2 | INDEX 更新 | テンプレ 1 実施 |
| T3.3 | ROADMAP 更新 | テンプレ 1 実施 |
| T3.4 | 日記新規 | **スキップ**（`docs/2026-05-28_開発日記.html` 既存） |
| T3.5 | fail_under 段階計画 | **55 → 70 → 80**（50 表記禁止） |
| T3.6 | CHECKLIST 付録 A | テンプレ 1 実施 |
| T3.7 | CHECKLIST ch21/22/24 拡充 | テンプレ 1 実施 |
| T3.8 | PHASE2_KICKOFF 終了注記 | テンプレ 1 実施 |
| T3.9 | PHASE4_KICKOFF 新規 | テンプレ 1 実施 |

| §F ID | 内容 | 本ファイルでの扱い |
|-------|------|-------------------|
| T4.1 | SSE_PAYLOADS 整備（B1） | **テンプレ 7** `phase2-sse`（スリム版。FastAPI 契約はテンプレ 9） |
| — | Q3 残高モック整合 | **Q3-MOCK**（テンプレ 2、完了 `d5c44a8`） |

---

## テンプレート 1 — `docs-sync`

**チャット名**: `docs-sync`  
**モデル**: Composer 2.5  
**投入**: 即時（Track 1 完了後）

```
[配置] YoRuu Track 3 ドキュメント同期（§PHASE3_QUALITY_AUDIT §F / §J.2）

# 目的
Track 1 完了（f499778, a2f2a0e、origin/main）を README / INDEX / ROADMAP / 日記 / 運用 SSOT に反映する。
設計章 ch1〜24・付録 A 本文、src/yoruu/**、docs/mockups/** は触らない。

# 前提コミット
- f499778: Track 1（A-HIGH 8 + Q1〜Q3）
- a2f2a0e: 日記 hash 追記
- pytest 20 passed、coverage ≈65%、fail_under=55（pyproject.toml）

# SSOT（read 必須）
@docs/design/PHASE3_QUALITY_AUDIT.md（§F Track 3、§C、§G、§I、§D）
@docs/design/INDEX.md
@docs/design/00_ROADMAP.md
@README.md
@docs/2026-05-28_開発日記.html

# 実施内容（監査書 §F の T3.1〜T3.9 に厳密対応。完了表に §F ID を併記すること）

| §F ID | 内容 |
|-------|------|
| T3.1 | README 全面更新：PHASE 番号は ROADMAP 準拠、v0.3.0、`uv sync`、Quick Start（config validate / db init / paper evaluate-once / nightly generate / strategy apply）、古いバッジ削除 |
| T3.2 | INDEX：L6 に PHASE 3 着手・Track 1 A-HIGH 完了、更新日 2026-05-28、ch13〜24+付録 A のコミット列・リンク |
| T3.3 | ROADMAP：§6 履歴（M2.1〜M2.3, scaffold, f499778）、§1/§3 依存矛盾解消、PHASE 1/2「完了 2026-05-27」、PHASE 3 Exit 具体化 |
| T3.4 | 日記新規 → **スキップ**（2026-05-28 日記は既存）。代替なし |
| T3.5 | fail_under 段階：**55（現状）→ 70 → 80（Exit）** を README/ROADMAP に明記（50 表記は使わない） |
| T3.6 | REVIEW_CHECKLIST_appendix_a.md 新規 + INDEX リンク |
| T3.7 | REVIEW_CHECKLIST_ch21/22/24 を 7 観点表に拡充 |
| T3.8 | PHASE2_KICKOFF_TEMPLATE.md 終了注記 |
| T3.9 | PHASE4_KICKOFF_TEMPLATE.md 新規 |

# 追加（マスター指定・§F 外だが同一コミット可）
- PHASE3_QUALITY_AUDIT.md：§I I4/I5 を「Track 1 後保留」、§D D11 を「採用済 f499778」
- README に Q1〜Q3 判定 3 行サマリ（E_NIGHTLY_008 統合 / ch22 Fill / open 残高減算 + INV-D-06）
- 2026-05-28 日記に Track 3 エントリ追記（§04-diary-workflow）
- ROADMAP に Track 1〜4 ステータス表（任意・T3.3 内でも可）

# Git
- コミット方針：マスター指定どおり **1 commit まとめ可**（§J.2 の分割 commit は今回上書き）
- message 例: docs(sync): Track 3 T3.1-T3.9 - reflect Track 1 completion
- push origin/main まで。全部おまかせ可。

# 完了報告（1 メッセージ）
1. commit hash
2. 変更ファイル一覧（±行数）
3. §F T3.1〜T3.9 対応表（スキップ理由含む）
4. 未対応・ブロッカー
```

---

## テンプレート 2 — `phase2-fix`（Q3-MOCK のみ）

**チャット名**: `phase2-fix`  
**モデル**: Composer 2.5  
**投入**: `docs-sync` と **並列可**（INDEX 完了待ち不要）

```
[実装] YoRuu モック Q3 残高整合（§PHASE3_QUALITY_AUDIT Q3 / ch13 §13.2.5）

# スコープ名（重要）
本タスクは監査書 §F の **T4.1（SSE_PAYLOADS）ではない**。
**Q3-MOCK: balance open 減算 / close 加算** のみ。SSE（B1）は別チャットで T4.1 本番実施。

# 目的
PaperExecutor（f499778）とモックの残高表示・SSE 擬似イベントを一致させる。

# 前提
- open 成功: balance -= size_usd
- close 成功: balance += size_usd + pnl
- INV-D-06: balance + Σ(open.size_usd) ≈ initial + Σ(closed.pnl)

# SSOT（read 必須）
@docs/design/PHASE3_QUALITY_AUDIT.md（§I Q3、§B A14）
@docs/design/13_paper_execution.md §13.2.5（D11）
@docs/mockups/shared/mock-data.js
@docs/mockups/shared/app.js
@docs/mockups/01_dashboard.html
@docs/mockups/02_trade_log.html

# タスク
Q3-MOCK.1: mock-data.js の balance 更新を open 減算 / close 加算に修正
Q3-MOCK.2: app.js の mockSSE（position_opened / position_closed）で balance を同期
Q3-MOCK.3: 01_dashboard / 02_trade_log の残高表示がイベント後に即更新されること
Q3-MOCK.4: 手動確認 — 3 ポジション open → 順次 close、balance 推移を console または UI で記録
Q3-MOCK.5: docs/mockups/CHANGELOG.md（無ければ新規）に Q3 整合を 1 節記載
Q3-MOCK.6: docs/2026-05-28_開発日記.html に Track 4（Q3-MOCK）エントリ追記
Q3-MOCK.7: 1 commit + push

# 範囲外
- 監査 T4.1 SSE_PAYLOADS（B1）、T4.2〜T4.9、src/yoruu/**、README/INDEX/ROADMAP、設計章 ch1〜24

# 完了条件・報告
- message 例: fix(mockups): Q3-MOCK align balance with PaperExecutor open/close
- 報告: commit hash / 変更ファイル / Q3-MOCK.1〜7 表 / balance 推移の確認結果 / 本番 T4.1 SSE への申し送り
```

---

## マスター側オペレーション（§L 補足）

| 順 | 待ち | 理由 |
|---|------|------|
| 1 | `docs-sync` の T3.2（INDEX）完了 | Track 2 Opus 起動時の前提コミット hash 記載用（**推奨**、phase2-fix は非依存） |
| 2 | `phase2-fix`（Q3-MOCK） | INDEX 非依存のため **並列可** |
| 3 | Opus `ch3-rolling` 等 | INDEX 更新後推奨（§L どおり） |
| 4 | 本番 **§F T4.1** SSE | Q3-MOCK 完了後、**テンプレ 7** `phase2-sse` |
| 5 | Track 1 第二フェーズ | **テンプレ 8** `PHASE3-fix` 継続（テンプレ 7 と並列可） |
| 6 | §F T4.2 i18n / パレット | **テンプレ 10** `phase2-i18n-palette`（前提 `7cbfd49`） |
| 7 | INV-D-02 実装 | **テンプレ 11** `PHASE3-fix-inv-d02`（前提 `579402f`、テンプレ 10 と並列可） |

---

## テンプレート 7 — `phase2-sse`（§F T4.1 / B1 スリム版）

**チャット名**: `phase2-sse`  
**モデル**: Composer 2.5  
**投入**: Track 2 完了後（`ff9f4e6` 推奨）。**テンプレ 8 と並列可**

```
# Track 4.1: SSE_PAYLOADS 整備（§F T4.1 / B1）

## 役割
Composer 2.5。監査 B1 解消。**モック契約を ch10 §10.5.3 / ch8 §8.9 に一致**させる。
設計章・`src/yoruu/**` は触らない（Track 2 完了済み）。

## 前提
- リポ: f:\Cursor\YoRuu / main
- 前提コミット: ff9f4e6（または 0030f6d / c8fa393）
- SSOT: ch10 §10.5.2〜10.5.3、ch8 §8.9.1

## マスター判定（変更不可）
- 11 イベント名は ch10 表と完全一致（state_changed 等）
- B1 修正: emergency_stop_triggered / mode_changed / strategy_applied の形
- 全イベントへの severity 新設はしない（alert_added のみ SSOT 通り）
- W_* コードは送出しない（モック内も E_NIGHTLY_008）

## スコープ
1. docs/mockups/shared/mock-data.js に SSE_PAYLOADS（11 件）追加
2. mockSSE() 呼び出しを定数参照に統一（app.js, 各 HTML）
3. docs/mockups/CHANGELOG.md + 日記 #entry-HHMM
4. commit + push + hash 追記

## 範囲外
- FastAPI / src/yoruu/api/sse/ / JSON Schema 新設
- ch24 WS 実装、ch10/ch24 の SSE エンドポイント再設計
- T4.2〜T4.9

## 完了報告
- hash、11 イベント before/after、B1 クローズ宣言、T4.2 申し送り
- push 直前 git pull --rebase
```

**注意**: FastAPI 契約・全 SSE severity 必須化は **テンプレ 9** `PHASE3-sse-contract`（PHASE 4 キックオフ時）。

---

## テンプレート 8 — `PHASE3-fix` 継続（Track 1 第二フェーズ）

**チャット名**: `PHASE3-fix`（継続）  
**モデル**: Composer 2.5  
**投入**: **テンプレ 7 と並列可**（`tests/**` vs `docs/mockups/**`）

```
# Track 1 第二フェーズ: coverage 80% 化 + InvariantChecker 全件 UT + A-MED 残対応

## 役割
Composer 2.5。PHASE 3 Exit ブロッカー（カバレッジ 80%、InvariantChecker UT、A-MED）の実装・テストのみ。
設計章は触らない（Track 2 完了済み・SSOT 確定）。

## 前提
- リポジトリ: f:\Cursor\YoRuu / main
- 前提コミット: ff9f4e6（または 0030f6d / c8fa393）
- 並列: phase2-sse（テンプレ 7）— 衝突なし
- SSOT（読取のみ）: ch16 §16.3 / §16.3.1（INV-D-06）、ch13 §13.2.5 D11、ch18 §18.3

## マスター判定（変更不可）
- 設計章変更禁止
- INV-D-06 UT 追加（inv_d06_balance_conservation、閾値 0.02 USD）
- fail_under 段階引き上げ: 55 → 70 → 80（一気に 80 で赤放置禁止）
- paper_executor: time.sleep → asyncio.sleep 統一（残存撲滅）

## スコープ
### 1. InvariantChecker 全件の個別ユニットテスト
- 対象: **ch16 §16.2〜16.5 の全 INV-* 19 件**（INV-S 5 + INV-D 6 + INV-R 5 + INV-M 3、INV-D-06 含む）
- 実装側は `src/yoruu/safety/invariants.py` の対応チェック全件をテスト対象とする
- tests/safety/test_invariants_individual.py（または既存へ追記）
- 各 INV 最低 3 ケース: 正常 / 違反 / 境界（INV-D-06 は閾値 0.02 USD 厳密、ch16 §16.3.1）
- severity 判定（ch16 §16.6 / ch18 §18.3）も assertion 対象

### 2. カバレッジ 80%
- pytest --cov=src/yoruu --cov-report=term-missing で穴埋め
- pyproject.toml fail_under を 70 コミット → 80 コミット

### 3. A-MED 残（監査 §F 一覧化 → 迷ったら停止）
- paper 非同期 sleep 他、Track 1 残があれば対応 or 申し送り

### 4. pytest-asyncio 整備（flaky 対策）

## 範囲外
- docs/design/**、WS クライアント、REST API 本体、24h paper、Track 4

## 成果物
- tests/** 補強、pyproject.toml、executor sleep 修正、日記、commit(s)+push

## 完了報告
- hash 一覧（55→70→80 段階含む）、最終 coverage
- InvariantChecker UT 追加件数（**19 件 × ケース数**、INV-S/D/R/M 内訳付き）
- INV-D-06 境界検証（0.02 USD ちょうど）、A-MED 解消/申し送り
- PHASE 3 Exit ブロッカーへの寄与、phase2-sse とのマージ衝突有無
- push 直前 git pull --rebase
```

---

## テンプレート 9 — `PHASE3-sse-contract`（FastAPI SSE 契約）

**チャット名**: `PHASE3-sse-contract`  
**モデル**: Composer 2.5  
**投入**: テンプレ 12（`18fb05c`）完了後

```
# FastAPI SSE 契約（ch10 §10.5.3 / mock-data.js B1 準拠）

## スコープ
1. src/yoruu/api/sse/ — Pydantic 11 イベント、validate_sse_payload、LAB_SSE_FIXTURES
2. ValidatingEventBus — publish 時に契約検証
3. GET /api/v1/sse/contracts, /sse/fixtures — SSE /events/stream は payload のみ data 行
4. StrategyApplier の strategy_applied に rationale / applied_at 付与
5. POST /strategy/apply, /strategy/rollback — StrategyApplier 本実装
6. paper-24h --max-cycles（lab smoke）

## 範囲外
- ch10 v1.2 severity 全イベント必須化ローリング
- 実 24h 連続実行（ハーネス検証のみ）

## 完了報告
- pytest、coverage、B1 フィールド一致、apply/rollback API、paper-24h smoke
```

---

## テンプレート 10 — `phase2-i18n-palette`（§F T4.2）

**チャット名**: `phase2-i18n-palette`  
**モデル**: Composer 2.5  
**投入**: `phase2-sse` 完了後（`7cbfd49` 推奨）。**テンプレ 11 と並列可**

```
# Track 4.2: i18n フォールバック + 緊急停止パレット + nightly モック整合

## 役割
Composer 2.5。Track 4.2 単独実行。Track 2D で確立した設計 SSOT
（ch18 §18.3 severity / ch08 §8.4.3 パレット / ch14 §14.5 i18n フォールバック / §14.11.4 CI 規約）
をモック層と i18n bundle に実装適用。設計章は触らない（Track 2 SSOT 確定済み）。

## 前提
- リポジトリ: f:\Cursor\YoRuu / main
- 前提コミット: 7cbfd49（phase2-sse 完了）。9e752d5 でも可
- 並列: PHASE3-fix-inv-d02（テンプレ 11）— 衝突なし
- 設計 SSOT（読取のみ）: ch08 §8.4.3 / §8.7.4 / §8.25.3、ch14 §14.5 / §14.11.4、ch18 §18.3、ch10 §10.5.3

## マスター判定（変更不可）
- W_* プレフィックス完全排除（Q1=A）
- E_NIGHTLY_008 二段義: 10% → WARN、20% → ERROR
- i18n 解決順: ja → en → key、en フォールバック時 WARN ログ
- 緊急停止パレット: ERROR=赤、WARN=黄、短縮一致禁止
- build_locales.py --check: ja/en キー集合一致、差分で fail

## スコープ
### 1. nightly-review.js — W_NIGHTLY_001 → E_NIGHTLY_008
- docs/mockups/shared/nightly-review.js
- severity: 10% → WARN、20% → ERROR（ch18 §18.3）

### 2. i18n bundle — error.e_nightly_008.*
- docs/mockups/shared/locales/ja.bundle.js、en.bundle.js
- 推奨: error.e_nightly_008.warn / error.e_nightly_008.error
- W_NIGHTLY_001 関連キー削除、ja/en キー集合完全一致

### 3. ch08 緊急停止パレット
- docs/mockups/shared/styles/ または該当 CSS/JS
- --severity-error-color / --severity-warn-color（ch08 既存トークン参照）
- emergency_stop_triggered 表示箇所に適用、severity === 完全一致のみ

### 4. tools/build_locales.py --check + CI
- ja/en キー差分 → exit 非 0、stderr に差分明示
- .github/workflows/ に PR 時チェック追加（ch14 §14.11.4）

### 5. i18n フォールバック（ランタイム）
- docs/mockups/shared/i18n.js（または既存ヘルパー）
- ja → en（console.warn）→ key

## 範囲外
- docs/design/** 変更、src/yoruu/**、INV-D-02（テンプレ 11）、T4.1 再修正、ch24/FastAPI/24h paper
- 他 SSE イベントへの severity 追加（設計変更）

## 成果物
- nightly-review.js、locales、styles/i18n、tools/build_locales.py、CI、CHANGELOG、日記、commit+push

## 完了報告
- hash、W→E 置換件数、i18n キー、パレット箇所、--check 正常/差分、CI 追加箇所、テンプレ 11 との衝突有無
- push 直前 git pull --rebase
```

---

## テンプレート 11 — `PHASE3-fix-inv-d02`（INV-D-02 実装）

**チャット名**: `PHASE3-fix-inv-d02`  
**モデル**: Composer 2.5  
**投入**: `PHASE3-fix` 完了後（`579402f` 推奨、`cb0e0f5` 以降可）。**テンプレ 10 と並列可**

```
# INV-D-02 実装: daily_pnl キャッシュ整合性検査

## 役割
Composer 2.5。PHASE3-fix 派生。ch16 §16.3 INV-D-02 実装漏れを解消。
§16.6 severity 表への INV-D-02 行追加は ch16 v1.0.2 ローリングで実施。

## 前提
- リポジトリ: f:\Cursor\YoRuu / main
- 前提コミット: 579402f（PHASE3-fix）。14f7b09 / cb0e0f5 以降可
- 並列: phase2-i18n-palette（テンプレ 10）— 衝突なし
- SSOT: ch16 §16.3（差 < $0.01）、§16.6（D-02 行追加）、ch13 §13.2.5 D11

## マスター判定（確定）
- Case A + 案 X: 日次集計 SQL + inv_d02 検査 + UT 3 件
- キャッシュ既存: bot_state.daily_pnl、get_daily_pnl / update_balance_and_pnl
- close 更新既存: PaperExecutor.close で daily_pnl += pnl
- 未実装: 当日 trades.pnl 集計（sum_closed_trade_pnl は全期間のみ）、inv_d02_*

## スコープ
### 1. 当日 trades.pnl 集計
- src/yoruu/data/database.py（※ persistence/ ディレクトリは未採用）
- sum_closed_trade_pnl_for_date(target_date) または sum_closed_trade_pnl_today()
- SUM(pnl) WHERE date(closed_at)=? AND closed_at IS NOT NULL、NULL → 0

### 2. inv_d02_daily_pnl_consistency()
- src/yoruu/safety/invariants.py
- INV_D02_TOLERANCE_USD = 0.01（INV_D06_TOLERANCE_USD と並列）
- diff = abs(trades_sum - cached); OK if diff < 0.01（境界 == 0.01 は違反）
- severity: ERROR

### 3. UT 3 ケース
- tests/safety/test_invariants_individual.py に追記
- ok / violate / boundary == 0.01（INV-D-06 パターン参照）

### 4. ch16 v1.0.2 ローリング
- docs/design/16_invariants.md §16.6 に INV-D-02 → ERROR
- INDEX.md、REVIEW_CHECKLIST_ch16.md 追記

### 5. カバレッジ
- fail_under=80 維持、pytest --cov 確認

## 範囲外
- 他 INV 修正、daily_pnl キャッシュ再実装、close ロジック変更、§16.3 定義変更、T4.2、ch24/FastAPI/24h

## 成果物
- database.py 集計、invariants.py、UT、ch16 v1.0.2、INDEX、CHECKLIST、日記、commit+push

## 完了報告
- hash、関数名、UT 結果、境界 $0.01 判定、coverage、ch16 v1.0.2、テンプレ 10 衝突有無
- INV 設計 19 = 実装 19 達成宣言
- push 直前 git pull --rebase
```

---

## テンプレート 12 — `PHASE3-exit-route-a`（PHASE 3 Exit 戦略 A）

**チャット名**: `PHASE3-exit-route-a`  
**モデル**: Composer 2.5  
**投入**: テンプレ 10/11 完了後（`2fc6f4f` / `a2b6081` 以降）

```
# PHASE 3 Exit 戦略 A — WS → CLOB → FastAPI → 24h paper

## 役割
Composer 2.5。PHASE3 残 4 項目をルート A 順で一括実装（lab 前提）。

## 前提
- リポジトリ: f:\Cursor\YoRuu / main
- fail_under=80、pytest --cov 緑
- lab URL のみ（wss://example.invalid、https://clob.lab.invalid）
- ch24 §24.9: テストは fixture / モック、live API 禁止

## スコープ（順序）
### 1. WebSocket 基盤（ch10 §10.8 / ch24 §24.7）
- AsyncWsClient（再接続・stale）
- PolymarketMarketWs / BinanceMarketWs
- market_runner + CLI `yoruu market run`

### 2. CLOB（ch24 §24.2 / §24.8）
- ClobRestClient（fixture + lab HTTP）
- ClobWsClient / PolymarketClient / LiveExecutor（E_WS_001）
- tests/fixtures/clob/

### 3. FastAPI 28 エンドポイント（ch10 §10.6）
- src/yoruu/web/app.py, routes/api_v1.py
- SSE `/api/v1/events/stream`（MemoryEventBus）
- CLI `yoruu serve`

### 4. 24h paper ハーネス
- CLI `yoruu paper-24h`（evaluate-once ループ）
- tools/paper_24h.py（任意）

### 5. テスト・依存
- httpx, websockets, fastapi, uvicorn, pytest-asyncio
- tests: test_api, test_infra_stack, test_clob_rest, test_event_bus

## 範囲外
- 本番 Polymarket/Binance 接続
- テンプレ 9 FastAPI SSE 契約の全面置換（B1 モックは維持）
- docs/design/** ローリング（ch16 以外）

## 成果物
- infra/web/cli 一式、pyproject 依存、テンプレ 12 索引、日記、commit+push

## 完了報告
- hash、pytest 件数、coverage%、CLI 3 コマンド、API スモーク、lab URL 確認
```

---

## テンプレート 14 — `phase4-hud-principal`（PHASE 4 M4.3〜M4.9 HUD + 元本）

**チャット名**: `phase4-hud-principal`  
**モデル**: Opus 4.7（M4.3 設計章）→ Composer 2.5（M4.4〜M4.8）  
**投入**: M4.2 完了後（`02edfa0` / `458d009` 以降）、案 Z ロードマップ承認後

**進行原則（2026-05-28）**: Opus 推奨を既定採用。マスター明示修正まで推奨で確定。一覧は [`PHASE4_ROADMAP_v1.md`](./PHASE4_ROADMAP_v1.md) 確定事項表。

**正本**

- [`PHASE4_ROADMAP_v1.md`](./PHASE4_ROADMAP_v1.md)（I-1 / 案 P 確定）
- [`PRINCIPAL_CONCEPT_V1_DRAFT.md`](./PRINCIPAL_CONCEPT_V1_DRAFT.md)
- [`../mockups/REF_IMAGE_GAP_MATRIX_v2.md`](../mockups/REF_IMAGE_GAP_MATRIX_v2.md)

```
# PHASE 4 M4.3〜M4.9: 参照 HUD + 元本概念（A-2/B-2）

## 確定方針（再掲）
- 新規 00_hud.html、既存 01〜10 + mock-data ロジック温存（集約ビューアのみ）
- ヒーロー: balance + withdrawable_principal 併記 + 累積 PnL
- 夜間: カウントダウンのみ → 03_nightly_review リンク
- システム枠: SSE + 稼働 + その他（Telegram 不採用）
- ローソク: HUD はプレースホルダのみ（PHASE 5）
- Hub/HUD: I-1 — index 温存、00_hud 主入口、相互リンク
- 通貨表示: E-1 + F-2（USD 内部、HUD JPY/USD トグル、`GET /api/v1/fx/usd_jpy`）
- 会計 H-1: balance=自由資金、locked_principal 列なし、total_assets=balance+locked
- U-2 REAL、案 P（M4.6→M4.7）
- ch10 v1.2 / ch13 v1.0.5 ローリング済（2026-05-28）

## 段階 1 — M4.3 設計章追補（Opus、実装触らない）
1. ch10 v1.2: bot_state 列 + principal_transactions + severity 必須化（任意同梱）
2. ch13 D11 v2: 入金/出金/open/close の principal/locked/balance 更新
3. ch16 INV-D-06 v2 + invariant 3 件
4. ch22: initial_principal + 旧キー後方互換
5. INDEX / ROADMAP 差し替え（PHASE4_ROADMAP_REVISION 承認内容）

## 段階 2 — M4.4 コア（Composer）
- マイグレーション、PrincipalService、PaperExecutor D11 v2
- InvariantChecker 拡張、単体テスト
- 出口: pytest 全緑、coverage ≥ 80%

## 段階 3 — M4.5 API/CLI（Composer）
- POST/GET /api/v1/principal/*
- SSE principal_changed（mock-data.js + api/sse/models.py + ValidatingEventBus）
- yoruu principal deposit|withdraw|show

## 段階 4 — M4.6 mock-data（Composer）
- principal, locked_principal, withdrawable_principal, signal_counts, cumulative_stats, system_status
- 既存 10 画面の mock 動作不変

## 段階 5 — M4.7 HUD HTML（Composer）
- docs/mockups/00_hud.html（参照レイアウト、shared/*.js 再利用）
- 入金ボタン UI（API 呼び出しは M4.5 完了後に結線）
- 出口: Hub↔HUD 相互リンク、主入口 00_hud、チャート placeholder
- HUD: JPY/USD トグル（localStorage）、formatCurrency + fx API（F-2）
- ヒーロー: total_assets 巨大表示、副欄 balance（追加可能元本）、PnL 段
- 中間: ダミー値スケルトンで視覚レビュー可（案 P）

## 段階 6 — M4.8 static + i18n（Composer）
- ja bundle HUD キー、tools/build_web_static.py（00_hud 取り込み）
- serve で HUD + principal_changed 反映

## 段階 7 — M4.9 Exit（Opus）
- PHASE4_EXIT_DECLARATION.md

## 範囲外
- ローソク足実装（PHASE 5）
- 既存 01_dashboard.html 等の全面リライト
- docs/mockups/ 削除

## 完了報告（各段階）
- commit hash、pytest 件数、coverage%、承認済み設計章 ID
```

---

## テンプレート 13 — `phase4-m42-static-ui`（PHASE 4 M4.2 静的 UI 結線）

**チャット名**: `phase4-m42-static-ui`  
**モデル**: Composer 2.5  
**投入**: PHASE 3 コード Exit 後（`48c47f4` / `f235ab0` 以降）

```
# PHASE 4 M4.2: 静的モック → Web UI 結線

## スコープ
1. tools/build_web_static.py — docs/mockups → src/yoruu/web/static/
2. web/app.py — /static, /pages, GET / リダイレクト
3. static/js/sse-client.js — EventSource → /api/v1/events/stream
4. mock-data.js dispatchSseEvent + app.js 緊急停止 REST
5. tests/web/ — 静的配信 + SSE 契約
6. ?mock=1 でモック SSE フォールバック

## 完了基準
- uv run yoruu serve → http://localhost:8765/pages/index.html
- 11 HTML + B1 契約 SSE、119 tests / 88% coverage
- docs/mockups/ は削除しない（正本維持）

## 範囲外
- docs/design/** 変更、Playwright E2E、ch10 v1.2 severity ローリング
```

---

## Track 2 — Opus ローリング（§J.4〜J.7）

**前提コミット（全チャット共通）**: `085cad5`（docs-sync）、`f499778`（Track 1）

### 推奨投入順序（§L 並列度 ≤ 3）

| 段階 | チャット | 並列 |
|------|----------|------|
| 1 | `ch3-rolling` + `ch10-rolling` | 2 同時 |
| 2 | `ch13-ch22-fillmodel` | 段階1のいずれか完了後 |
| 3 | `ch18-error-codes` | 段階2と 1 並列可、**単独推奨**（5 章・T4.2 ゲート） |

**INDEX 衝突**: 4 チャットすべてが INDEX を更新。後着はマージ確認。

貼り付け全文はマスター清書版（2026-05-28）を正本とする。概要:

| テンプレ | チャット | Track | 監査 |
|----------|----------|-------|------|
| 3 | `ch3-rolling` | 2A | §J.4 |
| 4 | `ch10-rolling` | 2B | §J.5 |
| 5 | `ch13-ch22-fillmodel` | 2C | §J.6 |
| 6 | `ch18-error-codes` | 2D | §J.7 |

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-05-28 | 初版（§F 厳密対応・Q3-MOCK 分離・パス修正・INV-D-06 式・fail_under 55） |
| 2026-05-28 | Track 2 投入順序・§J.4〜J.7 索引追加 |
| 2026-05-28 | テンプレ 7 `phase2-sse`（§F T4.1 B1 スリム）、8 Track1 第二フェーズ、9 `PHASE3-sse-contract` 索引 |
| 2026-05-28 | テンプレ 8: ch16 INV **19 件**（§16.2〜16.5）表記訂正（旧「15 件」廃止） |
| 2026-05-28 | テンプレ 7/8 完了状態反映、テンプレ 10 `phase2-i18n-palette`（T4.2）、11 `PHASE3-fix-inv-d02`（INV-D-02）追記 |
| 2026-05-28 | テンプレ 12 `PHASE3-exit-route-a`（Exit 戦略 A: WS/CLOB/FastAPI/24h paper）追記、10/11 完了反映 |
| 2026-05-28 | テンプレ 13 `phase4-m42-static-ui`（PHASE 4 M4.2）追記・完了反映 |
| 2026-05-28 | テンプレ 14 `phase4-hud-principal`（M4.3〜M4.9 HUD+元本、案 Z）追記 |
| 2026-05-28 | テンプレ 14: I-1 / 案 P 確定、PHASE4_ROADMAP_v1 正本化 |
