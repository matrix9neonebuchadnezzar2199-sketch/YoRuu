# 第20章 監査ログ

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
- **関連章**: 10（`audit_log` テーブル）, 15（Apply 書込）, 19（緊急停止）, 16（不変条件の検証）

## 20.1 目的・スコープ

### 20.1.1 目的

**誰が・いつ・何を・結果如何**を改ざん困難な形で記録する監査ログの SSOT を定義する。コンプライアンス・事後調査・起動時整合性チェックの根拠とする。

### 20.1.2 スコープ（含む）

- 記録対象イベント（§20.2）
- スキーマと `details_json` 規約（§20.3）
- 書込 API / トランザクション境界（§20.4）
- 照会・エクスポート（§20.5）
- 起動時整合性検査（§20.6）

### 20.1.3 スコープ外

- ファイルログのローテーション（→ 第18章 §18.4）
- ブロックチェーン等の外部不変ストア（v1.0 対象外）

## 20.2 記録対象イベント

| action | actor 例 | resource | 必須 |
|--------|----------|----------|------|
| `MODE_SWITCH` | USER | `bot` | ✓ |
| `STRATEGY_APPLY` | USER, NIGHTLY_REVIEW | `strategy` | ✓ |
| `STRATEGY_ROLLBACK` | USER | `strategy` | ✓ |
| `SETTINGS_CHANGE` | USER | `config` | ✓ |
| `EMERGENCY_STOP` | USER, SYSTEM | `bot` | ✓ |
| `EMERGENCY_RECOVER` | USER | `bot` | ✓ |
| `POSITION_CLOSE_MANUAL` | USER | `position` | ✓ |
| `NIGHTLY_REPORT_GENERATED` | SCHEDULER | `report` | ✓ |
| `INVARIANT_VIOLATION` | SYSTEM | `bot` | ✓ |

`result`: `SUCCESS` \| `FAILURE` \| `PARTIAL`（緊急停止で一部ポジション未クローズ時）。

## 20.3 スキーマ（ch10 §10.3.12 拡張）

### 20.3.1 テーブル（再掲）

ch10 の DDL を SSOT とする。追加制約:

- `ts` は UTC ISO8601（`TEXT`）
- `details_json` は最大 8 KB（超過時は要約 + `truncated: true`）

### 20.3.2 `details_json` 必須フィールド

| action | 必須キー |
|--------|----------|
| `STRATEGY_APPLY` | `previous_version`, `new_version`, `diff` |
| `MODE_SWITCH` | `from_mode`, `to_mode` |
| `SETTINGS_CHANGE` | `keys_changed[]`（値はマスク可） |
| `EMERGENCY_STOP` | `trigger_source`, `trigger_detail` |

秘密情報（API キー全文）は **禁止**。

## 20.4 書込規則

### 20.4.1 トランザクション

| 操作 | audit_log と本体 |
|------|------------------|
| Apply（ch15 §15.8） | **同一トランザクション** — audit 失敗なら全体 ROLLBACK |
| モード切替 | 状態更新成功後に audit（失敗時は WARN ログ、状態は確定済のため PARTIAL 記録を試行） |
| 緊急停止 | 停止処理の最終段階で必須 |

### 20.4.2 `AuditLogger` インターフェース

```python
class AuditLogger:
    def log(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        resource_id: str | None = None,
        details: dict | None = None,
        result: str,
    ) -> None: ...
```

## 20.5 照会・エクスポート

### 20.5.1 API

```http
GET /api/v1/audit?from=2026-05-01&to=2026-05-27&action=STRATEGY_APPLY&limit=100
```

- 既定ソート: `ts DESC`
- UI 戦略履歴画面（ch8 §8.16）と同一データソース

### 20.5.2 エクスポート

```http
GET /api/v1/audit/export?format=csv
```

- Zone 2（ch5）: ローカルホストのみ
- ファイル名: `audit_export_YYYYMMDD.csv`

## 20.6 起動時整合性検査

```
起動時:
1. bot_state.current_strategy_version を読む
2. strategy.json の version と比較
3. 不一致 → E_STATE_002、起動拒否
4. strategy_versions 最新行と diff 照合（オプション厳格モード）
5. 前回 EMERGENCY_STOP 未復帰 → 状態を EMERGENCY_STOP で再開（ch19）
```

Apply 部分失敗（DB committed / file not written）の検出は **手順 2-4** でカバー（`E_STATE_003`）。

## 20.7 章間相互参照表

| 本章節 | 参照先 | 内容 |
|--------|--------|------|
| §20.3 | ch10 §10.3.12 | DDL |
| §20.4 | ch15 §15.8.6 | Apply TX |
| §20.6 | ch18 E_STATE_* | 起動エラー |
| §20.2 | ch19 §19.4 | 緊急停止 |

## 20.8 品質チェック

### 20.8.2 レビュー判定（7項目）

| # | 観点 | 判定 |
|---|------|------|
| 1 | ch10 スキーマ | ✅ |
| 2 | ch15 Apply TX | ✅ |
| 3 | ch19 緊急停止 | ✅ |
| 4 | ch18 E_STATE | ✅ |
| 5 | ch5 Zone | ✅ |
| 6 | 秘密マスク | ✅ |
| 7 | ch16 検証連携 | ✅ |

---

**出力ファイル名**: `20_audit_log.md`
