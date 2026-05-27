# YoRuu 開発ロードマップ

> **目的**: YoRuu の全工程を PHASE 0〜7 に分割し、各 PHASE の Exit Criteria・成果物・マイルストーンを SSOT として管理する。本ドキュメントは設計・実装・運用すべての判断基準であり、章番号変更・スコープ変更が発生した場合は本ファイルを最初に更新する。

**バージョン**: v1.0  
**作成日**: 2026-05-27  
**承認**: PHASE 0 完了時点  
**関連**: `INDEX.md`、`REVIEW_CHECKLIST_ch01-07.md`、`08_mockup_carryover.md`

---

## 1. 全体 Gantt

```mermaid
gantt
    title YoRuu 開発全体ロードマップ
    dateFormat YYYY-MM-DD
    axisFormat %m/%d

    section 設計
    PHASE 0 基盤合意       :done,    p0, 2026-05-25, 3d
    PHASE 1 設計書執筆     :active,  p1, 2026-05-28, 10d
    PHASE 2 UIモック実装   :         p2, after p1, 5d

    section 実装
    PHASE 3 コア実装       :         p3, after p2, 14d
    PHASE 4 UI実装         :         p4, after p3, 10d
    PHASE 5 統合テスト     :         p5, after p4, 7d

    section 運用
    PHASE 6 ペーパー運用   :         p6, after p5, 14d
    PHASE 7 段階移行       :         p7, after p6, 30d
```

---

## 2. PHASE 一覧（Exit Criteria 確定版）

### PHASE 0: 基盤合意 — 完了（2026-05-25 〜 2026-05-27）

**目的**: 設計方針・章構成・運用ルールの合意形成と ch1〜7 の初版確定。

**成果物**:

- `00_INSTRUCTIONS_ch01-07.md`（指示書）
- `REVIEW_CHECKLIST_ch01-07.md`（レビュー基準）
- `08_mockup_carryover.md`（第8章持ち越し事項）
- `docs/design/01_overview.md` 〜 `07_io_diagram.md`（ch1〜7 初版 + 補助レビュー反映）
- `INDEX.md`（24章構成の合意）

**Exit Criteria**:

- 24章構成の合意完了
- モック運用ルールの合意完了
- ch1〜7 初版生成完了
- ch1〜7 補助レビュー反映完了（コミット `49fccec`）
- ch1〜7 正式 `APPROVED`（コミット `2623330`）

### PHASE 1: 設計書執筆（2026-05-28 〜 2026-06-06、10日）

**目的**: ch1〜24 すべての設計書を `APPROVED` 状態に到達させる。

**成果物**: `docs/design/01_*.md` 〜 `docs/design/24_*.md`（全24章、合計約 20,000〜25,000字）

**マイルストーン**:

| ID | 内容 | 期間目安 | 状態 |
|----|------|----------|------|
| M1.0 | ロードマップ整備（本ファイル + INDEX/§1.7 + cross-ref + carryover 更新） | 半日 | 完了 |
| M1.1 | ch1〜7 `APPROVED` | — | 完了 |
| M1.2 | ch8 UIモック**設計書のみ** `APPROVED`（HTML は PHASE 2） | 2日 | **完了**（v1.2.1、`08_ui_mockup.md`） |
| M1.3 | ch9〜14 詳細設計（操作フロー・関数+データモデル・戦略・モード・ペーパー約定・i18n） | 3日 | **進行中**（ch9 執筆完了・レビュー待ち、1/6） |
| M1.4 | ch15〜19 安全設計（夜間レビュー・不変条件・リスク・エラー・キルスイッチ） | 2日 | 待機 |
| M1.5 | ch20〜24 運用設計（監査・設定影響・設定仕様・テスト・デプロイ） | 2日 | 待機 |

**Exit Criteria**:

- 全24章が `APPROVED`
- `INDEX.md` の全章ステータスが `APPROVED`
- cross-ref（章番号参照）の全件整合確認完了
- 章間矛盾レビュー完了

### PHASE 2: UIモック実装（5日）

**目的**: 11画面の HTML モックを動作可能な状態で完成させる。

**成果物**:

- `docs/mockups/index.html`（ハブ）
- `docs/mockups/01_dashboard.html` 〜 `10_what_if.html`（10画面 + ハブ）
- `docs/mockups/shared/style.css`（GitHub Dark）
- `docs/mockups/shared/i18n.js`（ja 完備、en 枠）
- `docs/mockups/shared/mock-data.js`（リアル系数値）

**マイルストーン**:

