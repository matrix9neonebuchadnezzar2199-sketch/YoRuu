# PHASE 3 並列チャット — 貼り付け用テンプレ（修正版）

> **目的**: `PHASE3_QUALITY_AUDIT.md` §F / §J.2 / §J.3 / §L と ID 衝突しないよう調整した **そのまま貼れる** 依頼文。  
> **運用**: Track 3 先行 + `phase2-fix` は **Q3-MOCK のみ**（監査書 **T4.1 SSE とは別スコープ**）を `docs-sync` と並列可。  
> **正本**: 監査書 §F の T3.1〜T3.9 / T4.1〜T4.9。本ファイルのチャット用 ID は §F と **1:1 対応表** で併記する。

### 投入チャット索引（テンプレ 7〜9）

| # | ID | 状態 | 前提コミット | 触る領域 | 備考 |
|---|----|------|--------------|----------|------|
| 7 | `phase2-sse` | 投入可 | `ff9f4e6` | `docs/mockups/shared/` | §F T4.1 / B1 スリム |
| 8 | `PHASE3-fix`（継続） | 投入可 | `ff9f4e6` | `tests/**`, `src/yoruu/safety/` 等 | Track 1 第二フェーズ |
| 9 | `PHASE3-sse-contract` | 索引のみ | TBD | `src/yoruu/api/sse/`, ch10/ch24 | PHASE 4 前提、本文後日清書 |

**並列推奨（§L ≤ 3）**: テンプレ 7 + テンプレ 8 は **同時投入可**（ファイル衝突なし）。

---

## 調整メモ（貼り付け前チェック）

| # | 論点 | 対応 |
|---|------|------|
| 1 | マスター案の T3.x が §F と別定義になりうる | テンプレ 1 は **§F ID 列** を必須。完了報告に §F ID を併記 |
| 2 | `phase2-fix` の「T4.1」表記 | **Q3-MOCK** と命名。監査 **T4.1 = SSE_PAYLOADS（B1）** は別チャット |
| 3 | モックパス | `sse-mock.js` / `dashboard.html` 等は **実リポジトリに無し** → `app.js` / `01_dashboard.html` 等 |
| 4 | INV-D-06 | `balance + Σ(open.size_usd) ≈ initial + Σ(closed.pnl)`（open 減算・close 加算） |

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
### 1. InvariantChecker 個別 UT
- ch16 §16.2〜16.5 の INV-S/D/R/M 全件（実装 invariants.py と対応）
- tests/safety/test_invariants_individual.py（または既存へ追記）
- 各 INV: 正常 / 違反 / 境界（INV-D-06 は 0.02 USD 厳密）

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
- hash 一覧、最終 coverage、INV UT 件数、INV-D-06 境界結果、A-MED 解消/申し送り、phase2-sse 衝突有無
```

---

## テンプレート 9 — `PHASE3-sse-contract`（索引のみ）

| 項目 | 内容 |
|------|------|
| 目的 | FastAPI SSE Pydantic 契約、ch24 中継方針、JSON Schema |
| 位置づけ | PHASE 4 前提。**§F T4.1（B1）とは別系統** |
| 着手 | テンプレ 7 完了 + PHASE 4 キックオフ判断後 |
| 本文 | マスター清書版（FastAPI 契約）を PHASE 4 時に本ファイルへ転記 |
| 前提設計変更 | severity 全 SSE 必須化は ch10 v1.2 ローリング + ADR が先 |

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
