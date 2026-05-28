# 第16章 不変条件

- **バージョン**: v1.0.3
- **作成日**: 2026-05-27
- **ローリング更新**: 2026-05-28（v1.0.3: INV-D-06 v2、INV-D-07/08/09 追加、InvariantChecker 22 件）
- **v1.0.3 追補アーカイブ**: [`archive/principal-rollout-2026-05-28/ch16_v1.0.3_ROLLING_DRAFT.md`](./archive/principal-rollout-2026-05-28/ch16_v1.0.3_ROLLING_DRAFT.md)
- **承認日**: 2026-05-27
- **ステータス**: APPROVED（ローリング更新、再レビュー不要）
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
| INV-D-06 | **残高保存則 v2**: `balance + Σ(open.size_usd) ≈ principal + Σ(closed.pnl)`（**0.02 USD**） |
| INV-D-07 | **principal 保存則**: `principal == Σ(DEPOSIT) − Σ(WITHDRAW)`（**0.01 USD**） |
| INV-D-08 | **withdraw 制約**: 全 WITHDRAW で `amount <= balance_before` |
| INV-D-09 | **非負性**: `principal >= 0` かつ `balance >= 0` |

### 16.3.1 INV-D-06（残高保存則 v2）— v1.0.3 改訂

**適用**: PAPER / SIMMER。H-1: `balance` = 自由資金、`locked_principal` = `Σ(open.size_usd)`（派生列なし）。

**一次形式**: `total_assets ≈ principal + Σ(closed.pnl)`  
**展開形式**: `balance + Σ(open.size_usd) ≈ principal + Σ(closed.pnl)`

v1 後方互換: 入出金履歴が空、またはマイグレーション直後は `principal == initial_balance` 相当で v1 と等価。

**更新規則（ch13 §13.2.5 D11 v2）**: open/close は v1 維持。DEPOSIT/WITHDRAW で `balance`/`principal` 同額加減。

**検査**: `check_post_open` / `check_post_close` / `check_post_principal_change`（新規、M4.4）。severity: **ERROR**。

### 16.3.2 INV-D-07（principal 保存則）

`bot_state.principal` と `principal_transactions` の整合。許容誤差 **0.01 USD**。DEPOSIT/WITHDRAW 直後・5 分境界・起動時。severity: **ERROR**。

### 16.3.3 INV-D-08（withdraw 制約）

全 WITHDRAW で `amount <= balance_before`（= `withdrawable_principal`）。事前 `E_PRINCIPAL_001`、事後不変条件として ERROR。

### 16.3.4 INV-D-09（非負性）

`principal >= 0` かつ `balance >= 0`。5 分境界・資金操作直後。severity: **ERROR**。

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
| INV-D-02 | ERROR |
| INV-D-03 | CRITICAL |
| INV-D-06 | ERROR |
| INV-D-07 | ERROR |
| INV-D-08 | ERROR |
| INV-D-09 | ERROR |
| INV-R-02 境界 | CRITICAL（超過後） |
| INV-R-05 | ERROR |

## 16.7 テストへのマッピング

第23章 §23.4: 各 `INV-*` に対し最低 1 つのユニットまたは統合テストを要求。v1.0.3: `InvariantChecker` **19 → 22 件**（M4.4 で INV-D-06 v2 / 07 / 08 / 09 テスト追加）。

## 16.8 章間相互参照表

| 本章節 | 参照先 | 内容 |
|--------|--------|------|
| INV-D-03 | ch20 §20.6 | 起動検査 |
| INV-D-06 v2 | ch13 §13.2.5 D11 v2 | open/close/deposit/withdraw 後 |
| INV-D-07 | ch10 §10.3.14 / ch13 §13.2.6 | principal_transactions |
| INV-D-08 | ch13 §13.2.6 / ch18 E_PRINCIPAL_001 | withdraw |
| INV-D-09 | ch13 §13.2.5 / §13.2.6 | 非負性 |
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