| ID | 内容 |
|----|------|
| M2.1 | shared/* + index.html + ダッシュボード + 取引履歴 |
| M2.2 | 夜間レビュー + 戦略履歴 + Markov ライブビュー |
| M2.3 | 設定 + アラート + モード切替 + 緊急停止 + What‑If |

**Exit Criteria**:

- 全画面マスター承認
- ブラウザ（Chrome / Firefox）でダブルクリック起動・動作確認済み
- 外部CDN依存ゼロ確認

### PHASE 3: コア実装（14日）

**目的**: 取引ロジックの実装（UI なし、CLI で動作）。

**成果物**: `yoruu/core/`、`yoruu/strategy/`、`yoruu/execution/`、`yoruu/data/`、`tests/unit/`

**マイルストーン**:

| ID | 内容 |
|----|------|
| M3.1 | データ取得層（Binance WS + Polymarket CLOB） |
| M3.2 | Markov 推定 + Kelly サイジング |
| M3.3 | ペーパー約定エンジン（スリッページ・手数料・遅延モデル） |
| M3.4 | SQLite 永続化 + StateMachine |
| M3.5 | 夜間レポート生成（JSON 出力） |
| M3.6 | 戦略 Apply ロジック（CLI から） |

**Exit Criteria**:

- ペーパーモードで 24 時間連続稼働
- ユニットテスト pass（カバレッジ目標は ch23 で確定）
- 不変条件（ch16）assertion 全件通過

### PHASE 4: UI実装（10日）

**目的**: モックを実動 Web UI に変換。

**成果物**: `yoruu/web/`（FastAPI + 静的 HTML + REST + SSE）

**マイルストーン**:

| ID | 内容 |
|----|------|
| M4.1 | FastAPI 基盤 + SSE（リアルタイム更新） |
| M4.2 | ダッシュボード + 取引履歴 + Markov ライブビュー |
| M4.3 | 夜間レビュー Apply 画面（JSON 貼付け） |
| M4.4 | 設定・モード切替・緊急停止 |
| M4.5 | i18n 適用（日本語完備）・What‑If 実計算 |

**Exit Criteria**:

- モックと同等の動作
- API 応答時間 < 200ms（ローカル）
- SSE イベント全件動作確認

### PHASE 5: 統合テスト（7日）

**目的**: 安全性・例外系の最終検証。

**マイルストーン**:

| ID | 内容 |
|----|------|
| M5.1 | 不変条件テスト |
| M5.2 | カオステスト（WS切断・API障害・ディスクフル） |
| M5.3 | 緊急停止リハーサル |
| M5.4 | バックテストでの妥当性検証 |

**Exit Criteria**:

- 全テスト pass
- 72 時間ペーパー連続稼働
- カオステスト全シナリオで安全停止確認

### PHASE 6: ペーパー運用（14日）

**目的**: 実市場データでのペーパートレード運用。

**マイルストーン**:

| ID | 内容 |
|----|------|
| M6.1 | 初期戦略パラメータ確定 |
| M6.2 | 1週目運用 + 日次レビュー |
| M6.3 | 2週目運用 + 戦略パラメータ調整 |

**Exit Criteria**:

- 累積勝率 > 50%（参考値、絶対基準ではない）
- 最大ドローダウン < 20%
- 夜間レビューサイクル安定稼働

### PHASE 7: 段階移行（30日、任意）

**目的**: 少額からの実運用。

**マイルストーン**: $10 → $50 → $100 → 本格運用、各段階で1週間以上の検証。

**Exit Criteria**: マスター判断。

---

## 3. PHASE 間の依存関係

```mermaid
flowchart LR
    P0[PHASE 0<br>基盤合意] --> P1[PHASE 1<br>設計書執筆]
    P1 --> P2[PHASE 2<br>UIモック]
    P1 --> P3[PHASE 3<br>コア実装]
    P2 --> P4[PHASE 4<br>UI実装]
    P3 --> P4
    P4 --> P5[PHASE 5<br>統合テスト]
    P5 --> P6[PHASE 6<br>ペーパー運用]
    P6 --> P7[PHASE 7<br>段階移行]
```

PHASE 2 と PHASE 3 は PHASE 1 完了後に**並行可能**。PHASE 4 は両者の完了後に着手する。

---

## 4. 章番号と PHASE の対応表

| PHASE | 関連章 |
|-------|--------|
| PHASE 0 | ch1〜7 初版 |
| PHASE 1 M1.2 | ch8 |
| PHASE 1 M1.3 | ch9, ch10, ch11, ch12, ch13, ch14 |
| PHASE 1 M1.4 | ch15, ch16, ch17, ch18, ch19 |
| PHASE 1 M1.5 | ch20, ch21, ch22, ch23, ch24 |
| PHASE 2 | ch8 の HTML 実装 |
| PHASE 3 | ch11, ch13, ch10（データモデル節）が主要参照 |
| PHASE 4 | ch8, ch14 が主要参照 |
| PHASE 5 | ch16, ch17, ch18, ch19, ch23 が主要参照 |
| PHASE 6 | ch15, ch20 が主要参照 |
| PHASE 7 | ch22, ch24 が主要参照 |

---

## 5. 変更管理ルール

- **章番号変更**: 本ファイル §4 と `INDEX.md` を同時更新、`01_overview.md` §1.7 も同期。
- **PHASE 期間変更**: §1 Gantt と該当 PHASE の節を更新、変更理由を §6 変更履歴に追記。
- **マイルストーン追加・削除**: 該当 PHASE の表を更新、`INDEX.md` の進捗にも反映。

## 6. 変更履歴

| 日付 | バージョン | 変更内容 | コミット |
|------|-----------|----------|----------|
| 2026-05-27 | v1.0 | 初版作成、PHASE 0 完了確認、M1.0 ロードマップ整備 | `bce8a03` |
| 2026-05-27 | v1.0 | M1.2 完了、第8章 APPROVED（v1.2.1、severity 変数追記） | `832ad1e` |
