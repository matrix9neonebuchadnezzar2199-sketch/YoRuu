# 第6章 シーケンス図

> この章の目的
> YoRuu の主要ユースケースを時系列の処理フローとして示す。各シーケンスは第3章状態遷移と第5章信頼境界と整合する。

> 注: 本章で示す「想定実行時間」は全て設計段階の概算であり、実測値ではない。実測は本番稼働後に確認する。

## 6.1 Bot 起動シーケンス

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant CLI
    participant CFG as Config Loader
    participant DB
    participant SL as Strategy Loader
    participant WS as Web Server
    participant SCH as Scheduler
    participant EX as Exchange Client
    participant AL as Audit Logger

    U->>CLI: yoruu start
    CLI->>CFG: load yoruu.yaml
    CFG-->>CLI: Config object
    alt 設定検証失敗
        CFG-->>CLI: ValidationError
        CLI-->>U: エラー出力・終了
    end
    CLI->>DB: connect SQLite
    DB-->>CLI: connection
    CLI->>DB: read bot_runtime.last_state
    DB-->>CLI: last_state
    alt last_state == EMERGENCY_STOP
        CLI-->>U: EMERGENCY_STOP からの起動拒否
    end
    CLI->>SL: load strategy.json
    SL-->>CLI: StrategyParams
    alt strategy.json 不正
        SL->>SL: history/ から最新を試行
        SL-->>CLI: StrategyParams (fallback)
    end
    CLI->>EX: connect Polymarket WS
    EX-->>CLI: connected
    CLI->>EX: connect Binance WS
    EX-->>CLI: connected
    CLI->>WS: start Web Server
    WS-->>CLI: listening on 127.0.0.1:8765
    CLI->>SCH: register cron jobs
    SCH-->>CLI: scheduled
    CLI->>AL: log startup
    CLI->>DB: set bot_state = IDLE
    CLI-->>U: 起動完了
```

*図 6-1: Bot 起動シーケンス*

想定実行時間: 数秒程度 (概算、測定前)。
クリティカルポイント: `EMERGENCY_STOP` 状態からの自動起動を禁止する判定。Polymarket / Binance WS 接続失敗時のリトライ戦略 (→ 第18章)。

## 6.2 5分判定 → 注文シーケンス

```mermaid
sequenceDiagram
    participant SCH as Scheduler
    participant PA as Price Aggregator
    participant ME as Markov Estimator
    participant KS as Kelly Sizer
    participant SC as Safety Checker
    participant OM as Order Manager
    participant POLY as Polymarket
    participant DB
    participant AL as Audit Logger

    SCH->>OM: 5分境界イベント
    OM->>OM: state == IDLE 確認
    alt state != IDLE
        OM-->>SCH: スキップ
    end
    OM->>PA: 直近価格データ取得
    PA-->>OM: Price history
    OM->>ME: estimate(prices)
    ME-->>OM: transition_matrix + persistence
    OM->>OM: persistence >= threshold ?
    alt 閾値未達
        OM->>DB: 判定ログ (skip)
        OM-->>SCH: スキップ
    end
    OM->>POLY: 板情報取得
    POLY-->>OM: orderbook
    OM->>OM: edge = p_model - p_market
    alt edge < MIN_EDGE
        OM->>DB: 判定ログ (skip)
        OM-->>SCH: スキップ
    end
    OM->>KS: size(p, b, KELLY_FRACTION, balance)
    KS-->>OM: order_size
    OM->>SC: 不変条件チェック
    SC-->>OM: OK / NG
    alt NG
        OM->>AL: log invariant violation
        OM-->>SCH: スキップ (CRITICAL)
    end
    OM->>OM: state IDLE → TRADING
    OM->>POLY: 注文送信
    alt 注文失敗
        POLY-->>OM: error
        OM->>OM: retry counter++
        alt retries >= 3
            OM->>OM: state → EMERGENCY_STOP
        end
    end
    POLY-->>OM: order_id
    OM->>DB: trade record (open)
    OM->>AL: log order
    OM->>OM: state TRADING → MONITORING_POSITION
    OM-->>SCH: 完了
