# 第7章 インプット/アウトプット図

## この章の目的

ユーザー操作および自動トリガーに対する入力・処理・出力・副作用を一覧化する。第8章 UI モックアップの画面マッピングの基準とする。

---

## 7.1 I/O 一覧表

| # | 操作 (Input) | 入力元 | 入力データ | 処理概要 | 出力 (Output) | 出力先 | 副作用 |
|:---:|:---|:---|:---|:---|:---|:---|:---|
| 1 | Bot起動 | CLI | `yoruu start` | 設定読込、DB接続、Scheduler開始 | 起動ログ、Web UI URL | コンソール + ブラウザ | `INITIALIZING → IDLE` |
| 2 | ダッシュボード表示 | Web UI | `GET /` | ステータス集計 | HTML | ブラウザ | なし |
| 3 | 取引ログ表示 | Web UI | `GET /trades` | DB 問合せ | テーブル HTML | ブラウザ | なし |
| 4 | 取引ログ CSV | Web UI | エクスポートボタン | DB 抽出 | CSV ダウンロード | ブラウザ | なし |
| 5 | 夜間レビュー画面 | Web UI | `GET /review` | 当日 `reports/` 読込 | プロンプト + ペースト欄 | ブラウザ | なし |
| 6 | プロンプトコピー | Web UI | コピーボタン | クリップボード書込 | 成功トースト | ブラウザ | なし |
| 7 | JSON 貼り付け | Web UI | テキストエリア | 即時スキーマ検証 | OK/NG + 差分 | ブラウザ | なし |
| 8 | Apply 承認(1) | Web UI | ボタン | 範囲・不変条件 | 差分モーダル | ブラウザ | なし |
| 9 | Apply 確定(2) | Web UI | モーダル確定 | backup → 上書き | 完了 + 監査 | ブラウザ+DB+FS | `strategy.json` 更新 |
| 10 | 設定変更 | Web UI | フォーム POST | `yoruu.yaml` 更新 | 完了表示 | FS | 設定更新 |
| 11 | モード切替開始 | Web UI | paper→live ボタン | 警告モーダル | 警告 UI | ブラウザ | なし |
| 12 | モード確認入力 | Web UI | `"LIVE"` | 完全一致検証 | 残高 + 最終ボタン | ブラウザ | なし |
| 13 | モード最終確定 | Web UI | 最終ボタン | mode 変更 | 赤 UI バー | ブラウザ+DB | 監査ログ |
| 14 | 緊急停止 | Web UI | キルボタン | 全停止 | 停止完了 | ブラウザ | `EMERGENCY_STOP` |
| 15 | 戦略履歴 | Web UI | `GET /strategy-history` | history 読込 | 一覧表 | ブラウザ | なし |
| 16 | 戦略ロールバック | Web UI | ボタン | 過去版復元 | 完了 | FS+DB | strategy 差替 |
| 17 | アラート一覧 | Web UI | `GET /alerts` | ERROR/CRITICAL 抽出 | 一覧表 | ブラウザ | なし |
| 18 | バックテスト | Web UI | 期間フォーム | 過去データ実行 | サマリ | ブラウザ | DB 追記 |
| 19 | (自動) 5分判定 | Scheduler | 5分境界 | Markov+Kelly | 注文 or なし | Polymarket | DB 追記 |
| 20 | (自動) 夜間レポート | Scheduler | send_time | 集計 | `report_*.json` | FS | `GENERATING_REPORT` |
| 21 | (自動) 損失上限 | Position Tracker | 残高監視 | 上限判定 | 緊急停止 | 内部 | `EMERGENCY_STOP` |

### 第8章モックアップへのマッピング

| モックファイル | 対応 I/O # |
|:---|:---|
| `01_dashboard.html` | 2, 19, 21 |
| `02_trade_log.html` | 3, 4 |
| `03_nightly_review.html` | 5, 6, 7, 8, 9 |
| `04_settings.html` | 10 |
| `05_strategy_history.html` | 15, 16 |
| `06_alerts.html` | 17 |
| `07_mode_switch.html` | 11, 12, 13 |
| `08_emergency_stop.html` | 14 |

(→ 第8章で詳細)

---

## 7.2 入力の検証マトリクス

第5章 5.3 と整合。

| 入力項目 | 型 | 範囲 | 必須 | 検証関数 | エラーメッセージ |
|:---|:---|:---|:---:|:---|:---|
| `MIN_PROB` | float | 0.80 ≤ x ≤ 0.95 | ✓ | `validate_min_prob` | MIN_PROB は 0.80〜0.95 |
| `MIN_EDGE` | float | 0.01 ≤ x ≤ 0.20 | ✓ | `validate_min_edge` | MIN_EDGE は 0.01〜0.20 |
| `KELLY_FRACTION` | float | 0 &lt; x ≤ 0.8 | ✓ | `validate_kelly_fraction` | KELLY_FRACTION は 0〜0.8 |
| `persistence_threshold` | float | 0.50 ≤ x ≤ 0.90 | ✓ | `validate_persistence` | persistence_threshold 範囲外 |
| apply JSON 全体 | object | スキーマ + Δ≤10% | ✓ | `validate_strategy_apply` | 戦略パラメータが無効 |
| モード切替 `"LIVE"` | string | 完全一致 | ✓ | `validate_live_token` | LIVE と入力してください |
| `daily_loss_limit` 上方修正 | float | &gt; 現在値 | ✓ | `validate_loss_limit_increase` | リスク増加の確認が必要 |
| バックテスト開始日 | date | 過去 ≤ 終了 | ✓ | `validate_backtest_range` | 期間が不正 |

---

## 7.3 出力データのフォーマット

### 日次レポート JSON（概要のみ）

| トップレベルキー | 用途 |
|:---|:---|
| `date` | 対象日 (YYYY-MM-DD) |
| `summary` | 損益・勝率・取引回数の集計 |
| `trades` | 当日取引の参照 ID リスト |
| `strategy_snapshot` | 適用中パラメータのスナップショット |
| `prompt` | Opus 4.7 向け分析指示文（コピー用） |
| `meta` | 生成時刻・Bot バージョン |

完全スキーマは (→ 第15章で詳細)。

### 取引ログ CSV ヘッダ

```text
trade_id,market_id,side,entry_price,exit_price,size_usd,pnl_usd,mode,opened_at_utc,closed_at_utc
```

### 戦略履歴 JSON（概要）

| キー | 用途 |
|:---|:---|
| `version` | 連番またはタイムスタンプ ID |
| `applied_at` | apply 確定時刻 UTC |
| `params` | パラメータスナップショット |
| `source` | `opus_review` / `rollback` / `manual` |
| `diff_from_previous` | 変更フィールド一覧 |

---

## 7.4 ユーザー入力の集約一覧

| 書き込み箇所 | 信頼レベル | 検証回数 | タイミング |
|:---|:---|:---:|:---|
| `yoruu.yaml` | Zone 2 | 2 | 起動時 + ファイル変更検知時 |
| Apply テキストエリア | Zone 3 | 2 | preview + confirm |
| モード `"LIVE"` 入力 | Zone 3 | 1 | 送信時（完全一致） |
| `strategy.json` 直接編集 | Zone 2（非推奨） | 1 | 次回起動時。Web UI 経由を推奨 |

---

## 品質チェック

- [x] I/O 21項目網羅
- [x] 第8章モックマッピング表
- [x] 7.3 は概要のみ（第15章へ委譲）
- [x] 第5章 5.3 と検証関数一致
- [x] `07_io_diagram.md`
