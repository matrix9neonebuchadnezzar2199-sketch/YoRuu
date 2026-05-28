# PHASE 4 ロードマップ v1（採用済）

**日付**: 2026-05-28  
**ステータス**: **ADOPTED**（マスター承認・I-1 / 案 P 確定、`140437f` 系）  
**前提**: M4.1〜M4.2 ✅、PHASE 3 コード Exit ✅  
**旧草案**: [`PHASE4_ROADMAP_REVISION_DRAFT_2026-05-28.md`](./PHASE4_ROADMAP_REVISION_DRAFT_2026-05-28.md)（履歴）

---

## ゴール

参照画像（Hermes 型 HUD）相当の **単一画面体験** を、**元本概念（A-2/B-2）** を正しく扱う形で実現する。

---

## Hub / HUD ナビ（I-1 確定）

| 画面 | 役割 | パス |
|------|------|------|
| **HUD（主入口）** | 情報密集型ビューア・ボット実感 | `docs/mockups/00_hud.html` |
| **Hub** | 10 画面ナビ + 業務サマリ | `docs/mockups/index.html` |

**運用ルール**

- ブックマーク・README・Quick Start の「最初に開くページ」は **`00_hud.html`**（serve 時は `/pages/00_hud.html`）。
- Hub と HUD は **両画面温存**。相互リンクで双方向動線（M4.7 出口条件）。
- `index.html` の i18n / `hub_meta` は **削除・吸収しない**（I-2 相当の変更は行わない）。

---

## マイルストン（案 P: M4.6 → M4.7 順序維持）

| ID | 名称 | 領域 | 状態 | 出口条件（要約） |
|----|------|------|------|----------------|
| M4.1 | FastAPI + SSE 契約 | Composer | ✅ `dea96e0` | |
| M4.2 | 静的モック + EventSource | Composer | ✅ `02edfa0` | |
| **M4.3** | 設計章追補（元本 + ch10 v1.2） | Opus | **進行中** | ch10 ドラフト [`ch10_v1.2_ROLLING_DRAFT.md`](./ch10_v1.2_ROLLING_DRAFT.md) レビュー待ち（U 判断含む） |
| M4.4 | 元本コア実装 | Composer | ⏳ | DB、PrincipalService、D11 v2、INV 拡張、pytest 維持 |
| M4.5 | REST + CLI + SSE `principal_changed` | Composer | ⏳ | API/CLI、SSE 契約 |
| M4.6 | `mock-data.js` 拡張 | Composer | ⏳ | 既存 10 画面モック不変 |
| M4.7 | `00_hud.html` 新規 | Composer | ⏳ | 参照 8 割一致、I-1 相互リンク、チャート placeholder |
| M4.8 | i18n + static 反映 | Composer | ⏳ | `build_web_static`、serve で HUD |
| M4.9 | PHASE 4 Exit 宣言 | Opus | ⏳ | `PHASE4_EXIT_DECLARATION.md` |

**案 Q**（M4.6/M4.7 順序入替・スケルトン先行）は **不採用**。M4.7 内でダミー値スケルトンの中間レビューは可。

### PHASE 3 Exit 残の扱い

| 項目 | 扱い |
|------|------|
| lab 24h paper | **PHASE 5**（HUD 完成後に観察セット） |
| ch10 全 SSE severity 必須 | **M4.3** に統合 |

### PHASE 5（仮）

- M5.x ローソク足 + エントリーマーカー
- lab 24h paper + HUD 観察

---

## 依存関係

```mermaid
flowchart LR
  M43[M4.3 設計] --> M44[M4.4 コア]
  M44 --> M45[M4.5 API]
  M45 --> M46[M4.6 mock-data]
  M46 --> M47[M4.7 HUD HTML]
  M47 --> M48[M4.8 static/i18n]
  M48 --> M49[M4.9 Exit]
```

---

## 関連正本

- 突き合わせ: [`../mockups/REF_IMAGE_GAP_MATRIX_v2.md`](../mockups/REF_IMAGE_GAP_MATRIX_v2.md)
- 元本ドラフト: [`PRINCIPAL_CONCEPT_V1_DRAFT.md`](./PRINCIPAL_CONCEPT_V1_DRAFT.md)
- 投入テンプレ: [`PHASE3_PARALLEL_CHAT_TEMPLATES.md`](./PHASE3_PARALLEL_CHAT_TEMPLATES.md) テンプレート 14
