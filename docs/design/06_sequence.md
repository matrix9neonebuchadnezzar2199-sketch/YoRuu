# 第6章 シーケンス図

## この章の目的

主要ユースケース7種の時系列相互作用を sequenceDiagram で定義する。第3章の状態遷移・第5章の信頼境界と整合し、実装時の非同期境界と DB 書き込みポイントを明示する。

**想定実行時間の記述ルール**: 本章の数値はすべて **測定前**。修飾語 `概算` / `目安` / `未測定` を付与する。根拠のない具体ミリ秒は記載しない。

---

## 6.1 Bot 起動シーケンス

```mermaid
sequenceDiagram
    autonumber
    actor U as ユーザー
    participant CLI as CLI
    participant CFG as Config Loader
    participant DB as DB
    participant STR as Strategy Loader
    participant WEB as Web Server
    participant SCH as Scheduler
    participant EX as Exchange Client

    U->>CLI: yoruu start
    CLI->>CFG: load yoruu.yaml
    CFG->>CFG: pydantic 検証 (Zone 2)
    CFG-->>CLI: YoRuuConfig
    CLI->>DB: connect + migrate
    DB-->>CLI: OK
    CLI->>STR: load strategy.json
    STR->>STR: validate_strategy (Zone 2)
    STR-->>CLI: StrategyParams
  par 並列起動
    CLI->>WEB: uvicorn start
    CLI->>SCH: register jobs
    CLI->>EX: init clients (no trade yet)
  end
    CLI-->>U: 起動ログ + URL
    Note over CLI,DB: 状態 INITIALIZING → IDLE
```

**図 6-1: Bot 起動**

- **想定実行時間（測定前）**: 概算 5〜15秒（DB サイズ・マイグレーション有無に依存）`[要確認: 実測後に更新]`
- **クリティカルポイント**: `strategy.json` 検証失敗時は起動中止（`EMERGENCY_STOP` ではなく起動エラー終了）

---

## 6.2 5分判定 → 注文シーケンス

```mermaid
sequenceDiagram
    autonumber
    participant SCH as Scheduler
    participant PA as Price Aggregator
    participant MK as Markov Estimator
    participant KL as Kelly Sizer
    participant SF as Safety Checker
    participant OM as Order Manager
    participant PM as Polymarket API
    participant DB as DB
    participant AUD as Audit Logger

    SCH->>PA: on_5m_boundary()
    PA->>MK: estimate_transition()
    MK-->>KL: persistence, p_up
    KL->>KL: compute size (Kelly)
    KL->>SF: check invariants
    alt 不変条件 NG
        SF-->>SCH: skip trade
        SF->>AUD: log WARN
    else 不変条件 OK
        SF->>OM: submit signal
        OM->>PM: create_order (async)
        PM-->>OM: response
        OM->>OM: validate_polymarket_response (Zone 3)
        OM->>DB: INSERT orders
        OM->>AUD: log INFO
        Note over SCH,DB: IDLE → TRADING → IDLE/MONITORING_POSITION
    end
```

**図 6-2: 5分判定 → 注文**

- **想定実行時間（測定前）**: 目安 2〜8秒（ネットワーク・板深度に依存）。Polymarket CLOB の p99 レイテンシ公式値は `[要確認: 公式ドキュメント参照]`
- **クリティカルポイント**: `Safety Checker` が `MIN_PROB`, `MIN_EDGE`, `KELLY_FRACTION`, `daily_loss` を検証 (→ 第16章)

---

## 6.3 約定 → 決済監視 → クローズ

```mermaid
sequenceDiagram
    autonumber
    participant OM as Order Manager
    participant WS as Polymarket WS
    participant PT as Position Tracker
    participant RM as Resolution Monitor
    participant PM as Polymarket API
    participant DB as DB

    OM->>WS: subscribe fills
    WS-->>PT: fill event
    PT->>DB: UPDATE positions
    Note over PT: MONITORING_POSITION
    loop until resolved
        RM->>PM: poll market status
        RM->>RM: validate response (Zone 3)
    end
    RM->>PT: resolution complete
    PT->>DB: CLOSE position + INSERT trades
    Note over PT: → IDLE
```

**図 6-3: 約定 → 決済監視 → クローズ**

- **想定実行時間（測定前）**: 未測定（市場 Resolution 時刻は外部依存、最大5分市場サイクル）
- **クリティカルポイント**: 同一 `market_id` の未決済ポジションは1件まで (不変条件)

---

## 6.4 夜間レビュー（レポート生成）

```mermaid
sequenceDiagram
    autonumber
    participant SCH as Scheduler
    participant TA as Trade Aggregator
    participant RG as Report Generator
    participant FS as Filesystem
    participant UI as Web UI Notifier

    SCH->>SCH: nightly_review.send_time 到達
    Note over SCH: IDLE → GENERATING_REPORT
    SCH->>TA: aggregate today()
    TA->>DB: SELECT trades, positions
    TA-->>RG: stats + prompt context
    RG->>FS: write report_YYYY-MM-DD.json
    RG->>UI: SSE notify report_ready
    Note over SCH: → AWAITING_APPLY
```

