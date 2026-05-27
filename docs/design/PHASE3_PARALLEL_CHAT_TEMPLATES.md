# PHASE 3 並列チャット — 貼り付け用テンプレ（修正版）

> **目的**: `PHASE3_QUALITY_AUDIT.md` §F / §J.2 / §J.3 / §L と ID 衝突しないよう調整した **そのまま貼れる** 依頼文。  
> **運用**: Track 3 先行 + `phase2-fix` は **Q3-MOCK のみ**（監査書 **T4.1 SSE とは別スコープ**）を `docs-sync` と並列可。  
> **正本**: 監査書 §F の T3.1〜T3.9 / T4.1〜T4.9。本ファイルのチャット用 ID は §F と **1:1 対応表** で併記する。

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
| T4.1 | SSE_PAYLOADS 整備（B1） | **テンプレ 2 対象外** — 別チャットで §J.3 本番 |
| — | Q3 残高モック整合 | **Q3-MOCK**（テンプレ 2） |

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
| 4 | 本番 **§F T4.1** SSE | Q3-MOCK 完了後、**別投入**。§G「T4.1 SSE + T4.3」と Q3-MOCK を混ぜない |

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-05-28 | 初版（§F 厳密対応・Q3-MOCK 分離・パス修正・INV-D-06 式・fail_under 55） |