```

*図 6-2: 5分判定 → 注文シーケンス*

想定実行時間: 1〜3秒程度 (概算、測定前)。
クリティカルポイント: 不変条件チェックは注文送信の直前に必ず実施。連続失敗3回で EMERGENCY_STOP へ。

## 6.3 約定 → 決済監視 → クローズシーケンス

```mermaid
sequenceDiagram
    participant OM as Order Manager
    participant WSC as Polymarket WS
    participant PT as Position Tracker
    participant DB
    participant RM as Resolution Monitor

    OM->>PT: register position
    PT->>WSC: subscribe market_id
    loop 5分間 (決済まで)
        WSC->>PT: price update
        PT->>PT: check stop conditions
        alt 損失上限超過 (本ポジ単独)
            PT->>OM: trigger close
        end
    end
    WSC->>RM: resolution event
    RM->>DB: read position
    DB-->>RM: position
    RM->>RM: determine outcome (WIN/LOSS)
    RM->>DB: update position (closed)
    RM->>DB: update daily_pnl
    alt daily_pnl <= -daily_loss_limit
        RM->>OM: trigger EMERGENCY_STOP
    end
    RM->>OM: position closed
    OM->>OM: state MONITORING_POSITION → IDLE
```

*図 6-3: 約定 → 決済監視 → クローズシーケンス*

想定実行時間: 最大約5分 (市場決済まで)。
クリティカルポイント: 5分市場では事実上のストップロスは難しい (流動性が薄いため)。日次損失上限による全体停止を主たる安全装置とする (→ 第17章)。

## 6.4 夜間レビュー (レポート生成) シーケンス

```mermaid
sequenceDiagram
    participant SCH as Scheduler
    participant RG as Report Generator
    participant DB
    participant FS as Filesystem
    participant WS as Web Server (SSE)
    actor U as ユーザー

    SCH->>RG: send_time イベント
    RG->>RG: state == IDLE 確認
    alt state != IDLE
        RG-->>SCH: 次回再試行
    end
    RG->>RG: state IDLE → GENERATING_REPORT
    RG->>DB: 当日の trades, decisions 取得
    DB-->>RG: records
    RG->>RG: state 別 集計
    RG->>RG: 現行 strategy 読込
    RG->>RG: JSON 整形 + プロンプト埋め込み
    RG->>FS: write reports/YYYY-MM-DD.json
    FS-->>RG: OK
    RG->>RG: state → AWAITING_APPLY
    RG->>WS: SSE: review_available
    WS-->>U: UI 通知 (新しいレポート)
```

*図 6-4: 夜間レビュー (レポート生成) シーケンス*

想定実行時間: 数秒〜数十秒 (概算、測定前、件数依存)。
クリティカルポイント: レポート生成中は新規取引判定を停止する (state ガード)。生成失敗時は次の5分境界で再試行。

## 6.5 Apply シーケンス (ユーザーが JSON 貼り付け)

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant UI as Web UI
    participant AP as API Endpoint
    participant SV as Schema Validator
    participant RV as Range Validator
    participant DG as Diff Generator
    participant SW as Strategy Writer
    participant BM as Backup Manager
    participant AL as Audit Logger
    participant DB
    participant FS as Filesystem

    U->>UI: JSON 貼り付け
    UI->>AP: POST /api/apply/validate
    AP->>SV: schema validate
    alt スキーマ違反
        SV-->>AP: ValidationError
        AP-->>UI: 422 + 詳細
        UI-->>U: エラー表示
    end
    AP->>RV: range check
    alt 範囲外
        RV-->>AP: RangeError
        AP-->>UI: 422 + 詳細
        UI-->>U: エラー表示
    end
    AP->>RV: 変化率 ±10% 以内?
    alt 範囲外
        RV-->>AP: 警告 (拒否 or 強制承認?)
        AP-->>UI: 422 + 詳細
        UI-->>U: 「変化率超過、見直しを」
    end
    AP->>DG: 現行 vs 新の diff
    DG-->>AP: diff
    AP-->>UI: 検証 OK + diff
    UI-->>U: diff プレビュー + 確認ボタン
    U->>UI: 確認ボタンクリック (二重承認)
    UI->>AP: POST /api/apply/confirm
    AP->>AP: state AWAITING_APPLY → APPLYING_STRATEGY
    AP->>BM: backup current strategy.json
    BM->>FS: write strategy_history/YYYY-MM-DD_HHMMSS.json
    FS-->>BM: OK
    AP->>SW: write new strategy.json
    SW->>FS: write strategy.json
    FS-->>SW: OK
    AP->>AL: log strategy change (full diff + reason)
    AL->>DB: insert audit_log
    AP->>AP: state APPLYING_STRATEGY → IDLE
    AP-->>UI: 反映完了
    UI-->>U: 完了表示
```

