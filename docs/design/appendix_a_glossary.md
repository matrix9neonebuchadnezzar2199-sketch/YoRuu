# 付録 A 用語集

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
- **由来**: 第1章 §1.6 から SSOT を分離（中間レビュー案 Y）

> 設計書全体の用語定義 SSOT。第1章 §1.6 は要約参照。

| 用語 | 英 | 定義 |
|---|---|---|
| Markov連鎖 | Markov chain | 直近状態のみから次状態の確率を推定する確率モデル |
| 持続状態 | persistent state | 上昇または下降が連続している状態 |
| Persistence | persistence | Markov 推定の遷移確率（例: p(UP→UP)）。分析・表示用 |
| Kelly基準 | Kelly criterion | f* = p - (1-p)/b で最適賭け金比率を求める公式 |
| エッジ | edge | モデル推定確率 p とマーケット価格 q の差 (p - q) |
| CLOB | Central Limit Order Book | 中央集権型指値注文板。Polymarket の取引方式 |
| EIP-712 | EIP-712 | Ethereum の構造化データ署名規格。Polymarket 注文に必須 |
| ペーパーモード | paper mode | 実取引せず、リアルタイム市場で仮想約定するモード |
| SIMMER | simmer mode | PAPER と同エンジンで長期連続検証するモード（ch12） |
| backtest モード | backtest mode | 過去データで戦略を高速再生するモード |
| live モード | live mode | 実資金を投入する本番モード |
| persistence_threshold | persistence threshold | 直近 N 本の同方向継続割合の最小値（エントリー許可）。`MIN_PROB` とは別尺度 (→ 第11章) |
| MIN_PROB | MIN_PROB | エントリー方向の最小モデル確率（Kelly 入力の p） |
| MIN_EDGE | MIN_EDGE | エントリーを許可する最小エッジ |
| KELLY_FRACTION | KELLY_FRACTION | Kelly 基準の数値を実際にどれだけ使うかの係数 (0〜1) |
| 不変条件 | invariant | 常に成立しなければならない条件（→ 第16章 INV-*） |
| キル・スイッチ | kill switch | 緊急停止機構（→ 第19章） |
| 二重承認 | two-step confirmation | 危険操作で2段階の確認を要求する仕組み |
| 戦略パラメータ | strategy parameters | strategy.json で管理される動的パラメータ群 |
| 夜間レビュー | nightly review | 1日1回の戦略パラメータ見直しプロセス |
| Apply | apply | 新戦略パラメータを strategy.json に書き込む操作 |
| 監査ログ | audit log | 全変更を追記専用で記録するログ（→ 第20章） |
| Zone | zone | 信頼境界線で区切られた領域 (Zone 0〜3) |
| FillResult | fill result | 約定成功/失敗とエラーコードを返す DTO（ch13） |
| wait_reason | wait reason | エントリーを見送った理由の列挙（ch10/ch11） |
| RiskGuard | risk guard | 日次損失・連続失敗等を監視するコンポーネント |
| LiveExecutor | live executor | LIVE 実約定を担当する実行器（ch13/ch24） |
| PaperExecutor | paper executor | PAPER/SIMMER 仮想約定（ch13） |
| summary_json | summary json | 夜間レポートの集約 JSON（ch15 §15.4） |
| confirm_token | confirm token | 2 段階確認用の短期 UUID（ch19） |
| エラーコード | error code | `E_<DOMAIN>_<NNN>` 形式（ch18 SSOT） |

## 品質チェック

- [x] ch1 §1.6 の用語を包含
- [x] M1.5 新規用語（監査・不変条件・CLOB）を追加
- [x] 出力ファイル名: `appendix_a_glossary.md`
