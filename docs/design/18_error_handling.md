# 第18章 エラーハンドリング + ログトリアージ

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
- **関連章**: 10（API 応答形式）, 14（i18n `error.*`）, 15（`E_NIGHTLY_*` 意味論）, 17（リスクマトリクス）

## 18.1 目的・スコープ

### 18.1.1 目的

YoRuu 全体の**エラーコード体系**、**HTTP ステータスマッピング**、**ログレベルとトリアージ手順**を SSOT として確定する。第15章の `E_NIGHTLY_*` 候補を**正式コードとして採用**し、第14章 `error.*` 翻訳キーと 1:1 対応させる。

### 18.1.2 命名規則

| 要素 | 規則 |
|------|------|
| コード | `E_<DOMAIN>_<NNN>` — DOMAIN は大文字、NNN は 3 桁ゼロ埋め |
| i18n キー | `error.e_<domain>_<nnn>` — 小文字・ドット区切り（第14章 §14.10.8） |
| severity | `INFO` \| `WARN` \| `ERROR` \| `CRITICAL`（ch10 §10.2） |

### 18.1.3 API 応答形式（再掲）

```json
{
  "error": {
    "code": "E_FILL_001",
    "message": "Insufficient liquidity in order book",
    "details": { "required_usd": 10.0, "available_usd": 3.2 }
  }
}
```

`message` は英語（開発用）。UI は `code` から i18n を解決する。

## 18.2 ドメイン一覧

| ドメイン | 範囲 | 主な発生源 |
|----------|------|------------|
| `STATE` | 001〜019 | 状態機械・起動整合性 |
| `MODE` | 001〜019 | モード切替（ch12） |
| `FILL` | 001〜019 | 約定（ch13） |
| `NIGHTLY` | 001〜019 | 夜間レビュー（ch15） |
| `DB` | 001〜009 | SQLite |
| `SETTINGS` | 001〜019 | 設定 API |
| `LIVE` | 001〜019 | Polymarket CLOB（ch24） |
| `AUTH` | 001〜009 | API キー・署名 |
| `WS` | 001〜009 | WebSocket |

## 18.3 エラーコードカタログ（SSOT）

### 18.3.1 `E_STATE_*`

| コード | severity | HTTP | 説明 | ユーザーアクション |
|--------|----------|------|------|------------------|
| `E_STATE_001` | ERROR | 409 | 現在状態では操作不可 | 待機または状態確認 |
| `E_STATE_002` | CRITICAL | 503 | strategy.json と DB version 不一致（起動拒否） | ch20 §20.6 復旧 |
| `E_STATE_003` | CRITICAL | 503 | Apply 部分失敗の残骸検出 | 手動整合または rollback |

### 18.3.2 `E_MODE_*`

| コード | severity | HTTP | 説明 |
|--------|----------|------|------|
| `E_MODE_001` | WARN | 409 | LIVE 切替の 2 段階確認未完了 |
| `E_MODE_002` | WARN | 409 | 夜間レビュー中・非 IDLE でのモード切替拒否 |
| `E_MODE_003` | ERROR | 409 | `EMERGENCY_STOP` から LIVE への直接切替拒否（ch12 §12.5.3） |
| `E_MODE_004` | WARN | 409 | USDC 残高不足で LIVE 不可 |
| `E_MODE_005` | ERROR | 500 | モード切替中の内部エラー |

### 18.3.3 `E_FILL_*`

| コード | severity | HTTP | 説明 | リトライ |
|--------|----------|------|------|----------|
| `E_FILL_001` | WARN | 200* | 流動性不足（FillResult） | 次サイクル |
| `E_FILL_002` | WARN | 200* | スプレッド > 0.05 | 次サイクル |
| `E_FILL_003` | WARN | 200* | 価格 > 0.99 | なし |
| `E_FILL_004` | WARN | 200* | 価格 < 0.01 | なし |
| `E_FILL_005` | ERROR | 200* | オーダーブック取得失敗 | 最大 3 回 |
| `E_FILL_010` | ERROR | 200* | ポジション不在 | なし |

\* 取引 API は HTTP 200 + `FillResult.success=false` で返す（ch13 §13.6.3）。

### 18.3.4 `E_NIGHTLY_*`（ch15 候補を正式採用）

| コード | severity | HTTP | 説明 |
|--------|----------|------|------|
| `E_NIGHTLY_001` | WARN | — | スケジュール時 `state != IDLE`、再試行失敗 |
| `E_NIGHTLY_002` | ERROR | — | DB 集計失敗 |
| `E_NIGHTLY_003` | CRITICAL | — | `daily_reports` INSERT 失敗 |
| `E_NIGHTLY_004` | ERROR | — | summary_json 生成例外 |
| `E_NIGHTLY_005` | WARN | 422 | 提案 JSON に `constraints` 禁止キー |
| `E_NIGHTLY_006` | WARN | 422 | 提案 JSON に yoruu.yaml 系キー |
| `E_NIGHTLY_007` | WARN | 422 | パラメータ範囲外 |
| `E_NIGHTLY_008` | WARN | 422 | 変化率 ±20% 超 |
| `E_NIGHTLY_009` | WARN | 422 | 必須キー欠落 |
| `E_NIGHTLY_010` | ERROR | 500 | Apply: strategy_versions INSERT 失敗 |
| `E_NIGHTLY_011` | ERROR | 500 | Apply: バックアップ失敗 |
| `E_NIGHTLY_012` | ERROR | 500 | Apply: audit_log INSERT 失敗 |
| `E_NIGHTLY_013` | WARN | 409 | 並行 Apply |
| `E_NIGHTLY_014` | WARN | 409 | rollback 不可（状態・期限） |

