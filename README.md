<div align="center">

# YoRuu

### 夜間レビューで進化する、Polymarket BTC 5分 Up/Down 自動売買 Bot

*Markov · Kelly · Zero LLM at runtime · Human-in-the-loop nightly review*

<br>

[![Status](https://img.shields.io/badge/status-PHASE_3_core-1a1a2e?style=for-the-badge&logo=gitbook&logoColor=c9b8ff&labelColor=2d2d44)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu/blob/main/docs/design/INDEX.md)
[![Version](https://img.shields.io/badge/version-0.3.0-6c5ce7?style=for-the-badge)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-ready-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3.40+-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Polymarket](https://img.shields.io/badge/market-BTC_5min_Up%2FDown-6c5ce7?style=for-the-badge&logo=bitcoin&logoColor=white)](https://polymarket.com/)
[![Strategy](https://img.shields.io/badge/strategy-Markov_%2B_Kelly-2d7a3e?style=for-the-badge)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu)
[![LLM Cost](https://img.shields.io/badge/runtime_LLM-$0-00b894?style=for-the-badge)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu)
[![License](https://img.shields.io/badge/license-unlicensed_(private)-555555?style=for-the-badge)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu)

<br>

[![Docs](https://img.shields.io/badge/docs-24_chapter_APPROVED-7c3aed?style=flat-square&logo=readthedocs&logoColor=white)](docs/design/)
[![Mockups](https://img.shields.io/badge/UI-HTML_mockups_11%2F11-d68910?style=flat-square&logo=html5&logoColor=white)](docs/mockups/)
[![Modes](https://img.shields.io/badge/modes-4_(backtest·paper·simmer·live)-2c5f8d?style=flat-square)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu)
[![Infra](https://img.shields.io/badge/deploy-Hetzner_VPS_|_local-24292f?style=flat-square&logo=serverless&logoColor=white)](https://www.hetzner.com/)
[![Review](https://img.shields.io/badge/nightly_review-human_+_Opus_4.7-a78bfa?style=flat-square&logo=anthropic&logoColor=white)](docs/design/00_INSTRUCTIONS_ch01-07.md)
[![Risk](https://img.shields.io/badge/⚠_not_financial_advice-self_responsibility-c0392b?style=flat-square)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu)

<br>

[概要](#概要) ·
[Quick Start](#quick-start) ·
[特徴](#特徴) ·
[アーキテクチャ](#アーキテクチャ) ·
[動作モード](#動作モード) ·
[夜間レビュー](#夜間レビュー) ·
[ドキュメント](#ドキュメント) ·
[ロードマップ](#ロードマップ) ·
[免責](#免責事項)

</div>

---

## 概要

**YoRuu**（ヨルー）は、Polymarket の **BTC 5分 Up/Down** 市場向けに設計された個人運用型の自動売買 Bot である。  
取引判定は **Markov 2状態遷移** と **Kelly 基準** による純粋な Python 数式のみで行い、**ランタイムでは LLM を一切使用しない**。

「夜（Yo）」とループ感のある響き（Ruu）から名付けられた通り、**1日1回の夜間レビュー**で戦略パラメータを人間が監督しながら進化させる——安全とコスト効率を両立する設計が核となる。

> **設計思想**  
> Bonereaper 系エージェントの「再現」ではなく、本質（Markov + Kelly・低コスト運用）を抽出した **自分用の実装**。  
> Telegram 通知は廃止し、**Web UI + ローカルファイル + CLI** に集約する。

| | |
|---|---|
| **対象市場** | Polymarket · BTC 5分 Up/Down |
| **判定頻度** | 5分ごと（最大 288 回/日） |
| **戦略** | Markov persistence + Kelly sizing |
| **夜間レビュー** | レポート JSON → Genspark / Opus 4.7 → Web UI で apply |
| **想定運用** | ローカル PC または Hetzner VPS（〜 $6/月） |
| **現フェーズ** | **PHASE 3** コア実装（Track 1・2 完了、モック契約 T4.1 着手前、Web UI は PHASE 4） |
| **テスト** | `pytest` 20 passed、カバレッジ ≈65%、`fail_under` **55** → 70 → 80 |

### PHASE 3 トラック進捗（2026-05-28）

| Track | 内容 | 状態 | 参照コミット |
|:---|:---|:---:|:---|
| 1 | A-HIGH 8 + Q1〜Q3 実装 | 完了 | `f499778` |
| 2 | 設計書ローリング（ch3/10/13/16/22/08/11/14/15/18） | 完了 | `c8fa393` |
| 3 | README / INDEX / ROADMAP / CHECKLIST | 完了 | `085cad5` |
| 4 | モック後修正（§F T4.1〜T4.9） | **次**: T4.1 SSE（B1） | — |

並列投入テンプレ: [`docs/design/PHASE3_PARALLEL_CHAT_TEMPLATES.md`](docs/design/PHASE3_PARALLEL_CHAT_TEMPLATES.md)

### マスター判定サマリ（Q1〜Q3）

| ID | 判定 | 設計 / 実装要点 |
|:---|:---|:---|
| Q1 | A | `W_NIGHTLY_001` → `E_NIGHTLY_008`（†10% WARN / ‡20% ERROR、ch18 §18.3.4） |
| Q2 | A | `FillModel` 既定値は ch22 §22.2.1 SSOT |
| Q3 | A | open 時 `balance` 減算、close 時加算 + **INV-D-06**（ch16 §16.3.1） |

---

## Quick Start

前提: Python 3.11+、[uv](https://github.com/astral-sh/uv) 推奨。

```powershell
cd YoRuu
uv sync
copy config\yoruu.yaml.example config\yoruu.yaml
uv run yoruu config validate
uv run yoruu db init
uv run yoruu paper evaluate-once
uv run yoruu nightly generate
uv run yoruu strategy apply path\to\proposal.json --by USER
uv run pytest -q
```

設計 SSOT: [`docs/design/INDEX.md`](docs/design/INDEX.md)、PHASE 3 監査: [`docs/design/PHASE3_QUALITY_AUDIT.md`](docs/design/PHASE3_QUALITY_AUDIT.md)。

**カバレッジ `fail_under`**: 現状 **55**（Track 1 後暫定）→ **70**（安定化後）→ **80**（PHASE 3 Exit、ch23 §23.3）。**50 は使用しない。**

---

## 特徴

<table>
<tr>
<td width="50%" valign="top">

### 安全性ファースト

- 信頼境界線に基づく入力検証（外部 API · AI JSON · UI）
- **不変条件**（`MIN_PROB` · `KELLY_FRACTION` 等）の機械的 assert
- **キル・スイッチ** · 二重承認（paper → live は `"LIVE"` 手入力）
- `strategy.json` はバックアップ後にのみ上書き
- 監査ログ（append-only）

</td>
<td width="50%" valign="top">

### シンプル & 低コスト

- ランタイム LLM API コスト **$0**（夜間レビューは既存 Genspark 契約）
- Python 単体（Hermes 等のエージェント基盤なし）
- SQLite + JSON · 単一 `yoruu.yaml` 設定
- UI は **Vanilla HTML/CSS/JS**（モックアップから本実装へ移植）

</td>
</tr>
<tr>
<td width="50%" valign="top">

### テスト可能性

| モード | 用途 |
|:---|:---|
| `backtest` | 過去データで戦略検証 |
| `paper` | リアルタイム・仮想約定 |
| `simmer` | Polymarket 向けペーパー連携 |
| `live` | 本番（多段確認必須） |

</td>
<td width="50%" valign="top">

### 可観測性

- 構造化ログ（`structlog`）+ エラーコード体系
- 取引ログ · ポジション · 日次レポート JSON
- 戦略パラメータのバージョン履歴
- `mode: live` 時は UI 全体で視覚的警告（赤バー）

</td>
</tr>
</table>

---

## アーキテクチャ

```mermaid
flowchart TB
    subgraph External["外部（非信頼）"]
        BN[Binance WS]
        PM[Polymarket CLOB]
        AI[Opus 4.7 via Genspark]
    end

    subgraph YoRuu["YoRuu Core"]
        PA[Price Aggregator]
        SE[Strategy Engine<br/>Markov + Kelly]
        OM[Order Manager]
        PT[Position Tracker]
    end

    subgraph Modes["Mode Executors"]
        BT[backtest]
        PP[paper]
        SM[simmer]
        LV[live]
    end

    subgraph Persist["永続化"]
        DB[(SQLite)]
        SJ[strategy.json]
        RP[reports/]
    end

    subgraph UI["Web UI"]
        WEB[FastAPI + HTML/CSS/JS]
    end

    BN --> PA --> SE --> OM
    PM <--> OM
    SE --> Modes
    OM --> PT
    PT --> DB
    OM --> DB
    SE --> SJ
    RP --> AI
    AI --> WEB
    WEB --> SJ
    WEB --> OM
    Modes --> PM
```

<details>
<summary><strong>レイヤー構成（クリックで展開）</strong></summary>

| レイヤー | コンポーネント | 責務 |
|:---|:---|:---|
| データソース | Binance WS · Polymarket REST/WS | 価格・板・注文 |
| コア | Strategy Engine · Order Manager | 判定・発注・ポジション |
| モード | 4 Executors | 戦略結果の実行先分岐 |
| 永続化 | SQLite · JSON | 取引・監査・戦略・レポート |
| UI | FastAPI Web | 操作・監視・apply · 緊急停止 |
| 横断 | Scheduler · Logger · Safety | 5分境界 · ログ · 不変条件 |

</details>

---

## 動作モード

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  backtest   │ ──▶ │    paper    │ ──▶ │   simmer    │ ──▶ │    live     │
│  過去検証   │     │  仮想約定   │     │  外部PT連携 │     │  本番取引   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │                    │
       └────────────────────┴────────────────────┴────────────────────┘
                    各段階で不変条件・損失上限・監査ログが有効
```

| モード | 実取引 | 典型用途 |
|:---|:---:|:---|
| `backtest` | ✗ | パラメータ探索・回帰テスト |
| `paper` | ✗ | フォワード検証（リアルタイム） |
| `simmer` | ✗ | Polymarket エコシステムとの整合確認 |
| `live` | ✓ | 本番（二重承認 · 残高確認 · UI 赤強調） |

---

## 夜間レビュー

毎日、設定時刻に `report_YYYY-MM-DD.json`（集計データ + AI 用プロンプト）をローカル出力。  
人間が Genspark 経由で **Opus 4.7** に分析を依頼し、返却 JSON を Web UI で検証・二重承認のうえ `strategy.json` に反映する。

```
  report.json ──copy──▶ Opus 4.7 ──copy──▶ Web UI (/review)
       ▲                      │                    │
       │                      │                    ▼
  Scheduler              人間が監督          Schema + Range 検証
  (send_time)                                 Diff プレビュー
                                                    │
                                                    ▼
                                            strategy.json + audit_log
```

| ステップ | 操作 | 安全装置 |
|:---:|:---|:---|
| 1 | レポートをコピー（または添付） | ローカル保存のみ（NW 不要） |
| 2 | AI 分析 → JSON を取得 | 人間が内容を確認 |
| 3 | Web UI に貼り付け | 即時スキーマ検証 + 差分表示 |
| 4 | Apply 確定 | 範囲検証 · `E_NIGHTLY_008`（±10% 警告 / ±20% 拒否）· バックアップ |

---

## ドキュメント

| 種別 | パス | 説明 |
|:---|:---|:---|
| 設計指示書（第1〜7章） | [`docs/design/00_INSTRUCTIONS_ch01-07.md`](docs/design/00_INSTRUCTIONS_ch01-07.md) | Cursor / Opus 4.7 向け生成仕様 |
| レビュー用チェックリスト | [`docs/design/REVIEW_CHECKLIST_ch01-07.md`](docs/design/REVIEW_CHECKLIST_ch01-07.md) | 第1〜7章の人間レビュー基準 |
| 開発日記 | [`docs/2026-05-27_開発日記.html`](docs/2026-05-27_%E9%96%8B%E7%99%BA%E6%97%A5%E8%A8%98.html) | 設計判断の時系列ログ |
| UI モックアップ | [`docs/mockups/`](docs/mockups/) | HTML 11/11 · オフライン動作（PHASE 2 完了） |
| 設計 INDEX | [`docs/design/INDEX.md`](docs/design/INDEX.md) | 24章 + 付録 A APPROVED |
| PHASE 3 監査 | [`docs/design/PHASE3_QUALITY_AUDIT.md`](docs/design/PHASE3_QUALITY_AUDIT.md) | A-HIGH / 4 Track |
| 並列チャットテンプレ | [`docs/design/PHASE3_PARALLEL_CHAT_TEMPLATES.md`](docs/design/PHASE3_PARALLEL_CHAT_TEMPLATES.md) | docs-sync / Q3-MOCK / Track 2 / T4.1 |
| 開発日記 | [`docs/2026-05-28_開発日記.html`](docs/2026-05-28_%E9%96%8B%E7%99%BA%E6%97%A5%E8%A8%98.html) | Track 1〜2 ローリングログ |

### 設計書 24章（APPROVED）

<details>
<summary><strong>章一覧を表示</strong></summary>

| # | 章 | モック更新 |
|:---:|:---|:---:|
| 1 | 概要 | — |
| 2 | アーキテクチャ概観 | — |
| 3 | 状態遷移図 | — |
| 4 | データフロー図（DFD） | — |
| 5 | 信頼境界線図 | — |
| 6 | シーケンス図 | — |
| 7 | I/O 図 | — |
| 8 | **UI モックアップ一式** | ★ 全画面初版 |
| 9〜24 | 操作フロー · 戦略 · 安全 · デプロイ 等 | 該当画面を随時更新 |

</details>

---

## リポジトリ構成

```
YoRuu/
├── README.md
├── pyproject.toml            # v0.3.0, fail_under 55
├── config/yoruu.yaml.example
├── docs/design/              # 設計書 24章 + 付録 A
├── docs/mockups/             # PHASE 2 モック 11画面
├── src/yoruu/
│   ├── cli.py
│   ├── core/                 # StateMachine, EventBus
│   ├── strategy/             # Markov, Kelly, Evaluator
│   ├── execution/            # PaperExecutor, FillModel
│   ├── data/                 # SQLite schema
│   ├── review/               # Nightly, Apply
│   └── safety/               # Invariants
└── tests/
```

---

## ロードマップ

| フェーズ | 内容 | 状態 |
|:---|:---|:---:|
| **PHASE 0** | ch1〜7 基盤合意 | 完了 |
| **PHASE 1** | 設計書 24章 + 付録 A | 完了（2026-05-27） |
| **PHASE 2** | HTML モック 11画面 | 完了（2026-05-27） |
| **PHASE 3** | コア CLI + 品質トラック | 着手中（Track 1・2 完了、T4.1 SSE 次） |
| **PHASE 4** | FastAPI Web UI + SSE | 予定（T4.1 完了後） |
| **PHASE 5〜7** | 統合テスト · ペーパー運用 · live | 予定 |

詳細: [`docs/design/00_ROADMAP.md`](docs/design/00_ROADMAP.md)

---

## 技術スタック

| カテゴリ | 選定 |
|:---|:---|
| 言語 | Python 3.11+ · [uv](https://github.com/astral-sh/uv) |
| CLI | Click（`yoruu` エントリポイント） |
| API / UI（PHASE 4） | FastAPI · SSE |
| 取引所 | py-clob-client（Polymarket 公式） |
| データ | SQLite · SQLAlchemy · alembic |
| 設定 | pydantic-settings · `yoruu.yaml` |
| ログ | structlog |
| テスト | pytest · pytest-asyncio |
| プロセス管理 | systemd / supervisor |

---

## 免責事項

> **本リポジトリは教育・個人研究目的の設計・実装プロジェクトである。**
>
> - 金融商品取引に関する助言・勧誘ではない  
> - 過去のバックテスト結果は将来の利益を保証しない  
> - `live` モードでの取引は **自己責任** — 損失上限・キルスイッチを必ず理解したうえで運用すること  
> - API キー・秘密鍵は `.env` で管理し、リポジトリにコミットしない  

---

<div align="center">

<br>

**YoRuu** — *trade with math. evolve at night.*

<br>

[![GitHub](https://img.shields.io/badge/GitHub-matrix9neonebuchadnezzar2199--sketch%2FYoRuu-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu)
[![Issues](https://img.shields.io/github/issues/matrix9neonebuchadnezzar2199-sketch/YoRuu?style=for-the-badge&logo=github)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu/issues)
[![Stars](https://img.shields.io/github/stars/matrix9neonebuchadnezzar2199-sketch/YoRuu?style=for-the-badge&logo=github&color=c9b8ff)](https://github.com/matrix9neonebuchadnezzar2199-sketch/YoRuu/stargazers)

<sub>README · v0.3.0 · PHASE 3 · Track 2 完了 · last updated 2026-05-28</sub>

</div>
