# YoRuu 設計書 生成指示書 — 第1〜7章

## このドキュメントの目的

このファイルは、YoRuu (Polymarket BTC 5-min Up/Down 自動売買Bot) の設計書 **第1章〜第7章** を生成するための、Cursor / Opus 4.7 向け指示書です。

Cursorで使用するモデル: **Claude Opus 4.7** (設計フェーズ)
出力先: `docs/design/01_overview.md` 〜 `docs/design/07_io_diagram.md` (章ごとにファイル分割)

---

## 全体ルール (全章共通)

### 言語・文体
- 日本語で記述する
- ですます調ではなく、技術文書として簡潔な**である調 / 体言止め**を併用
- 主観表現 (思います、でしょう) は禁止
- 章の冒頭に必ず「この章の目的」を1〜3行で記載

### 図の表現
- 図は原則 **Mermaid** で記述する
- Mermaidで表現困難なものは ASCII art を許容
- 図には必ずキャプション (`図 X-Y: ...`) を付ける
- 図中の文言は日本語OK、ただしコード識別子・関数名は英数字

### 用語統一
- 「ボット」ではなく「Bot」
- 「ユーザー」(ユーザではない)
- 「ペーパーモード」「ライブモード」(英数字混在せず、日本語表記で統一)
- 「夜間レビュー」(ナイトリーレビュー等は使わない)
- 「戦略パラメータ」(strategy parameters と併記)

