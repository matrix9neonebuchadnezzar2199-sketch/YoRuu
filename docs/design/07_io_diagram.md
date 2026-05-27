# 第7章 インプット/アウトプット図

> この章の目的
> ユーザーが行う全ての操作と、それに対するシステムの出力の対応関係を網羅する。第8章 UI モックアップの作成根拠となる。

## 7.1 I/O 一覧表

ユーザー操作およびシステム自動動作と、その出力・副作用を一覧化する。

| # | 操作 / トリガー | 入力元 | 入力データ | 処理概要 | 出力 | 出力先 | 副作用 |
|---|---|---|---|---|---|---|---|
| 1 | Bot 起動 | CLI | `yoruu start` | 設定読込、DB接続、Scheduler開始 | 起動ログ、Web UI 起動 | コンソール + Web | state INITIALIZING → IDLE |
| 2 | Bot 停止 | CLI / Web UI | `yoruu stop` または停止ボタン | 安全停止手順 (→ 第2章 2.5.5) | 停止ログ | コンソール + Web | state → SHUTDOWN |
| 3 | ダッシュボード表示 | Web UI | GET / | 現在のステータス取得 | HTML | ブラウザ | なし |
| 4 | 取引ログ表示 | Web UI | GET /trades | DB問い合わせ | テーブル HTML | ブラウザ | なし |
| 5 | 取引ログ CSV エクスポート | Web UI | クリックボタン | DB から抽出・整形 | CSV ダウンロード | ブラウザ | なし |
| 6 | 取引ログ JSON エクスポート | Web UI | クリックボタン | DB から抽出・整形 | JSON ダウンロード | ブラウザ | なし |
| 7 | 取引フィルタ | Web UI | GET /trades?from=...&to=... | DB問い合わせ | テーブル更新 | ブラウザ | なし |
| 8 | 夜間レビュー画面表示 | Web UI | GET /review | 当日 reports/ 読込 | プロンプト + ペースト欄 | ブラウザ | なし |
| 9 | プロンプトコピー | Web UI | クリックボタン | クリップボード書き込み | コピー成功表示 | ブラウザ | なし |
| 10 | レポートファイルダウンロード | Web UI | クリックボタン | reports/YYYY-MM-DD.json 配信 | JSON ダウンロード | ブラウザ | なし |
| 11 | JSON 貼り付け | Web UI | テキストエリア入力 | 即時スキーマ検証 | 検証結果 (OK/NG) + 差分表示 | ブラウザ | なし |
| 12 | Apply 承認 (1段階目) | Web UI | クリックボタン | 範囲検証 + 不変条件 | 差分プレビューモーダル | ブラウザ | なし (state は変化しない) |
| 13 | Apply 確定 (2段階目) | Web UI | モーダル内ボタン | バックアップ → strategy.json 上書き | 反映完了表示 + 監査ログ | ブラウザ + DB + FS | strategy.json 更新、state APPLYING → IDLE |
| 14 | Apply スキップ | Web UI | ボタン | 当日のレビューを破棄 | スキップ確認 | ブラウザ | state AWAITING_APPLY → IDLE |
| 15 | 設定変更 | Web UI | フォーム送信 | yoruu.yaml 書き換え | 反映完了表示 | ブラウザ + FS | yoruu.yaml 更新 |
| 16 | モード切替 (paper → live) | Web UI | クリックボタン | 確認ダイアログ表示 | 警告モーダル | ブラウザ | なし (まだ切替えない) |
| 17 | モード切替 確認 (テキスト) | Web UI | "LIVE" 入力 | 文字列一致確認 | 残高表示 + 最終ボタン | ブラウザ | なし |
| 18 | モード切替 最終確定 | Web UI | 最終ボタンクリック | mode 変更 + 再初期化 | 完了表示 + UI 赤強調 | ブラウザ + DB | mode 変更、監査ログ |
| 19 | 緊急停止 | Web UI | クリックボタン | 全停止処理 | 停止完了表示 | ブラウザ | 全 WS 切断、全注文キャンセル、state → EMERGENCY_STOP |
| 20 | 戦略履歴閲覧 | Web UI | GET /strategy-history | history/ 読込 | 一覧テーブル | ブラウザ | なし |
| 21 | 戦略ロールバック | Web UI | クリックボタン (二重承認あり) | 過去バージョン復元 | 反映完了表示 | ブラウザ + FS + DB | strategy.json 差替、監査ログ |
| 22 | アラート一覧表示 | Web UI | GET /alerts | DB から ERROR/CRITICAL 抽出 | 一覧テーブル | ブラウザ | なし |
| 23 | アラート詳細表示 | Web UI | GET /alerts/{id} | 1件の詳細取得 | 詳細 HTML | ブラウザ | なし |
| 24 | バックテスト実行 | Web UI | フォーム (期間指定) | 過去データで戦略実行 | 結果サマリ + チャート | ブラウザ | DB 追記 (mode=backtest 区分) |
| 25 | リアルタイムステータス | Web UI | SSE 接続 | ステータス更新 push | ステータスイベント | ブラウザ | なし |
| 26 | (自動) 5分判定 | Scheduler | 5分境界 | Markov + Kelly 判定 | (なし) または 注文 | Polymarket | DB 追記、state IDLE → TRADING |
| 27 | (自動) 夜間レポート生成 | Scheduler | send_time 到達 | 当日ログ集計 | report_YYYY-MM-DD.json | FS | DB 読込のみ、state IDLE → GENERATING_REPORT → AWAITING_APPLY |
| 28 | (自動) 損失上限到達 | Position Tracker | リアルタイム監視 | 上限判定 | 緊急停止トリガー | Bot 内部 | state → EMERGENCY_STOP |
| 29 | (自動) 連続失敗3回 | Order Manager | 注文失敗カウント | 自動緊急停止 | 緊急停止トリガー | Bot 内部 | state → EMERGENCY_STOP |
| 30 | (自動) 価格 WS 切断検知 | Price Aggregator | WS heartbeat | 自動再接続 | 接続復帰または WARN | ブラウザ + ログ | なし (継続) |

