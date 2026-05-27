# 第24章 Polymarket CLOB クライアント詳細

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
- **関連章**: 13（LiveExecutor 対比）, 18（`E_LIVE_*`）, 22（`polymarket.*` 設定）

## 24.1 目的

LIVE モードで使用する **Polymarket CLOB REST / WebSocket クライアント**の契約・署名・注文ライフサイクル・リトライを SSOT 化する。ch13 §13.6 の「詳細は第24章」を充足する。

## 24.2 アーキテクチャ

```
LiveExecutor
    └── PolymarketClient
            ├── ClobRestClient   (注文・キャンセル・残高)
            ├── ClobWsClient     (約定・板更新)
            └── Signer (EIP-712)
```

- **Zone 3**（ch5）: 外部 Polymarket のみ。秘密鍵はプロセス外秘匿（環境変数）。

## 24.3 認証

| 項目 | 値 |
|------|-----|
| 署名規格 | EIP-712（ch22 `signature_type`） |
| チェーン | Polygon `chain_id: 137` |
| API キー | HTTP ヘッダ `POLY_*`（公式 SDK 準拠、実装時ドキュメント参照） |

認証失敗 → `E_AUTH_001` → `EMERGENCY_STOP`（ch19）。

## 24.4 注文タイプ（v1.0）

| 操作 | タイプ | 用途 |
|------|--------|------|
| エントリー | LIMIT GTC | 戦略サイズ・価格で買い |
| 緊急クローズ | MARKET / aggressive LIMIT | `EMERGENCY_STOP` |
| キャンセル | DELETE order | 停止処理 |

## 24.5 注文ライフサイクル

```
create_order → accepted → matched | partial | rejected
                ↓
            cancel (optional)
```

| 状態 | DB `trades.status` |
|------|-------------------|
| accepted | `pending` |
| matched | `filled` |
| rejected | `failed` |

## 24.6 リトライ戦略（ch13 §13.6.3 確定）

| 失敗種別 | リトライ | コード |
|----------|----------|--------|
| 流動性不足 | 1 回（500ms 後） | `E_LIVE_001` |
| タイムアウト | 2 回（指数バックオフ） | `E_LIVE_002` |
| 残高不足 | 0 | `E_LIVE_003` |
| レート制限 | 0、CRITICAL | `E_LIVE_005` |
| 署名失敗 | 0 | `E_LIVE_004` |

## 24.7 WebSocket

- 購読: マーケットチャンネル（`market.id` に対応する token ID）
- 再接続: ch22 `websocket.max_reconnect_attempts`
- 30s 無更新 → `E_WS_001`、取引スキップ

## 24.8 `PolymarketClient` インターフェース

```python
class PolymarketClient:
    async def place_order(self, req: LiveOrderRequest) -> LiveOrderResult: ...
    async def cancel_order(self, order_id: str) -> bool: ...
    async def get_balance_usdc(self) -> float: ...
    async def close(self) -> None: ...
```

`LiveOrderRequest` フィールド: `token_id`, `side`, `price`, `size_usd`, `order_type`.

## 24.9 テスト

- **実 API 呼び出し禁止**（ch23 `@pytest.mark.live_mock`）
- フィクスチャ: Recorded HTTP (`tests/fixtures/clob/`)

## 24.10 章間参照

| 本章 | 参照先 |
|------|--------|
| §24.6 | ch13 §13.6.3, ch18 §18.3.7 |
| §24.3 | ch22 §22.2 polymarket |
| LiveExecutor | ch10 §10.7.7 |

## 24.11 レビュー（7項目）— 全合格

---

**出力ファイル名**: `24_polymarket_clob.md`
