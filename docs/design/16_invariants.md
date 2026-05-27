# 第16章 不変条件

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
- **関連章**: 3（状態）, 10（データモデル）, 11（戦略）, 15（Apply）, 17（リスク）, 19（キル）

## 16.1 目的・スコープ

### 16.1.1 目的

実行時に**常に真**でなければならない条件（不変条件）を列挙し、違反時の検知・応答を SSOT 化する。`InvariantChecker` の実装と PHASE 5 テストの根拠とする。

### 16.1.2 分類

| 種別 | 検査タイミング | 違反時 |
|------|----------------|--------|
| **起動時** | `INITIALIZING` | 起動拒否 or `EMERGENCY_STOP` |
| **遷移時** | 状態変更直前 | 遷移拒否 |
| **取引時** | `TRADING` / Fill 前後 | スキップ or 停止 |
| **継続的** | 各 5 分境界 | WARN or 停止 |

## 16.2 状態機械不変条件（INV-S）

| ID | 条件 | 検査 |
|----|------|------|
| INV-S-01 | 任意時刻で bot はちょうど 1 状態 | 排他ロック |
| INV-S-02 | `EMERGENCY_STOP` 中は新規 `TRADING` 不可 | ガード |
| INV-S-03 | `SHUTDOWN` は終端（遷移なし） | — |
| INV-S-04 | `APPLYING_STRATEGY` 中はモード切替不可 | ch12 §12.5.2 |
| INV-S-05 | BACKTEST 実行中は ch3 状態機械未使用 | ch12 §12.2.1 |

## 16.3 データ不変条件（INV-D）

| ID | 条件 |
|----|------|
| INV-D-01 | `open_positions` の `mode` は現在 `bot_state.mode` と一致 |
| INV-D-02 | `trades.pnl` の日次合計と `daily_pnl` キャッシュの差 < $0.01 |
| INV-D-03 | `strategy.json.version` == `bot_state.current_strategy_version`（起動時、ch20 §20.6） |
| INV-D-04 | `audit_log` に成功した `STRATEGY_APPLY` がある場合、対応する `strategy_versions` 行が存在 |
| INV-D-05 | LIVE モードの `trades` は `executor=live` のみ |

## 16.4 戦略・リスク不変条件（INV-R）

| ID | 条件 |
|----|------|
| INV-R-01 | エントリー時 `size_usd <= risk.max_trade_size_usd` |
| INV-R-02 | エントリー時 `daily_loss < daily_loss_limit`（厳密: 等号で停止、ch17 R-FIN-01） |
| INV-R-03 | `MIN_PROB`, `MIN_EDGE`, `KELLY_FRACTION`, `PERSISTENCE_THRESHOLD` は `constraints` 内 |
| INV-R-04 | Kelly 由来サイズが負でない |
| INV-R-05 | 同一 5 分境界で二重エントリーなし |

## 16.5 モード不変条件（INV-M）

| ID | 条件 |
|----|------|
| INV-M-01 | LIVE かつ `EMERGENCY_STOP` 履歴 24h 以内 → LIVE 切替 API 拒否（ch19） |
| INV-M-02 | PAPER 再起動で残高リセット（SIMMER は INV-M-03 例外） |
| INV-M-03 | SIMMER 残高はセッション跨ぎで単調減少のみ許可（リセット操作は明示 API のみ） |

## 16.6 違反時応答

```
InvariantViolation(inv_id, severity):
  if severity == CRITICAL:
      trigger EMERGENCY_STOP (AUTO_INVARIANT)
      audit_log INVARIANT_VIOLATION
  elif severity == ERROR:
      block transition / reject API
  else:
      WARN alert only
```

| inv_id | 既定 severity |
|--------|---------------|
| INV-S-02 違反試行 | ERROR |
| INV-D-03 | CRITICAL |
| INV-R-02 境界 | CRITICAL（超過後） |
| INV-R-05 | ERROR |

## 16.7 テストへのマッピング

第23章 §23.4: 各 `INV-*` に対し最低 1 つのユニットまたは統合テストを要求。

## 16.8 章間相互参照表

| 本章節 | 参照先 | 内容 |
|--------|--------|------|
| INV-D-03 | ch20 §20.6 | 起動検査 |
| INV-R-* | ch11, ch17 | 戦略・リスク |
| INV-M-* | ch12 | モード |
| 違反応答 | ch19 §19.2 | AUTO_INVARIANT |

## 16.9 品質チェック

### 16.9.2 レビュー判定（7項目）

| # | 観点 | 判定 |
|---|------|------|
| 1 | ch3 状態 | ✅ |
| 2 | ch10 データ | ✅ |
| 3 | ch11 戦略 | ✅ |
| 4 | ch12 モード | ✅ |
| 5 | ch15 Apply | ✅ |
| 6 | ch19 キル | ✅ |
| 7 | ch23 テスト | ✅ |

---

**出力ファイル名**: `16_invariants.md`