## 7.2 入力検証マトリクス

第5章 5.3 と整合する形で、UI からの入力に対する検証ルールを明示する。

| 入力項目 | 型 | 範囲 | 必須 | 検証関数 | エラーメッセージ |
|---|---|---|---|---|---|
| Apply JSON: `MIN_PROB` | float | 0.80 ≤ x ≤ 0.95 | ✓ | `validate_min_prob` | "MIN_PROB は 0.80〜0.95 の範囲" |
| Apply JSON: `MIN_EDGE` | float | 0.01 ≤ x ≤ 0.20 | ✓ | `validate_min_edge` | "MIN_EDGE は 0.01〜0.20 の範囲" |
| Apply JSON: `KELLY_FRACTION` | float | 0 < x ≤ 0.80 | ✓ | `validate_kelly_fraction` | "KELLY_FRACTION は 0〜0.80 の範囲" |
| Apply JSON: `PERSISTENCE_THRESHOLD` | float | 0.80 ≤ x ≤ 0.95 | ✓ | `validate_persistence_threshold` | "PERSISTENCE_THRESHOLD は 0.80〜0.95 の範囲" |
| Apply JSON: `reason` | string | 1〜500文字 | ✓ | `validate_reason` | "理由は1〜500文字で必須" |
| Apply: 変化率 | float | 各パラメータ ±10% 以内 | ✓ | `validate_change_rate` | "前回値からの変化が10%を超えています" |
| 設定 `mode` | enum | {backtest, paper, simmer, live} | ✓ | `validate_mode` | "無効なモード" |
| 設定 `nightly_review.send_time` | string | "HH:MM" 形式 | ✓ | `validate_time_format` | "HH:MM 形式で入力" |
| 設定 `nightly_review.timezone` | string | IANA TZ 名 | ✓ | `validate_timezone` | "有効なタイムゾーン名" |
| 設定 `max_trade_size_usd` | float | 0 < x ≤ 1000 | ✓ | `validate_max_trade` | "0より大きく1000以下" |
| 設定 `daily_loss_limit_usd` | float | 0 < x | ✓ | `validate_loss_limit` | "0より大きい値" |
| モード切替確認 | string | "LIVE" と完全一致 (大文字小文字区別) | ✓ | `validate_live_text` | "LIVE と入力してください" |
| バックテスト期間 from | date | 過去90日以内 | ✓ | `validate_backtest_from` | "過去90日以内" |
| バックテスト期間 to | date | from 以降、未来不可 | ✓ | `validate_backtest_to` | "from 以降、未来不可" |

サーバ側 (FastAPI Pydantic) で必ず再検証する。クライアント検証は UX のための即時フィードバックに留め、信頼しない。

## 7.3 出力データのフォーマット

主要な出力データのスキーマ概要を示す。詳細スキーマは第15章 (夜間レビューフロー) で完全定義する。

### 7.3.1 日次レポート (概要)

ファイル: `data/reports/YYYY-MM-DD.json`

概要:
- 当日の取引サマリ (件数、勝率、損益)
- Markov 状態別の成績
- 個別取引のリスト
- 現行 strategy パラメータ
- Opus 4.7 への指示プロンプト (固定テンプレート)