*図 6-5: Apply シーケンス*

想定実行時間: ユーザー入力待ちを除き 1秒以下 (概算、測定前)。
クリティカルポイント: 二重承認 (検証→ diff 表示→確認) を必ず通過させる。バックアップは strategy.json 書き換えの**前**に必ず行う。

## 6.6 モード切替シーケンス (paper → live)

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant UI as Web UI
    participant AP as API Endpoint
    participant CD as Confirm Dialog
    participant WL as Wallet Loader
    participant BC as Balance Checker
    participant AL as Audit Logger
    participant DB

    U->>UI: モード切替画面
    UI-->>U: 現在モード表示 (paper)
    U->>UI: 「live に切替」ボタン
    UI->>CD: 警告モーダル表示
    CD-->>U: テキスト入力欄 ("LIVE" と入力してください)
    U->>CD: "LIVE" 入力
    CD->>CD: 文字列完全一致確認
    alt 不一致
        CD-->>U: 拒否、再入力
    end
    CD->>WL: load wallet
    WL-->>CD: wallet ready
    CD->>BC: check balance
    BC-->>CD: balance (USDC)
    CD-->>U: 残高表示 + 「理解した」チェックボックス + 最終確定ボタン
    U->>CD: チェック ON + 最終ボタン
    CD->>AP: POST /api/mode/switch (target=live)
    AP->>AP: 現在状態 == IDLE 確認
    alt state != IDLE
        AP-->>UI: 拒否 (取引中)
        UI-->>U: 拒否表示
    end
    AP->>DB: update mode = live
    AP->>AL: log mode change
    AP->>AP: 再初期化 (取引パスの切替)
    AP-->>UI: 切替完了
    UI-->>U: 完了表示 (UI 全体が赤強調になる)
```

*図 6-6: モード切替シーケンス*

想定実行時間: ユーザー入力待ちを除き 1秒以下 (概算、測定前)。
クリティカルポイント: テキスト一致確認 + 残高表示 + 最終承認の3段階。state が IDLE 以外なら拒否。

## 6.7 緊急停止シーケンス

```mermaid
sequenceDiagram
    actor U as ユーザー
    participant T as 自動トリガー
    participant EH as Emergency Handler
    participant OC as Order Canceller
    participant WD as WS Disconnector
    participant SP as State Persister
    participant WS as Web Server
    participant AL as Audit Logger
    participant DB

    alt 手動
        U->>WS: POST /api/emergency_stop
        WS->>EH: trigger
    else 自動
        T->>EH: trigger (daily_loss / 連続失敗 / etc.)
    end
    EH->>EH: 即座に state → EMERGENCY_STOP
    EH->>OC: cancel all open orders
    OC->>OC: 全注文に cancel リクエスト
    Note over OC: 失敗してもログのみ、続行
    EH->>WD: disconnect all WS
    WD-->>EH: disconnected
    EH->>SP: persist state to DB
    SP->>DB: update bot_state
    EH->>AL: log emergency stop (trigger source)
    AL->>DB: insert audit_log
    EH->>WS: SSE: emergency_stop
    WS-->>U: UI 最大強調表示
```

*図 6-7: 緊急停止シーケンス*

想定実行時間: 1秒以下 (概算、測定前)。
クリティカルポイント: 注文キャンセル失敗でも処理は続行する (停止優先)。自動・手動のいずれのトリガーでも同じシーケンスを通る。

## 6.8 シーケンス間の共通規約

- 全シーケンスで監査ログへの書き込みポイントを明示する
- DB への書き込みは順序が重要 (バックアップ → 上書き → 監査ログ)
- 外部 API への呼び出し前に必ず Zone 1 内での検証を完了する
- 状態遷移は第3章定義の遷移のみを使用する

## 品質チェック

- [x] 章の冒頭に「この章の目的」を記載した
- [x] 図はすべて Mermaid sequenceDiagram で描画した
- [x] 図にキャプションを付けた
- [x] 他章への参照は `(→ 第X章)` 形式で記載した
- [x] 用語は第1章 1.6 の用語集と一致している
- [x] 出力ファイル名: `06_sequence.md`
- [x] 章内で矛盾する記述がない
- [x] 後続章で詳細化される項目は明示的に「(→ 第X章で詳細)」と書いた
- [x] 想定実行時間は全て「概算、測定前」を明記した
- [x] エラー分岐は `alt` で表現した
- [x] DB への書き込みポイントを明示した