### コードブロック
- Pythonコードは ```python フェンスを使用
- JSON例は ```json
- YAML例は ```yaml
- 設計段階なので**動作するコードは不要**、構造のみ示す

### 相互参照
- 他章を参照するときは `(→ 第X章 X.Y節)` の形式

---

## 出力ファイル構成

以下7ファイルを生成すること。

```
docs/design/
├── 01_overview.md         # 第1章 概要
├── 02_architecture.md     # 第2章 アーキテクチャ概観
├── 03_state_diagram.md    # 第3章 状態遷移図
├── 04_data_flow.md        # 第4章 データフロー図 (DFD)
├── 05_trust_boundary.md   # 第5章 信頼境界線図
├── 06_sequence.md         # 第6章 シーケンス図
└── 07_io_diagram.md       # 第7章 インプット/アウトプット図
```

---

## 第1章 概要 (`01_overview.md`)

### 含めるべき内容

#### 1.1 システムの目的
- YoRuu は Polymarket の BTC 5分 Up/Down 市場向けの自動売買Bot
- 個人開発者 1名 (本人) が自宅PCまたは VPS で運用することを前提
- 商用化・複数ユーザー対応は **スコープ外**
- 設計のインスピレーション元として "Claude × Hermes BTC 5-MIN Polymarket Agent (@Bonereaper)" の画像があるが、これを「再現」するのではなく**本質を抽出した自分用の実装**である旨を明記

#### 1.2 本家との差分 (重要)
以下の表形式で記載すること。

| 項目 | Bonereaper (オリジナル) | YoRuu (本実装) | 差分の理由 |
|---|---|---|---|
| 取引判定 | Markov + Kelly (LLM不使用) | 同じ | — |
| 夜間レビュー実行 | Claude Opus 4.7 が自動実行 | 人間が Genspark経由でOpus 4.7に手動依頼 | コストゼロ + 安全性向上 |
| 通知 | Telegram Bot | なし、すべて Web UI で完結 | シンプル化 |
| エージェント基盤 | Hermes Agent (NousResearch) | なし、Python単体 | 不要な複雑性の排除 |
| インフラ | Hetzner VPS | Hetzner VPS または ローカルPC | 同じ |
| モード | live のみ | backtest / paper / simmer / live の4モード | テスト可能性 |
| パラメータ適用 | 完全自動 | 検証 + 二重承認を経て適用 | 暴走防止 |

#### 1.3 想定ユーザー
- 1名のみ (本人)
- Python・Cursor・Cron・基本的なSQL の知識あり
- 投資判断は自己責任で行える
- マルチユーザー対応・認証・課金等は不要

#### 1.4 設計原則
箇条書きで5原則を記載。各原則に「これに反する例」「これに従う例」を1行ずつ添える。

1. **シンプルさ最優先**: 機能追加よりも既存機能の堅牢化を優先
2. **安全性は機能性に優先する**: 動かないより、誤動作する方がはるかに危険
3. **テスト可能性**: ライブモードに行く前に検証できないものは作らない
4. **低コスト運用**: 月額固定費は VPS 約$6/月のみを目標
5. **可観測性**: 何が起きたか後から完全に追える状態を維持

#### 1.5 スコープ
**スコープ内**:
- BTC 5分 Up/Down 市場での自動売買
- Markov + Kelly 戦略
- 4モード (backtest / paper / simmer / live)
- Web UI による操作・監視
- 夜間レビュー機構 (Opus 4.7 への手動連携)
- 戦略パラメータの安全な書き換え
- 監査ログ・キル・スイッチ

**スコープ外** (明示的に「やらない」):
- ETH / SOL / XRP など他資産
- 15分・1時間など他の時間枠
- 複数ユーザー対応・ログイン認証
- モバイルアプリ
- スマートコントラクト独自実装
- 機械学習モデルの自前訓練
- 高頻度取引 (HFT) 最適化
- 完全自動の夜間レビュー (Phase 2以降の検討事項)

#### 1.6 用語集
表形式で以下を必ず含める。

| 用語 | 英 | 定義 |
|---|---|---|
| Markov連鎖 | Markov chain | 直近状態のみから次状態の確率を推定する確率モデル |
| 持続状態 | Persistent state | 上昇または下降が連続している状態 |
| Persistence | — | 同一方向が連続する確率 (例: UP→UPの確率) |
| Kelly基準 | Kelly criterion | f* = p - (1-p)/b で最適賭け金比率を求める公式 |
| エッジ | Edge | モデル推定確率 p とマーケット価格 q の差 (p - q) |
| CLOB | Central Limit Order Book | 中央集権型指値注文板。Polymarketの取引方式 |
| EIP-712 | — | Ethereum の構造化データ署名規格、Polymarket注文に必須 |
| ペーパーモード | Paper mode | 実取引せず、リアルタイム市場で仮想約定するモード |
| Simmer | — | Polymarket向けペーパートレード提供サービス |
| persistence_threshold | — | エントリーを許可する最小持続確率 |
| MIN_PROB | — | エントリーを許可する最小モデル確率 |
| MIN_EDGE | — | エントリーを許可する最小エッジ |
| KELLY_FRACTION | — | Kelly基準の数値を実際にどれだけ使うかの係数 (0〜1) |
| 不変条件 | Invariant | 常に成立しなければならない条件 |
| キル・スイッチ | Kill switch | 緊急停止機構 |

#### 1.7 ドキュメント構成
本設計書全24章の章タイトル一覧を表で示し、それぞれの章で何を定義するかを1行で説明。

---

## 第2章 アーキテクチャ概観 (`02_architecture.md`)

### 含めるべき内容

#### 2.1 全体アーキテクチャ図
Mermaidで以下の構造を描画。

- **データソース層**: Binance WebSocket, Polymarket CLOB (REST + WS), Chainlink (オンチェーン参照、オプショナル)
- **コア層**: Price Aggregator, Strategy Engine (Markov + Kelly), Order Manager, Position Tracker
- **モード層**: Backtest / Paper / Simmer / Live の各 Executor (戦略結果を実際に何にするかを分岐)
- **永続化層**: SQLite (取引ログ・状態・監査), JSON (strategy.json, reports)
- **UI層**: Web UI (FastAPI + Vanilla HTML/CSS/JS)
- **レビュー層**: Daily Report Generator → ローカルファイル出力 → 人間 → Opus 4.7 → 戻り JSON → Apply Validator → strategy.json
- **横断的関心事**: Scheduler (cron), Logger, Audit Logger, Emergency Stop Monitor

矢印の方向と「誰が誰を呼ぶか」が一目でわかるレイアウトにする。

#### 2.2 技術スタック表

| 層 | 技術 | バージョン目安 | 選定理由 |
|---|---|---|---|
| 言語 | Python | 3.11+ | エコシステム、可読性、Polymarket SDK の対応 |
| Web Framework | FastAPI | 最新安定版 | 軽量、型安全、自動API docs |
| WS Client | websockets | — | 標準的・安定 |
| HTTP Client | httpx | — | async対応、リトライ書きやすい |
| Polymarket | py-clob-client | — | 公式 |
| DB | SQLite | 3.40+ | 単一ファイル、バックアップ容易、十分高速 |
| ORM | SQLAlchemy | — | 型安全、マイグレーション (alembic) |
| スケジューラ | APScheduler | — | cron相当、Python内で完結 |
| 設定 | pydantic-settings | — | 型検証込みYAML読込 |
| ログ | structlog | — | 構造化ログ、JSON出力可能 |
| テスト | pytest + pytest-asyncio | — | 標準 |
| Web UI | 素のHTML/CSS/JS | — | 依存最小、モックアップとの一貫性 |
| Web UI (リアルタイム) | Server-Sent Events | — | WebSocket より単純、十分 |
| プロセス管理 | systemd or supervisor | — | VPS運用標準 |

#### 2.3 デプロイ構成図
2パターンを描画。

- **パターンA**: ローカルPC運用 (開発・初期検証用)
- **パターンB**: Hetzner VPS運用 (本番)

それぞれで「どこにDBがあるか」「Web UIにどうアクセスするか」「秘密鍵はどこに置くか」を明示。

#### 2.4 ディレクトリ構造
完成形のディレクトリ構成を示す。

```
yoruu/
├── pyproject.toml
├── README.md
├── .env.example
├── yoruu.yaml.example
├── .cursor/
│   └── rules/
│       └── project.md       # Cursor運用ルール
├── docs/
│   ├── design/              # 設計書 (本ファイル群)
│   └── mockups/             # HTMLモックアップ
├── src/yoruu/
│   ├── __init__.py
│   ├── __main__.py          # CLI エントリポイント
│   ├── config.py            # 設定ファイル読み込み
│   ├── core/                # 戦略・約定・状態管理
│   ├── data/                # 価格データ取得
│   ├── exchange/            # Polymarket クライアント
│   ├── modes/               # 4モードの分岐実装
│   ├── review/              # 夜間レビュー
│   ├── persistence/         # DB, JSON I/O
│   ├── safety/              # 不変条件検証, キル・スイッチ
│   ├── audit/               # 監査ログ
│   ├── scheduler/           # cron的スケジューリング
│   ├── web/                 # FastAPI Web UI
│   └── utils/               # 共通ユーティリティ
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── scripts/                 # 運用補助スクリプト
```

各ディレクトリの責務を1行で説明する表も併記。

#### 2.5 横断的関心事 (Cross-cutting Concerns)
以下を別建てで定義。

- **ロギング**: 全モジュールが `structlog.get_logger(__name__)` を使う
- **エラー処理**: 例外は専用クラス階層 (`YoRuuError` を継承) を必ず通す
- **時刻**: 内部は全てUTC、表示時のみローカルTZに変換、ユーザー設定TZは `Asia/Tokyo` をデフォルト
- **乱数**: シード固定でテスト再現性を確保
- **シャットダウン**: SIGTERM受信で安全停止 (現ポジションをDB保存、新規発注停止、WS切断)

---

## 第3章 状態遷移図 (`03_state_diagram.md`)

### 含めるべき内容

#### 3.1 Bot全体の状態定義
以下8状態を Mermaid の stateDiagram-v2 で描画。

- `INITIALIZING` (起動直後、設定読込・DB接続)
- `IDLE` (稼働中だが取引時刻待ち)
- `TRADING` (5分ごとの判定・発注実行中)
- `MONITORING_POSITION` (約定後、決済待ち)
- `GENERATING_REPORT` (夜間レビュー時刻、レポート生成中)
- `AWAITING_APPLY` (レポート出力済、ユーザーからのapply待ち)
- `APPLYING_STRATEGY` (新パラメータ検証・適用中)
- `EMERGENCY_STOP` (キル・スイッチ発動、全停止)
- `SHUTDOWN` (正常終了処理中)

#### 3.2 遷移条件
各遷移に **トリガー** と **ガード条件** (許可される前提) を明記。

例:
- `IDLE → TRADING`: トリガー = 5分境界到達、ガード = `daily_loss < daily_loss_limit AND mode ∈ {paper, simmer, live}`
- `* → EMERGENCY_STOP`: トリガー = キル・スイッチ押下 OR daily_loss_limit 超過 OR 連続注文失敗3回、ガード = なし (常に許可)

#### 3.3 遷移時の副作用
状態遷移時に必ず実行される処理を記載。

| 遷移 | 副作用 |
|---|---|
| `* → EMERGENCY_STOP` | 全WS切断、未約定注文キャンセル試行、状態をDBに永続化、Web UIに最大強調表示 |
| `IDLE → TRADING` | 監査ログに記録 |
| `AWAITING_APPLY → APPLYING_STRATEGY` | strategy.json バックアップ作成 |
| ... | ... |

#### 3.4 禁止される遷移
明示的に「これは絶対起きてはいけない遷移」を列挙。実装時に assert で防ぐ対象。

例:
- `EMERGENCY_STOP → TRADING` への直接遷移は禁止 (必ず手動で `INITIALIZING` を経由)
- `APPLYING_STRATEGY → APPLYING_STRATEGY` の再入は禁止 (排他制御)

---

## 第4章 データフロー図 (DFD) (`04_data_flow.md`)

### 含めるべき内容

#### 4.1 DFDレベル0 (コンテキスト図)
Mermaidで、YoRuuを1つの箱として外部エンティティとのデータ授受を描画。

外部エンティティ:
- Binance (BTC現物価格)
- Polymarket (板情報、注文、約定)
- Chainlink (決済価格、参照のみ)
- ユーザー (Web UI操作、apply入力)
- Opus 4.7 (Genspark経由、人間が仲介)

#### 4.2 DFDレベル1 (主要プロセス)
YoRuu内部を以下のプロセスに分解して描画。

- P1: Price Ingestion
- P2: Market State Estimation (Markov)
- P3: Trading Decision (Kelly)
- P4: Order Execution
- P5: Position Monitoring
- P6: Trade Logging
- P7: Daily Report Generation
- P8: Strategy Apply
- P9: Audit Logging

データストア:
- D1: SQLite (trades, positions, audit_log, etc.)
- D2: strategy.json + strategy_history/
- D3: reports/ ディレクトリ
- D4: logs/ ディレクトリ

#### 4.3 データの寿命表
各データがいつ生まれ、いつ消えるかを表で明示。バックアップ戦略の根拠になる。

| データ | 発生 | 保存先 | 寿命 | バックアップ |
|---|---|---|---|---|
| BTC価格 (5秒足) | リアルタイム | メモリのみ | 直近100本 | なし |
| BTC価格 (5分足) | 5分ごと集計 | SQLite `prices_5min` | 90日 | 日次 |
| 取引ログ | 約定時 | SQLite `trades` | 無期限 | 日次 |
| ポジション | エントリー時 | SQLite `positions` | 決済まで | 日次 |
| 監査ログ | 任意操作時 | SQLite `audit_log` | 無期限・追記専用 | 日次 |
| 日次レポート | 夜間レビュー時 | `reports/YYYY-MM-DD.json` | 無期限 | 週次 |
| strategy.json | apply時 | プロジェクトルート + history/ | 全バージョン保持 | 週次 |
| アプリログ | リアルタイム | `logs/yoruu.log` | 30日でローテーション | 週次 |

#### 4.4 データの変換ポイント
「どこでデータが変換されるか」を明示。例: Binance JSON → 内部 `Price` dataclass、Polymarket Order Response → 内部 `Trade` レコード、等。

---

## 第5章 信頼境界線図 (`05_trust_boundary.md`)

### 含めるべき内容

#### 5.1 信頼ゾーン定義

以下4ゾーンを定義。

- **Zone 0 (最高機密)**: 秘密鍵、APIキー、wallet seed
- **Zone 1 (内部信頼)**: YoRuu Bot プロセス内、メモリ・DB
- **Zone 2 (準信頼)**: ローカルファイルシステム (設定、ログ、レポート)
- **Zone 3 (非信頼)**: 外部API応答 (Polymarket, Binance, Chainlink), Opus 4.7 からの戻り JSON, ユーザー入力

#### 5.2 信頼境界線図
Mermaidで4ゾーンを箱で表現し、ゾーン間のデータ授受に**検証関数**を必ず配置する図を描画。

#### 5.3 境界別の検証ルール表

| 境界 | 入力 | 必須検証 | 違反時の動作 |
|---|---|---|---|
| Zone 3 → Zone 1 (Polymarket応答) | 注文応答 | スキーマ検証、金額の符号、ID整合性 | 例外 → 監査ログ → 再試行 |
| Zone 3 → Zone 1 (Binance応答) | 価格 | 範囲チェック (前値の±5%以内)、タイムスタンプ単調性 | 異常値スキップ + ログ |
| Zone 3 → Zone 1 (Opus JSON) | 新パラメータ | スキーマ検証、範囲チェック、変化率±10%以内 | apply拒否 + UI表示 |
| Zone 3 → Zone 1 (UI入力) | 全項目 | サーバ側でも必ず再検証 | エラーレスポンス |
| Zone 0 アクセス | 秘密鍵読み出し | 呼び出し元関数のホワイトリスト | 例外 + CRITICAL ログ |
| Zone 2 → Zone 1 (strategy.json) | ファイル読込 | スキーマ検証、署名チェック (任意) | 前バージョンへフォールバック |

#### 5.4 機密情報の取り扱いポリシー
- 環境変数 `.env` で管理
- ファイル権限 `chmod 600`、所有者のみ
- ログ・エラーメッセージへの**いかなる形での出力も禁止**
- メモリ上での保持は最小時間、不要になったら明示的に削除
- Git管理対象から完全に除外 (`.gitignore` で `.env`, `*.key`, `*.pem` を必ず除外)

---

## 第6章 シーケンス図 (`06_sequence.md`)

### 含めるべき内容

以下7つのユースケースをそれぞれ Mermaid sequenceDiagram で描画。

#### 6.1 Bot起動シーケンス
登場者: ユーザー, CLI, Config Loader, DB, Strategy Loader, Web Server, Scheduler, Exchange Client

#### 6.2 5分判定 → 注文シーケンス
登場者: Scheduler, Price Aggregator, Markov Estimator, Kelly Sizer, Safety Checker, Order Manager, Polymarket API, DB, Audit Logger

ガード条件 (不変条件チェック) を明示すること。

#### 6.3 約定 → 決済監視 → クローズシーケンス
登場者: Order Manager, Polymarket WS, Position Tracker, Resolution Monitor, DB

#### 6.4 夜間レビュー (レポート生成) シーケンス
登場者: Scheduler, Trade Aggregator, Report Generator, Filesystem, Web UI Notifier

時刻指定設定 (`yoruu.yaml` の `nightly_review.send_time`) からの起動を明示。

#### 6.5 Apply シーケンス (ユーザーがJSON貼り付け)
登場者: ユーザー, Web UI, API Endpoint, Schema Validator, Range Validator, Diff Generator, ユーザー (二重承認), Strategy Writer, Backup Manager, Audit Logger, DB

二重承認のステップを明確に図示。

#### 6.6 モード切替シーケンス (paper → live)
登場者: ユーザー, Web UI, Mode Switcher, Safety Confirmation Dialog, ユーザー (テキスト入力 "LIVE"), Wallet Loader, Balance Checker, DB, Audit Logger

最重要シーケンス。確認ダイアログ表示、テキスト一致確認、残高表示、最終承認の4ステップを必ず描画。

#### 6.7 緊急停止シーケンス
登場者: ユーザー OR Auto-trigger, Emergency Handler, Order Canceller, WS Disconnector, State Persister, UI Notifier, Audit Logger

自動トリガーの場合 (損失上限超過など) も同じシーケンスを通ることを示す。

### 各シーケンスの記述要件
- アクター/コンポーネント間の同期/非同期を区別 (`->>` vs `-->>`)
- エラー分岐は `alt` で表現
- DBへの書き込みポイントを明示
- 各シーケンスの末尾に「想定実行時間」「クリティカルポイント」を1〜2行で添える

---

## 第7章 インプット/アウトプット図 (`07_io_diagram.md`)

### 含めるべき内容

#### 7.1 I/O一覧表
ユーザーが行う**全操作**と、それに対するシステムの**出力**を網羅した表。

| # | 操作 (Input) | 入力元 | 入力データ | 処理概要 | 出力 (Output) | 出力先 | 副作用 |
|---|---|---|---|---|---|---|---|
| 1 | Bot起動 | CLI | `yoruu start` | 設定読込、DB接続、Scheduler開始 | 起動ログ、Web UI起動 | コンソール + ブラウザ | 状態 INITIALIZING → IDLE |
| 2 | ダッシュボード表示 | Web UI | GET / | 現在のステータス取得 | HTML | ブラウザ | なし |
| 3 | 取引ログ表示 | Web UI | GET /trades | DB問い合わせ | テーブルHTML | ブラウザ | なし |
| 4 | 取引ログCSVエクスポート | Web UI | クリックボタン | DBから抽出・整形 | CSVダウンロード | ブラウザ | なし |
| 5 | 夜間レビュー画面表示 | Web UI | GET /review | 当日reports/読込 | プロンプト + ペースト欄 | ブラウザ | なし |
| 6 | プロンプトコピー | Web UI | クリックボタン | クリップボード書き込み | コピー成功表示 | ブラウザ | なし |
| 7 | JSON貼り付け | Web UI | テキストエリア入力 | 即時スキーマ検証 | 検証結果(OK/NG) + 差分表示 | ブラウザ | なし |
| 8 | Apply 承認 (1段階目) | Web UI | クリックボタン | 範囲検証・不変条件 | 差分プレビューモーダル | ブラウザ | なし |
| 9 | Apply 確定 (2段階目) | Web UI | モーダル内ボタン | strategy.jsonバックアップ→上書き | 反映完了表示 + 監査ログ | ブラウザ + DB + FS | strategy.json更新 |
| 10 | 設定変更 | Web UI | フォーム送信 | yoruu.yaml書き換え | 反映完了表示 | ブラウザ + FS | yoruu.yaml更新 |
| 11 | モード切替 (paper → live) | Web UI | クリックボタン | 確認ダイアログ表示 | 警告モーダル | ブラウザ | なし |
| 12 | モード切替 確認 (テキスト) | Web UI | "LIVE"入力 | 文字列一致確認 | 残高表示 + 最終ボタン | ブラウザ | なし |
| 13 | モード切替 最終確定 | Web UI | 最終ボタンクリック | mode変更 + 再初期化 | 完了表示 + UIの赤強調 | ブラウザ + DB | mode変更、監査ログ |
| 14 | 緊急停止 | Web UI | クリックボタン | 全停止処理 | 停止完了表示 | ブラウザ | 全WS切断、全注文キャンセル |
| 15 | 戦略履歴閲覧 | Web UI | GET /strategy-history | history/読込 | 一覧テーブル | ブラウザ | なし |
| 16 | 戦略ロールバック | Web UI | クリックボタン | 過去バージョン復元 | 反映完了表示 | ブラウザ + FS + DB | strategy.json差替 |
| 17 | アラート一覧表示 | Web UI | GET /alerts | DBから ERROR/CRITICAL抽出 | 一覧テーブル | ブラウザ | なし |
| 18 | バックテスト実行 | Web UI | フォーム (期間指定) | 過去データで戦略実行 | 結果サマリ + チャート | ブラウザ | DB追記 |
| 19 | (自動) 5分判定 | Scheduler | 5分境界 | Markov + Kelly判定 | (なし) または 注文 | Polymarket | DB追記 |
| 20 | (自動) 夜間レポート生成 | Scheduler | send_time到達 | 当日ログ集計 | report_YYYY-MM-DD.json | FS | DB読込のみ |
| 21 | (自動) 損失上限到達 | Position Tracker | リアルタイム監視 | 上限判定 | 緊急停止トリガー | Bot内部 | EMERGENCY_STOP |

#### 7.2 入力の検証マトリクス
全UI入力について、検証ルールを表で明示。

| 入力項目 | 型 | 範囲 | 必須 | 検証関数 | エラーメッセージ |
|---|---|---|---|---|---|
| `MIN_PROB` (新値) | float | 0.80 ≤ x ≤ 0.95 | ✓ | `validate_min_prob` | "MIN_PROB は 0.80〜0.95 の範囲" |
| ... | ... | ... | ... | ... | ... |

第5章 5.3 と整合性を保つこと。

#### 7.3 出力データのフォーマット
主要な出力データのスキーマ例 (JSON / CSV ヘッダ) を明示。

- 日次レポート JSON (詳細は第15章で完全定義、ここでは概要のみ)
- 取引ログ CSV ヘッダ
- 戦略履歴 JSON

#### 7.4 ユーザー入力の集約一覧
「ユーザーが直接書き込む箇所」を列挙し、それぞれの**信頼レベル**と**検証回数**を明示。

例:
- yoruu.yaml: ユーザーが直接編集する設定。起動時とファイル変更検知時に検証。
- Apply入力 (JSON): Web UI のテキストエリア。送信時に必ず検証、確定時にも再検証。
- モード切替の "LIVE" 入力: テキスト完全一致のみ許可、大文字小文字区別。

---

## 各章の品質チェックリスト

Opus 4.7 は各章を書き終わったら、以下を自己チェックして章末に `## 品質チェック` セクションを設けて記載すること。