完全な JSON スキーマは → 第15章で詳細定義する。本章ではフィールド列挙のみに留める。

### 7.3.2 取引ログ CSV ヘッダ

```
trade_id,decision_id,timestamp_utc,market_id,side,size_usd,price,outcome,pnl_usd,state_at_entry,mode
```

### 7.3.3 戦略履歴 JSON (概要)

ファイル: `data/strategy_history/YYYY-MM-DD_HHMMSS.json`

概要:
- 適用前のパラメータ全体
- 適用したパラメータ全体
- diff
- 理由 (reason)
- 適用時刻 (UTC)
- 監査ログ ID

完全スキーマは → 第15章および第20章で詳細定義。

## 7.4 ユーザー入力の集約一覧

ユーザーが直接書き込む箇所と、その信頼レベル・検証回数を明示する。

| 入力箇所 | 入力経路 | 信頼ゾーン | 検証回数 | 検証タイミング |
|---|---|---|---|---|
| `yoruu.yaml` | エディタで直接編集 | Zone 2 | 2回 | 起動時 + ファイル変更検知時 |
| `.env` | エディタで直接編集 | Zone 0 | 1回 | 起動時のみ (権限チェック含む) |
| Apply 入力 JSON | Web UI テキストエリア | Zone 3 | 2回 | 送信時 + 確定時 |
| 設定変更フォーム | Web UI フォーム | Zone 3 | 2回 | 送信時 + 適用時 |
| モード切替 "LIVE" | Web UI テキスト入力 | Zone 3 | 1回 (厳密一致) | 入力即時 |
| バックテスト期間 | Web UI 日付ピッカー | Zone 3 | 1回 | 実行時 |
| 緊急停止操作 | Web UI ボタン | Zone 3 | 0回 (確認なし、即実行) | — |
| 戦略ロールバック | Web UI ボタン | Zone 3 | 1回 (確認モーダル) | クリック時 |

緊急停止が「検証なし即実行」なのは、緊急時に余計な手順を強要しないためである。誤って押しても、再起動で復帰できる (state → EMERGENCY_STOP → 手動再起動 → INITIALIZING → IDLE)。

## 7.5 SSE (Server-Sent Events) で配信するイベント

Web UI へのリアルタイム通知に SSE を使用する。配信するイベントの一覧。

| イベント名 | 発生条件 | ペイロード概要 |
|---|---|---|
| `state_change` | bot_state 変更時 | `{from, to, timestamp}` |
| `trade_opened` | 新規ポジション | `{trade_id, market_id, side, size, price}` |
| `trade_closed` | ポジション決済 | `{trade_id, outcome, pnl}` |
| `daily_pnl` | 損益更新時 | `{pnl_today, balance}` |
| `review_available` | レポート生成完了 | `{date, file_path}` |
| `error` | ERROR ログ発生 | `{error_code, message, severity}` |
| `critical` | CRITICAL ログ発生 | `{error_code, message}` |
| `mode_change` | モード変更時 | `{from, to}` |
| `ws_status` | 外部 WS 接続状態変化 | `{service, status}` |

SSE 接続が切れた場合は Web UI 側で自動再接続を行う。

## 7.6 第8章 UI モックアップ作成への引き継ぎ

第7章の I/O 一覧 (7.1) に基づき、第8章で以下の画面を作成する。

| # | 画面名 | 対応する I/O 番号 |
|---|---|---|
| 1 | ダッシュボード | 3, 25 |
| 2 | 取引ログ画面 | 4, 5, 6, 7 |
| 3 | 夜間レビュー画面 | 8, 9, 10, 11, 12, 13, 14 |
| 4 | 設定画面 | 15 |
| 5 | 戦略履歴画面 | 20, 21 |
| 6 | アラート画面 | 22, 23 |
| 7 | モード切替画面 | 16, 17, 18 |
| 8 | 緊急停止 (ダッシュボード組込) | 19 |
| 9 | バックテスト画面 | 24 |

各画面の詳細ワイヤーフレームと動作は第8章および第9章で確定する。

## 品質チェック

- [x] 章の冒頭に「この章の目的」を記載した
- [x] 図は表形式で I/O 関係を網羅した
- [x] 図にキャプションを付けた (表は番号付け)
- [x] 他章への参照は `(→ 第X章)` 形式で記載した
- [x] 用語は第1章 1.6 の用語集と一致している
- [x] 出力ファイル名: `07_io_diagram.md`
- [x] 章内で矛盾する記述がない
- [x] 後続章で詳細化される項目は明示的に「(→ 第X章で詳細)」と書いた
- [x] 7.3 は概要のみとし、完全 JSON スキーマは第15章に持ち越した
- [x] 入力検証マトリクスは第5章と整合している