**図 6-4: 夜間レポート生成**

- **想定実行時間（測定前）**: 概算 1〜30秒（当日取引件数に比例）
- **クリティカルポイント**: レポートには分析用プロンプトを同梱 (→ 第15章)。本章では生成フローのみ

---

## 6.5 Apply（JSON 貼り付け・二重承認）

```mermaid
sequenceDiagram
    autonumber
    actor U as ユーザー
    participant WEB as Web UI
    participant API as API Endpoint
    participant SV as Schema Validator
    participant RV as Range Validator
    participant DF as Diff Generator
    participant BW as Backup Manager
    participant SW as Strategy Writer
    participant AUD as Audit Logger
    participant DB as DB

    U->>WEB: paste JSON
    WEB->>API: POST /api/apply/preview
    API->>SV: validate (Zone 3)
    API->>RV: range + delta 10%
    alt 検証 NG
        API-->>WEB: 400 + errors
    else 検証 OK
        API->>DF: build diff
        API-->>WEB: diff modal
        U->>WEB: 承認 (1段階目)
        U->>WEB: 確定 (2段階目)
        WEB->>API: POST /api/apply/confirm
        Note over API: AWAITING_APPLY → APPLYING_STRATEGY
        API->>BW: backup strategy.json
        API->>SW: write strategy.json
        API->>AUD: audit_log append
        API->>DB: record apply metadata
        API-->>WEB: success
        Note over API: → IDLE
    end
```

**図 6-5: Apply 二重承認**

- **想定実行時間（測定前）**: 概算 &lt; 1秒（ローカル検証・ファイル I/O のみ）
- **クリティカルポイント**: Zone 3 Opus JSON は **2回** 検証（preview + confirm）

---

## 6.6 モード切替（paper → live）

```mermaid
sequenceDiagram
    autonumber
    actor U as ユーザー
    participant WEB as Web UI
    participant MS as Mode Switcher
    participant DLG as Safety Dialog
    participant WL as Wallet Loader
    participant BC as Balance Checker
    participant DB as DB
    participant AUD as Audit Logger

    U->>WEB: click ライブモードへ
    WEB->>DLG: show warning modal
    U->>DLG: type "LIVE"
    alt 文字列不一致
        DLG-->>WEB: reject
    else 一致
        DLG->>WL: load wallet (Zone 0)
        WL->>BC: fetch balance
        BC-->>DLG: display balance
        U->>DLG: final confirm + checkbox
        DLG->>MS: set mode=live
        MS->>DB: persist mode
        MS->>AUD: CRITICAL audit
        MS-->>WEB: enable red UI bar
    end
```

**図 6-6: paper → live（4ステップ）**

1. 警告モーダル表示  
2. `"LIVE"` 手入力（大文字小文字区別）  
3. 残高表示  
4. 最終確認チェック + 確定  

- **想定実行時間（測定前）**: 人間操作時間に依存（システム処理は概算 &lt; 3秒）
- **クリティカルポイント**: 秘密鍵読込は Zone 0 ホワイトリスト経由のみ

---

## 6.7 緊急停止

```mermaid
sequenceDiagram
    autonumber
    actor U as ユーザー
    participant TR as Auto-trigger
    participant EH as Emergency Handler
    participant OC as Order Canceller
    participant WD as WS Disconnector
    participant SP as State Persister
    participant UI as UI Notifier
    participant AUD as Audit Logger

    alt ユーザー
        U->>EH: kill switch
    else 自動
        TR->>EH: daily_loss / 3 failures
    end
    EH->>OC: cancel all open
    EH->>WD: disconnect all WS
    EH->>SP: state=EMERGENCY_STOP
    EH->>UI: max alert
    EH->>AUD: CRITICAL log
```

**図 6-7: 緊急停止（手動・自動共通経路）**

- **想定実行時間（測定前）**: 目安 1〜5秒（未約定キャンセル数に依存）`[要確認: 実測後に更新]`
- **クリティカルポイント**: 全状態から `EMERGENCY_STOP` へ遷移可能 (→ 第3章 3.2節)

---

## 品質チェック

- [x] 7シーケンスすべて Mermaid sequenceDiagram
- [x] 各図にキャプション・実行時間（測定前修飾）・クリティカルポイント
- [x] 状態名は第3章と同一（INITIALIZING, IDLE, TRADING, …）
- [x] DB 書き込みポイント明示（6.2, 6.3, 6.5, 6.6）
- [x] Zone 3 検証を alt/注釈で明示
- [x] 第8章以降の詳細スキーマには踏み込まない
- [x] `06_sequence.md`