### 18.3.5 `E_DB_*`

| コード | severity | HTTP | 説明 |
|--------|----------|------|------|
| `E_DB_001` | CRITICAL | 500 | クリティカルパス書込失敗 |
| `E_DB_002` | ERROR | 500 | 読込失敗 |
| `E_DB_003` | CRITICAL | 503 | DB ファイル不存在・破損 |

`E_NIGHTLY_003` は内部で `E_DB_001` をラップしてもよい（ログには両方記録可）。

### 18.3.6 `E_SETTINGS_*`

| コード | severity | HTTP | 説明 |
|--------|----------|------|------|
| `E_SETTINGS_001` | WARN | 422 | スキーマ検証失敗 |
| `E_SETTINGS_002` | WARN | 409 | 再起動必須キー変更中の競合操作 |
| `E_SETTINGS_003` | ERROR | 500 | 設定ファイル書込失敗 |

詳細マトリクスは第21章。

### 18.3.7 `E_LIVE_*`（概要、詳細は第24章）

| コード | severity | 説明 |
|--------|----------|------|
| `E_LIVE_001` | WARN | 流動性不足（API 応答） |
| `E_LIVE_002` | ERROR | 注文タイムアウト |
| `E_LIVE_003` | ERROR | 残高不足 |
| `E_LIVE_004` | ERROR | EIP-712 署名失敗 |
| `E_LIVE_005` | CRITICAL | API レート制限超過 |

### 18.3.8 `E_AUTH_*` / `E_WS_*`

| コード | severity | 説明 |
|--------|----------|------|
| `E_AUTH_001` | CRITICAL | Polymarket API キー無効 |
| `E_WS_001` | WARN | WebSocket 切断（再接続中） |
| `E_WS_002` | ERROR | 再接続上限超過 |

## 18.4 ログトリアージ

### 18.4.1 ログファイル構成

| ファイル | 内容 | ローテーション |
|----------|------|----------------|
| `logs/yoruu.log` | 構造化 JSON 行 | 日次、7 日保持 |
| `logs/trades.log` | 約定専用（オプション） | 日次 |
| `logs/audit.log` | 監査（DB と二重化しない、デバッグ用のみ） | 永続圧縮 |

### 18.4.2 ログレベルと出力

| レベル | 用途 | 例 |
|--------|------|-----|
| DEBUG | 開発のみ | オーダーブックスナップショット |
| INFO | 正常業務 | 状態遷移、約定成功 |
| WARN | 回復可能 | `E_FILL_001`、リトライ |
| ERROR | 要対応 | `E_NIGHTLY_002` |
| CRITICAL | 即時停止 | `E_AUTH_001`、`E_DB_003` |

### 18.4.3 トリアージ手順（運用）

```
1. UI アラートタブで severity >= ERROR を確認
2. logs/yoruu.log を時刻で grep: "code":"E_*
3. コード → 本章 §18.3 で意味確認 → 第17章リスク ID へマッピング
4. CRITICAL かつ EMERGENCY_STOP でない → 手動キル検討（第19章）
5. 事後: audit_log（第20章）と突合
```

### 18.4.4 秘密情報のマスキング

ログに出力してはならない: API 秘密鍵、EIP-712 署名生データ、SSH 鍵パス（ch5 §5.2）。`details_json` は ID と数値のみ。

## 18.5 i18n 連携（第14章）

| コード | i18n キー（ja） |
|--------|-----------------|
| `E_FILL_001` | `error.e_fill_001` |
| `E_MODE_001` | `error.e_mode_001` |
| … | 全コードで `error.e_<domain>_<nnn>` |

PHASE 3 実装時: `src/yoruu/ui/locales/ja.json` に §18.3 全件を追加。`en.json` は v1.0 で空オブジェクト可（ch14）。

## 18.6 章間相互参照表

| 本章節 | 参照先 | 内容 |
|--------|--------|------|
| §18.3.3 | ch13 §13.8 | Fill 失敗 |
| §18.3.4 | ch15 §15.10 | Nightly 意味論 |
| §18.3.2 | ch12 §12.5.2 | モード 409 |
| §18.4 | ch5 §5.2 | 秘密マスク |
| §18.5 | ch14 §14.10.8 | error.* |

## 18.7 品質チェック

### 18.7.1 章末チェックリスト

- [x] ch15 候補コードを正式採用（番号維持）
- [x] ch13 E_FILL_001〜010 掲載
- [x] HTTP と FillResult の使い分け明記
- [x] i18n キー規則と一致

### 18.7.2 レビュー判定（7項目）

| # | 観点 | 判定 |
|---|------|------|
| 1 | ch15 意味論維持 | ✅ |
| 2 | ch14 i18n 規則 | ✅ |
| 3 | ch10 API 形式 | ✅ |
| 4 | ch13 Fill 系列 | ✅ |
| 5 | ch12 MODE 系列 | ✅ |
| 6 | ログトリアージ手順 | ✅ |
| 7 | ch24 LIVE 伏線 | ✅ |

---

**出力ファイル名**: `18_error_handling.md`
