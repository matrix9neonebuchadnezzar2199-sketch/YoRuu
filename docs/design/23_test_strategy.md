# 第23章 テスト戦略（デプロイ・ロールバック統合）

- **バージョン**: v1.0.0
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **ステータス**: APPROVED
- **関連章**: 16（不変条件）, 13（ペーパー約定）, 22（設定）, 05（信頼境界）

> **統合注記**: 旧 ch24「デプロイ + ロールバック」は本章 §23.8〜§23.9 に統合（中間レビュー案 Y、2026-05-27）。

## 23.1 目的・スコープ

### 23.1.1 目的

PHASE 3〜7 の**テストピラミッド**、**カバレッジ目標**、**CI パイプライン**、**デプロイ・ロールバック手順**を SSOT 化する。

### 23.1.2 テストピラミッド

```
        ┌─────────┐
        │  E2E    │  少数（Playwright UI、lab のみ）
       ┌┴─────────┴┐
       │ Integration │  API + DB + モック WS
      ┌┴─────────────┴┐
      │   Unit          │  戦略・Fill・状態・不変条件
      └─────────────────┘
```

## 23.2 ツールスタック

| 層 | ツール | 備考 |
|----|--------|------|
| 単体 | pytest, pytest-asyncio | `uv run pytest` |
| カバレッジ | pytest-cov | 目標 §23.3 |
| 静的解析 | ruff, mypy --strict | CI 必須 |
| 統合 | pytest + 一時 SQLite | `tmp_path` fixture |
| E2E | Playwright（任意） | ch8 モックと同 URL |

## 23.3 カバレッジ目標

| モジュール | 行カバレッジ | 分岐 |
|------------|--------------|------|
| `strategy/`（Markov, Kelly） | ≥ 90% | ≥ 85% |
| `execution/`（Paper, Fill） | ≥ 85% | ≥ 80% |
| `state/` | ≥ 90% | ≥ 85% |
| `api/` | ≥ 75% | — |
| `invariants/` | **100%**（全 INV-*） | 100% |
| 全体 | ≥ 80% | — |

## 23.4 不変条件テスト（ch16 連動）

| テスト ID | 対象 | 種別 |
|-----------|------|------|
| T-INV-01 | INV-S-02 EMERGENCY 中 TRADING | unit |
| T-INV-02 | INV-D-03 version 不一致起動 | integration |
| T-INV-03 | INV-R-05 二重エントリー | unit |
| T-INV-04 | INV-M-01 LIVE 拒否 | api |

各 `INV-*` は §16.2〜16.5 の表と 1:1 でトレース可能にする（`pytest.mark.invariant`）。

## 23.5 モード別テストスイート

| スイート | 内容 | マーカー |
|----------|------|----------|
| `paper` | PaperExecutor + モック OrderBook | `@pytest.mark.paper` |
| `backtest` | 30 日固定フィクスチャ | `@pytest.mark.backtest` |
| `live` | **モックのみ**（実 API 禁止） | `@pytest.mark.live_mock` |
| `nightly` | Apply TX + audit | `@pytest.mark.nightly` |

## 23.6 CI パイプライン（GitHub Actions）

```yaml
# 概要（詳細はリポジトリ .github/workflows/ci.yml）
on: [push, pull_request]
jobs:
  lint: ruff + mypy
  test: pytest -m "not live_mock" --cov --cov-fail-under=80
  design: scripts/verify_crossrefs.py  # 章参照整合（PHASE 1 後半で追加可）
```

## 23.7 テストデータ

- 合成 PE / 価格 CSV: `tests/fixtures/`（実検体禁止、§90 規約）
- EICAR 相当の無害バイナリのみ
- WebSocket: `tests/mock_ws/` 録画 JSON 再生

## 23.8 デプロイ（旧 ch24 統合）

### 23.8.1 環境

| 環境 | 用途 | ネットワーク |
|------|------|--------------|
| `lab` | 開発・SIMMER | 隔離 VM、Polymarket testnet 不可時は PAPER のみ |
| `prod` | LIVE | エアギャップ推奨 UI、API キーは OS 資格情報 |

### 23.8.2 デプロイ手順

```
1. git tag vX.Y.Z
2. uv sync --frozen
3. yoruu config validate
4. yoruu db migrate  # PHASE 3 で導入
5. systemctl restart yoruu  # または docker compose up -d
6. ヘルスチェック GET /api/v1/health
7. 起動ログで INV-D-03 合格確認
```

### 23.8.3 Docker（任意）

- イメージ: `python:3.12-slim`
- ボリューム: `data/`, `config/`, `logs/` のみマウント
- **秘密ファイルをイメージに焼かない**

## 23.9 ロールバック（旧 ch24 統合）

### 23.9.1 戦略ロールバック

- API: `POST /api/v1/strategy/rollback`（ch15 §15.8.5）
- 24 時間以内・version 連続性チェック → `E_NIGHTLY_014`

### 23.9.2 バイナリロールバック

```
1. systemctl stop yoruu
2. git checkout vX.Y.(Z-1)  # または前タグの wheel
3. yoruu db migrate --down  # スキーマ後方互換がある場合のみ
4. strategy.json は触らない（データ互換確認）
5. systemctl start yoruu
6. audit_log に DEPLOY_ROLLBACK 記録（v1.1 action 追加可）
```

### 23.9.3 ロールバック禁止条件

- DB マイグレーションが不可逆
- `EMERGENCY_STOP` 未解消のまま LIVE 再開

## 23.10 章間相互参照表

| 本章節 | 参照先 | 内容 |
|--------|--------|------|
| §23.4 | ch16 | INV-* |
| §23.5 | ch12, ch13 | モード・約定 |
| §23.8 | ch5, ch22 | 信頼境界・設定 |
| §23.9 | ch15, ch20 | rollback・audit |

## 23.11 品質チェック

### 23.11.2 レビュー判定（7項目）

| # | 観点 | 判定 |
|---|------|------|
| 1 | ch16 全 INV テスト化 | ✅ |
| 2 | カバレッジ数値 | ✅ |
| 3 | LIVE 実 API 禁止 | ✅ |
| 4 | デプロイ手順 | ✅ |
| 5 | ロールバック手順 | ✅ |
| 6 | ch5 lab 前提 | ✅ |
| 7 | 旧 ch24 統合明記 | ✅ |

---

**出力ファイル名**: `23_test_strategy.md`
