# 第19章 キルスイッチ + 2段階確認

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
- **関連章**: 3（`EMERGENCY_STOP`）, 6（§6.7 シーケンス）, 9（§9.8 UI フロー）, 10（`emergency_stops`）, 12（復帰制約）, 17（R-STR-04, R-FIN-01）

## 19.1 目的・スコープ

### 19.1.1 目的

**緊急停止（キルスイッチ）**のトリガー、実行手順、データ記録、**復帰**、および**危険操作の 2 段階確認**を SSOT として確定する。

### 19.1.2 スコープ（含む）

- 自動トリガー（§19.2）
- 手動トリガー（§19.3）
- UI / API / CLI（§19.4）
- 復帰フロー（§19.5）
- 2 段階確認の対象操作（§19.6）

### 19.1.3 スコープ外

- モック HTML の見た目（→ ch8 §8.19、PHASE 2 実装済）
- Polymarket 側の注文キャンセル API 詳細（→ 第24章）

## 19.2 自動トリガー

| トリガ ID | 条件 | ソース | 状態遷移 |
|-----------|------|--------|----------|
| `AUTO_LOSS_LIMIT` | `daily_pnl <= -daily_loss_limit_usd` | RiskGuard | → `EMERGENCY_STOP` |
| `AUTO_CONSECUTIVE_FAIL` | 15 分以内 Fill 失敗 ≥ 3 | FillExecutor | → `EMERGENCY_STOP` |
| `AUTO_AUTH_FAIL` | `E_AUTH_001` | PolymarketClient | → `EMERGENCY_STOP` |
| `AUTO_INVARIANT` | 不変条件違反（ch16） | InvariantChecker | → `EMERGENCY_STOP` |
| `AUTO_INIT_FAIL` | 起動時致命的エラー | Bootstrap | → `EMERGENCY_STOP` または終了 |

自動トリガー時も `emergency_stops` レコードと `audit_log` を必ず書く（§19.4.4）。

## 19.3 手動トリガー

| 経路 | 2 段階 | 備考 |
|------|--------|------|
| UI 緊急停止画面（§8.19） | **あり**（確認モーダル） | ch9 §9.8 |
| `POST /api/v1/emergency/stop` | **あり**（`confirm_token`） | ch10 §10.6.6 |
| CLI `yoruu emergency-stop` | **あり**（`--confirm`） | 本番運用 |
| キーボードショートカット | **なし**（v1.0 無効） | v1.1 検討、誤操作防止 |

手動トリガの `trigger_source` は `USER`。

## 19.4 実行シーケンス

### 19.4.1 処理順序（固定）

```
1. 新規エントリー禁止フラグを即時 SET（メモリ）
2. オープンポジション: close(reason=EMERGENCY_STOP) を順次実行
   - PAPER/SIMMER: PaperExecutor 成行クローズ（ch13 §13.7.2）
   - LIVE: LiveExecutor + ch24 キャンセル/成行
3. WebSocket: 取引判定ループ停止（接続は維持可、v1.0）
4. bot_state.state = EMERGENCY_STOP（DB）
5. emergency_stops INSERT（ch10 §10.3.11）
6. audit_log INSERT（action=EMERGENCY_STOP）
7. SSE: emergency_stop_triggered
8. アラート CRITICAL
```

### 19.4.2 API

```http
POST /api/v1/emergency/stop
Content-Type: application/json

{
  "confirm_token": "<uuid-from-step1>",
  "reason": "manual_user_request"
}
```

Step 1: `POST /api/v1/emergency/stop/prepare` → `{ "confirm_token": "...", "expires_in_sec": 120 }`

### 19.4.3 `emergency_stops` 記録

| フィールド | 値例 |
|------------|------|
| `trigger_source` | `USER` \| `SYSTEM` \| `RISK_GUARD` |
| `trigger_detail` | `AUTO_LOSS_LIMIT` 等 |
| `open_positions_closed` | クローズ試行数 |
| `daily_pnl_at_stop` | 停止時点 PnL |

### 19.4.4 監査

`audit_log`: `actor=USER|SYSTEM`, `action=EMERGENCY_STOP`, `resource=bot`, `result=SUCCESS|PARTIAL`（一部ポジション未クローズ時 PARTIAL）。

## 19.5 復帰フロー

### 19.5.1 原則

- `EMERGENCY_STOP` から **直接 LIVE には遷移不可**（ch12 §12.5.3）
- 復帰は `EMERGENCY_STOP` → `INITIALIZING` → `IDLE` のみ（ch3 §3.2）
- 復帰後の推奨モード: **PAPER**（UI 文言、API 強制なし）

### 19.5.2 API

```http
POST /api/v1/emergency/recover
{
  "target_mode": "PAPER",
  "confirm": true
}
```

- `target_mode=LIVE` は **409 `E_MODE_003`**（停止直後 24 時間は UI でもグレーアウト推奨）
- 成功時: `emergency_stops.recovered_at`, `recovered_to_mode` 更新

### 19.5.3 ログアーカイブ

ch9 §9.8.7: 停止時に `logs/` を zip 化し `log_archive_path` にパス記録（オプション、`--no-archive` でスキップ可）。

## 19.6 2 段階確認（キル以外）

| 操作 | 第1段階 | 第2段階 | エラー |
|------|---------|---------|--------|
| LIVE モード切替 | チェックリスト 7 項目 | `confirm_live=true` | `E_MODE_001` |
| 緊急停止 | Prepare token | `confirm_token` | — |
| strategy Apply（±10%超） | 警告ダイアログ | チェックボックス | ch15 |
| strategy Apply（±20%超） | — | **拒否**（v1.0） | `E_NIGHTLY_008` |
| 設定: `daily_loss_limit` 引き上げ | 警告 | テキスト入力「CONFIRM」 | `E_SETTINGS_*` |

## 19.7 章間相互参照表

| 本章節 | 参照先 | 内容 |
|--------|--------|------|
| §19.2 | ch17 §17.3 | リスク自動応答 |
| §19.4 | ch6 §6.7 | シーケンス図 |
| §19.4 | ch10 §10.3.11 | emergency_stops |
| §19.5 | ch12 §12.5.3 | LIVE 復帰禁止 |
| §19.6 | ch15 §15.7.4 | Apply 閾値 |

## 19.8 品質チェック

### 19.8.1 章末チェックリスト

- [x] 自動・手動トリガー一覧
- [x] prepare/confirm API パターン
- [x] 復帰と LIVE 制約
- [x] ch3 状態遷移と一致

### 19.8.2 レビュー判定（7項目）

| # | 観点 | 判定 |
|---|------|------|
| 1 | ch3 EMERGENCY_STOP | ✅ |
| 2 | ch6 §6.7 | ✅ |
| 3 | ch9 §9.8 | ✅ |
| 4 | ch12 復帰制約 | ✅ |
| 5 | ch10 API | ✅ |
| 6 | PHASE 2 モック §8.19 | ✅ |
| 7 | ch16 不変条件連携 | ✅ |

---

**出力ファイル名**: `19_kill_switch.md`