- [ ] 章の冒頭に「この章の目的」を記載した
- [ ] 図はすべて Mermaid または ASCII で描画した
- [ ] 図にキャプションを付けた
- [ ] 他章への参照は `(→ 第X章 X.Y節)` 形式で記載した
- [ ] 用語は第1章 1.6 の用語集と一致している
- [ ] 出力ファイル名が指定通り (例: `03_state_diagram.md`)
- [ ] 章内で矛盾する記述がない
- [ ] 後続章で詳細化される項目は明示的に「(→ 第X章で詳細)」と書いた

---

## 生成順序と相互参照

以下の順で生成すること。各章は前章を参照することがある。

1. `01_overview.md` (用語集が後続章の基礎)
2. `02_architecture.md` (アーキテクチャが後続章の前提)
3. `03_state_diagram.md` (状態定義が4,5,6,7章で参照される)
4. `04_data_flow.md` (データの所在が5,6章で参照される)
5. `05_trust_boundary.md` (境界が6,7章で参照される)
6. `06_sequence.md` (具体的なやり取り)
7. `07_io_diagram.md` (UIのI/O一覧)

各章を生成後、`docs/design/INDEX.md` に章タイトル・ファイル名・1行サマリ・ステータス (DRAFT/REVIEW_PENDING/APPROVED) の一覧を更新すること。

---

## 出力後の確認依頼

7章すべて生成完了後、以下の形式でサマリを提示すること。

```
# 設計書 第1〜7章 生成完了

## 生成ファイル
- docs/design/01_overview.md (XXX行)
- docs/design/02_architecture.md (XXX行)
- ...
- docs/design/INDEX.md (更新)

## 主要な設計判断
- [章番号] 判断内容と理由

## 第8章以降に持ち越した検討事項
- [項目] 持ち越し理由

## 確認をお願いしたいポイント
- [章番号 + 節] 確認内容
```

これにより、ユーザーは効率的にレビューできる。

---

## 注意事項

- **動作するコードは書かないこと**。設計段階のため、構造・インターフェース・データフローのみ示す
- **第8章以降の内容には踏み込まないこと**。例えば UI モックアップHTMLは第8章で作成するため、本指示書範囲では「画面があること」のみ言及して詳細レイアウトには立ち入らない
- **未確定事項は推測で埋めず、明示的に「[要確認]」を残すこと**。後の章で確定する
- **複数の選択肢があるときは推奨案を1つに絞り、他案は脚注に残すこと**
- **Mermaidが複雑になりすぎる場合は、複数の図に分割すること**。1つの図に20ノード以上は避ける

---

以上が第1〜7章の生成指示である。Opus 4.7 はこの指示書に従い、`docs/design/` 以下に7ファイルを生成すること。
