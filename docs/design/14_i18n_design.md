# 第14章 i18n 設計

- **バージョン**: v1.0.2
- **作成日**: 2026-05-27
- **承認日**: 2026-05-27
- **最終更新**: 2026-05-28（v1.0.2: §14.5 ja/en フォールバック明文化、§14.11.4 bundle 同期 CI）
- **ステータス**: APPROVED
- **関連章**: 1（概要 §1.2）, 8（UI モック §8.8 / §8.20.5.1）, 9（ユーザーフロー §9.13）, 10（関数・データモデル §10.6.11 / §10.11.5）, 18（エラーコード）
- **新設章**（旧構成にはなし、ch24 再編で追加）

## 14.1 目的・スコープ

### 14.1.1 目的

YoRuu の国際化（i18n）設計を単一の真実（SSOT）として確定する。UI 全文字列の翻訳キー化、辞書構造、フォールバック規則、サーバー側 i18n エンドポイント、開発時規約を規定し、初期から日本語・英語の二言語に対応可能な状態にする。日本語が一次言語、英語は将来拡張用の枠組みのみを v1.0 で確定する。

### 14.1.2 スコープ（含む）

- 二言語ポリシー（日本語完備、英語空辞書）（§14.2）
- 翻訳キー命名規則（§14.3）
- 辞書ファイル構造（§14.4）
- フォールバック規則（§14.5）
- UI 側実装規約（`data-i18n` 属性、`t()` 関数）（§14.6）
- サーバー側 i18n（§14.7）
- 動的文字列・変数埋込（§14.8）
- 日時・数値・通貨フォーマット（§14.9）
- 翻訳キー一覧（カテゴリ別代表例）（§14.10）
- 開発時規約・運用フロー（§14.11）

### 14.1.3 スコープ外

- HTML/CSS/JavaScript 実装コード（→ PHASE 2 / PHASE 4）
- 英語翻訳の完成（PHASE 7 以降）
- 多言語 OCR / 音声 UI（範囲外）
- ライブ翻訳 API 連携（範囲外）

### 14.1.4 設計原則

1. **キー優先**: すべての表示文字列を翻訳キー経由とする。ハードコードされた日本語/英語文字列を禁止
2. **二言語前提**: v1.0 から `ja` / `en` の 2 言語スロット、`en` は空辞書として枠を確保
3. **フォールバック透明性**: `en` 不在時は `ja` で表示、開発者には警告ログを出力
4. **クライアント解決**: 翻訳は UI 側で解決、サーバー API は言語非依存の構造化データを返す
5. **拡張容易性**: 第3言語追加が辞書ファイル追加のみで完結

## 14.2 二言語ポリシー

### 14.2.1 サポート言語

| コード | 言語 | v1.0 時点の完成度 |
|--------|------|-----------------|
| `ja` | 日本語 | 完備（一次言語） |
| `en` | 英語 | 空辞書（キー枠のみ、表示は `ja` フォールバック） |

### 14.2.2 既定言語の決定順序

1. URL クエリ `?lang=ja|en`（セッション一時）
2. `localStorage.yoruu_lang`（ユーザー選択保存）
3. `yoruu.yaml` `ui.default_language`（§10.4.2、既定 `ja`）
4. ブラウザ `navigator.language` の頭 2 文字
5. ハードコード既定 `ja`

### 14.2.3 言語切替の挙動

- ヘッダーの言語切替プルダウン（§8.5.2）で即時切替
- 切替時に `localStorage` 更新、全 `data-i18n` 要素を再描画
- SSE 受信中のメッセージはキャッシュから再翻訳（言語切替で表示が即反映）
- API リロード不要（クライアント側解決）

### 14.2.4 英語完備までの方針

- v1.0: 英語辞書ファイル（`en.json`）は空 `{}` で配置
- PHASE 4 〜 PHASE 6: 日本語完備、英語は未着手
- PHASE 7 以降: 英語翻訳追加（コミュニティ翻訳 or 機械翻訳の人手校正）

## 14.3 翻訳キー命名規則

### 14.3.1 全体構造

```
<namespace>.<context>.<element>[.<variant>]
```

- 全て `snake_case`
- 階層は `.` で区切る、最大 4 階層
- ASCII のみ、絵文字・全角文字禁止

### 14.3.2 名前空間（namespace）

第一階層の名前空間 11 種類：

| 名前空間 | 用途 | 例 |
|---------|------|------|
| `nav` | サイドバー・ナビゲーション | `nav.dashboard` |
| `page` | 各画面のタイトル・見出し | `page.dashboard.title` |
| `action` | ボタン・操作のラベル | `action.apply` |
| `metric` | 数値・指標のラベル | `metric.daily_pnl` |
| `state` | ボット状態の表示名 | `state.trading` |
| `mode` | モード表示名 | `mode.paper` |
| `cmd` | コマンドパレット項目 | `cmd.switch_mode_live` |
| `alert` | アラートメッセージ | `alert.ws_disconnected` |
| `error` | エラーコード対応メッセージ | `error.e_fill_001` |
| `tooltip` | ツールチップ・補足説明 | `tooltip.persistence_threshold` |
| `markov` | Markov 関連（§8.20） | `markov.wait.persistence` |

§14.11.6 の `a11y.*` は ARIA 専用の追加名前空間（12 種目相当、キー総数に含める）。

### 14.3.3 コンテキスト（context）

第二階層は画面・機能を表す：

- `page.dashboard.*` ⇒ ダッシュボード画面内の文字列
- `action.modal.*` ⇒ モーダル内の操作ボタン
- `tooltip.settings.*` ⇒ 設定画面のツールチップ

### 14.3.4 要素（element）

第三階層は具体的な要素：

- `page.dashboard.title` ⇒ 画面タイトル
- `metric.daily_pnl.label` ⇒ 「当日損益」ラベル
- `metric.daily_pnl.unit` ⇒ 「USD」など単位

### 14.3.5 バリアント（variant）

第四階層は同一要素の文脈差異：

- `state.trading.short` ⇒ 「取引中」（短縮）
- `state.trading.long` ⇒ 「取引中（自動エントリー判定実行中）」（詳細）
- `action.apply.confirm` ⇒ 確認ダイアログでの「適用する」

`markov.wait.risk` は §8.20.5.1 の `risk_*` サフィックスを `.risk` バリアントで代表（具体化は `markov.wait.risk_balance` 等の第 4 階層で吸収可）。

### 14.3.6 予約キー

| キー | 用途 |
|------|------|
| `_meta.lang_name` | 当該言語の自称（例: `ja` の `_meta.lang_name = "日本語"`） |
| `_meta.version` | 辞書ファイルのバージョン |
| `_meta.completeness` | 完成度パーセンテージ（情報的） |

### 14.3.7 禁止事項

- 文末記号（。、！？）をキーに含めない（値側で管理）
- 動詞活用形をキーに含めない（`action.save` / `action.saving` は別キー）
- 番号付け（`label1`, `label2`）禁止、意味的命名を強制

## 14.4 辞書ファイル構造

### 14.4.1 配置

```
src/yoruu/ui/locales/
├─ ja.json
├─ en.json
└─ _schema.json   # JSON Schema（バリデーション用）
```

PHASE 2 のモックでは：

```
docs/mockups/shared/locales/
├─ ja.json          # SSOT（編集対象）
├─ en.json          # SSOT（キー枠、値は空可）
├─ ja.bundle.js     # file:// 用ビルド成果物（ja.json から生成）
└─ en.bundle.js     # 同上（PHASE 4 以降）
```

`ja.bundle.js` / `en.bundle.js` は **手編集禁止**。`tools/build_locales.py`（PHASE 3 実装予定）で JSON → bundle を再生成する（§14.11.4）。

### 14.4.2 ファイル形式

JSON、UTF-8、フラットなキー→値マップ：

```json
{
  "_meta.lang_name": "日本語",
  "_meta.version": "1.0.0",
  "_meta.completeness": 100,

  "nav.dashboard": "ダッシュボード",
  "nav.trade_log": "取引履歴",
  "nav.nightly_review": "夜間レビュー",

  "page.dashboard.title": "ダッシュボード",
  "page.dashboard.subtitle": "リアルタイム監視",

  "action.apply": "適用",
  "action.cancel": "キャンセル",
  "action.emergency_stop": "緊急停止",

  "metric.daily_pnl.label": "当日損益",
  "metric.win_rate.label": "勝率",

  "state.trading.short": "取引中",
  "state.idle.short": "待機中",

  "mode.paper": "ペーパー",
  "mode.simmer": "シマー",
  "mode.live": "ライブ",

  "markov.wait.persistence": "持続性閾値未達",
  "markov.wait.edge": "エッジ不足",
  "markov.wait.prob": "確率不足",
  "markov.wait.risk": "リスク制約",
  "markov.wait.liquidity": "流動性不足",

  "error.e_fill_001": "流動性不足のため約定できませんでした"
}
```

### 14.4.3 ネスト構造を採用しない理由

- フラットキーは `t('nav.dashboard')` 形式の検索が O(1)
- ネスト構造（`{"nav": {"dashboard": "…"}}`）は深いキーで型不整合リスク
- 翻訳ツール（po2json 等）との互換性が高い
- キー検索・grep が容易

### 14.4.4 サイズ目安

- v1.0 完成時の `ja.json`: 約 500〜700 キー
- ファイルサイズ: 50〜80 KB（圧縮前）、UI ロード時に一括取得
- HTTP gzip で 15〜25 KB に圧縮想定

## 14.5 フォールバック規則

### 14.5.1 解決順序

`t(key, lang)` の解決。**一次言語は `ja`、英語は `en` フォールバック**（Track 2D / T4.2 前提）。

```
1. <lang>.json に key が存在し値が非空 → 値返却
2. lang != ja かつ ja.json に key 存在 → 値返却（en フォールバック時は WARN ログ、§14.5.2）
3. lang == ja かつ en.json に key 存在 → 値返却（開発用・WARN ログ）
4. key 文字列そのまま返却（ERROR ログ）
```

`lang=en` で `en.json` が空 `{}` の期間は、手順 1 をスキップし手順 2 で常に `ja` に落ちる（§14.2.4）。

### 14.5.2 フォールバック時のログ

| 状況 | ログレベル | 出力先 |
|------|----------|-------|
| `en` 表示で `ja` にフォールバック（手順 2） | **WARN** | コンソール |
| `ja` 表示で `en` にフォールバック（手順 3） | WARN | コンソール |
| 手順 4（キーそのまま） | ERROR | コンソール + サーバー `alerts`（PHASE 5 以降検討） |
| 言語コード不正（`zh` 等） | WARN、`ja` で表示 | コンソール |

### 14.5.3 UI 表示時のフォールバック明示

- 開発モード（`?dev=1`）では、フォールバック発生時に該当要素に CSS クラス `i18n-fallback` 追加
- 本番モードでは透明（フォールバックは表示上影響なし）

### 14.5.4 サーバー側フォールバック

`GET /api/v1/i18n/{lang}` で `lang=en` 指定時、空辞書 `{}` を返す（クライアント側で `ja` にフォールバック）。`lang=zh` 等の未対応言語は 404 ではなく `ja` 辞書を返す（クライアントの再リクエスト回避）。

## 14.6 UI 側実装規約

### 14.6.1 HTML 属性

```html
<button data-i18n="action.emergency_stop">緊急停止</button>
```

- `data-i18n` 属性に翻訳キーを記述
- 属性値が現言語で解決される
- 初期 HTML 内の日本語テキストはフォールバック表示用（JS 無効時に意味が通る）

### 14.6.2 属性翻訳

属性自体も翻訳可能：

```html
<button
  data-i18n="action.apply"
  data-i18n-attr-title="tooltip.apply_strategy"
  data-i18n-attr-aria-label="a11y.apply_button">
  適用
</button>
```

- `data-i18n-attr-<attr>` で各属性を指定
- 複数属性可

### 14.6.3 `t()` 関数

```javascript
function t(key, vars = {}) {
  const value = lookupKey(key, currentLang);
  if (!value) {
    console.error(`[i18n] Missing key: ${key}`);
    return key;
  }
  return interpolate(value, vars);
}
```

JavaScript 動的生成時のみ使用、HTML 内静的テキストは `data-i18n` を優先。

### 14.6.4 言語切替時の再描画

```javascript
function switchLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('yoruu_lang', lang);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-attr]').forEach(el => {
    // 属性翻訳の再描画
  });
}
```

### 14.6.5 `<html lang>` 属性

言語切替時に `<html lang="ja">` も同期更新（スクリーンリーダー対応）。

## 14.7 サーバー側 i18n

### 14.7.1 原則

サーバー API は **言語非依存** の構造化データを返す。例：

```json
{
  "ok": false,
  "error": {
    "code": "E_FILL_001",
    "severity": "ERROR",
    "details": { "market": "BTC_5MIN_UPDOWN" }
  }
}
```

クライアントは `code = "E_FILL_001"` を `t('error.e_fill_001')` で表示。

### 14.7.2 例外：エラーメッセージの英語フォールバック

`error.message` フィールドには英語の短い説明を含める（開発者・ログ用）：

```json
{
  "code": "E_FILL_001",
  "message": "Insufficient liquidity",
  "severity": "ERROR"
}
```

- `code` が一次キー、`message` は補助（ログ・デバッグ用）
- UI は `code` ベースで `t()` 解決、`message` は表示しない（フォールバック時のみ）

### 14.7.3 i18n エンドポイント

`GET /api/v1/i18n/{lang}`（§10.6.11）:

```json
{
  "ok": true,
  "data": {
    "_meta.lang_name": "日本語",
    "_meta.version": "1.0.0",
    "nav.dashboard": "ダッシュボード"
  }
}
```

- 起動時に UI が一括取得
- `Cache-Control: max-age=3600`（辞書はビルド時固定のため 1 時間キャッシュ）
- 辞書更新時はサーバー再起動 or キャッシュバスター（`?v=<hash>`）

### 14.7.4 辞書のソース・オブ・トゥルース

`src/yoruu/ui/locales/*.json` がサーバー側 SSOT。`docs/mockups/shared/locales/*.json` は PHASE 2 モック用で、PHASE 4 で `src/` 配下に統合・同期。

### 14.7.5 ログ・監査の言語

- サーバーログ・`audit_log` は英語（または日本語固定）で記録
- ログは多言語化しない（運用者向け）
- `alerts.message` は日本語固定（UI 表示時にそのまま使用 or `code` 経由で再翻訳）

判断: **`alerts.message` は日本語固定**（UI が `ja` 一次のため）、`code` で英語フォールバック可能な設計とする。PHASE 7 以降で `alerts.code` 経由の翻訳に移行検討。

## 14.8 動的文字列・変数埋込

### 14.8.1 変数埋込構文

`{varname}` 形式：

```json
{
  "alert.position_opened": "{side} ポジションを ${size} で約定しました"
}
```

```javascript
t('alert.position_opened', { side: 'YES', size: 7.10 })
// → "YES ポジションを $7.10 で約定しました"
```

### 14.8.2 複数形対応

英語の複数形は ICU MessageFormat の簡易版を採用（v1.1 検討、v1.0 では単数固定）：

```json
{
  "metric.trade_count": "{count, plural, =0 {0 取引} =1 {1 取引} other {# 取引}}"
}
```

日本語は複数形変化なし、英語完成時に対応。

### 14.8.3 性別・敬語

YoRuu は単一ユーザー向けかつ機械的 UI のため、敬語レベル・性別の動的選択は不要。日本語は「ですます調」、英語は「フォーマル中立」で統一。

### 14.8.4 改行・段落

- `\n` で改行（JSON エスケープ）
- HTML タグ（`<br>` 等）はキー値に含めない（XSS リスク・国際化困難）
- 段落分割が必要な場合はキーを分割（`page.help.intro` / `page.help.detail`）

### 14.8.5 HTML エスケープ

`t()` の戻り値は HTML エスケープして DOM に挿入。`innerHTML` 直接代入禁止、`textContent` を使用。リッチテキストが必要な場合は別途専用キー（v1.1 検討）。

## 14.9 日時・数値・通貨フォーマット

### 14.9.1 日時

`Intl.DateTimeFormat` を使用、言語コード渡し：

```javascript
new Intl.DateTimeFormat(currentLang, {
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit',
  timeZone: 'Asia/Tokyo'
}).format(date);
```

- 日本語: `2026/05/27 14:32`
- 英語: `05/27/2026 02:32 PM`

タイムゾーンは `Asia/Tokyo` 固定（§10.12.4）。

### 14.9.2 数値

`Intl.NumberFormat`：

```javascript
new Intl.NumberFormat(currentLang, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(8.42);
```

桁区切り: 日本語・英語とも `1,000.50` 形式。

### 14.9.3 通貨

USD 固定（§10.4.2 `currency: USD`）：

```javascript
new Intl.NumberFormat(currentLang, {
  style: 'currency',
  currency: 'USD',
}).format(8.42);
```

両言語とも `$` プレフィックス。v1.1 で「￥」「€」追加検討。

### 14.9.4 パーセント

```javascript
new Intl.NumberFormat(currentLang, {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
}).format(0.543);
```

### 14.9.5 単位の翻訳

固有単位（USD・%）は数値フォーマッタが扱う。それ以外（ms・bps 等）は翻訳キー化：

```json
{
  "unit.ms": "ミリ秒",
  "unit.sec": "秒",
  "unit.bps": "bps"
}
```

## 14.10 翻訳キー一覧（カテゴリ別代表例）

完全な一覧は `docs/mockups/shared/locales/ja.json` を SSOT とし、本章では代表例のみ記載。

### 14.10.1 `nav.*`（サイドバー、11 件）

| キー | 値 |
|------|---|
| `nav.dashboard` | ダッシュボード |
| `nav.trade_log` | 取引履歴 |
| `nav.nightly_review` | 夜間レビュー |
| `nav.settings` | 設定 |
| `nav.strategy_history` | 戦略履歴 |
| `nav.alerts` | アラート |
| `nav.mode_switch` | モード切替 |
| `nav.emergency_stop` | 緊急停止 |
| `nav.markov_live` | Markov ライブ |
| `nav.what_if` | What-If |
| `nav.hub` | ハブ |

### 14.10.2 `page.*`（画面タイトル・見出し、約 60 件）

| キー | 値 |
|------|---|
| `page.dashboard.title` | ダッシュボード |
| `page.dashboard.subtitle` | リアルタイム監視 |
| `page.nightly_review.title` | 夜間レビュー |
| `page.nightly_review.diff_preview` | 差分プレビュー |
| `page.mode_switch.live_warning` | LIVE モードは実資金が動きます |
| `page.emergency_stop.title` | 緊急停止 |

### 14.10.3 `action.*`（操作ラベル、約 50 件）

| キー | 値 |
|------|---|
| `action.apply` | 適用 |
| `action.cancel` | キャンセル |
| `action.confirm` | 確認 |
| `action.emergency_stop` | 緊急停止 |
| `action.rollback` | ロールバック |
| `action.export_csv` | CSV エクスポート |
| `action.copy_json` | JSON をコピー |
| `action.paste_json` | JSON を貼り付け |

### 14.10.4 `metric.*`（指標ラベル、約 40 件）

| キー | 値 |
|------|---|
| `metric.daily_pnl.label` | 当日損益 |
| `metric.cumulative_pnl.label` | 累積損益 |
| `metric.win_rate.label` | 勝率 |
| `metric.trade_count.label` | 取引数 |
| `metric.persistence.label` | 持続性 |
| `metric.edge.label` | エッジ |

### 14.10.5 `state.*`（状態名、9 状態 × 2 バリアント = 18 件）

| キー | 値 |
|------|---|
| `state.initializing.short` | 起動中 |
| `state.idle.short` | 待機中 |
| `state.trading.short` | 取引中 |
| `state.monitoring_position.short` | ポジション監視中 |
| `state.nightly_review.short` | 夜間レビュー中 |
| `state.emergency_stop.short` | 緊急停止 |
| `state.error.short` | エラー |
| `state.shutdown.short` | 終了 |
| `state.backtest.short` | バックテスト |

各 `.long` バリアントも併設（詳細説明文）。

### 14.10.6 `mode.*`（モード名、4 件）

| キー | 値 |
|------|---|
| `mode.backtest` | バックテスト |
| `mode.paper` | ペーパー |
| `mode.simmer` | シマー |
| `mode.live` | ライブ |

### 14.10.7 `markov.*`（§8.20.5.1 同期、6 件）

| キー | 値 | wait_reason |
|------|---|-------------|
| `markov.wait.persistence` | 持続性閾値未達 | `persistence` |
| `markov.wait.edge` | エッジ不足 | `edge` |
| `markov.wait.prob` | 確率不足 | `prob` |
| `markov.wait.risk` | リスク制約 | `risk_*` |
| `markov.wait.liquidity` | 流動性不足 | `liquidity` |
| `markov.wait.risk_budget` | 予算上限 | `risk_budget` |

### 14.10.8 `error.*`（エラーコード対応、PHASE 3 で 50〜100 件）

| キー | 値 |
|------|---|
| `error.e_fill_001` | 流動性不足のため約定できませんでした |
| `error.e_fill_002` | スプレッドが大きすぎます |
| `error.e_mode_001` | LIVE 切替の要件を満たしていません |
| `error.e_state_001` | 現在の状態ではこの操作は実行できません |

第18章で全コードを確定。ch18 APPROVED 後に v1.0.1 追補候補。

### 14.10.9 `tooltip.*`（補足説明、約 80 件）

| キー | 値 |
|------|---|
| `tooltip.persistence_threshold` | 行列の自己遷移確率の最小値が閾値以上である場合のみエントリーします |
| `tooltip.kelly_fraction` | Kelly 基準で算出した最適サイズの何%を実際に賭けるかを決定します |
| `tooltip.daily_loss_limit` | 当日の損失がこの額に達すると新規エントリーを停止します |

### 14.10.10 `cmd.*`（コマンドパレット、約 30 件）

| キー | 値 |
|------|---|
| `cmd.goto_dashboard` | ダッシュボードへ移動 |
| `cmd.switch_mode_paper` | モードを PAPER に切替 |
| `cmd.switch_mode_live` | モードを LIVE に切替（要確認） |
| `cmd.emergency_stop` | 緊急停止（即時発火） |

### 14.10.11 `_meta.*`（予約、3 件）

| キー | 値 |
|------|---|
| `_meta.lang_name` | 日本語 |
| `_meta.version` | 1.0.0 |
| `_meta.completeness` | 100 |

## 14.11 開発時規約・運用フロー

### 14.11.1 新規キー追加の手順

1. 該当画面・コンポーネントでキーを設計（§14.3 命名規則準拠）
2. `ja.json` に追加
3. `en.json` に空文字列または同キーで追加（フォールバック動作確認）
4. UI 側で `data-i18n` または `t()` で参照
5. 単体テストでキー存在を確認

### 14.11.2 キー削除・変更の手順

- キー削除: 全 UI 参照を grep 検索、削除後にビルド
- キー名変更: 旧キーを 1 リリース残し、deprecated コメント、次リリースで削除
- 値変更: 直接編集可、レビュー必須

### 14.11.3 翻訳ツール連携

- v1.0 では手動編集
- v1.1 以降で `po2json` / `lingui` 等の連携検討
- 機械翻訳（DeepL / GPT）の補助使用は可、人手校正必須

### 14.11.4 CI/CD でのバリデーション

PHASE 4 以降で以下を CI 化（**差分時 fail**）：

1. **キー集合同期**: `ja.json` と `en.json` のキー集合が完全一致（`en` の値は空文字列可）
2. **bundle 同期**: `ja.bundle.js` / `en.bundle.js` が直近 `build_locales` 出力と一致
3. **HTML 参照**: 全 `data-i18n` に対応キーが `ja.json` に存在
4. 未使用キー検出（警告）、重複キー検出（fail）

検査手順例（リポジトリルート）:

```bash
python tools/build_locales.py --check
# 内部: json.load → キー集合 diff → bundle ハッシュ比較 → exit 1 on mismatch
```

`tools/build_locales.py` は `ja.json` → `ja.bundle.js`（`window.YORUU_LOCALES_ja = {...}`）を生成し、`--write` で上書き、`--check` で CI 用検証のみ行う。pre-commit フック登録は T4.9（別タスク）。

### 14.11.5 キー数モニタリング

| 指標 | 目標 |
|------|------|
| キー総数 | 500〜700（v1.0 完成時） |
| 平均キー長 | 5〜30 文字 |
| ファイルサイズ | 50〜80 KB（圧縮前） |
| 未使用キー | 5% 以下 |

### 14.11.6 アクセシビリティ連携

- `a11y.*` 名前空間は ARIA ラベル専用
- スクリーンリーダー読み上げに最適化された短い表現
- `aria-label` / `aria-describedby` への注入で使用（§8.22）

| キー | 値 |
|------|---|
| `a11y.main_nav` | メインナビゲーション |
| `a11y.apply_button` | 適用ボタン（適用後は元に戻せません） |
| `a11y.emergency_stop_button` | 緊急停止ボタン（確認なしで即時発火） |

### 14.11.7 i18n テスト

- フォールバック動作確認（`en` 空状態で UI が `ja` で表示されるか）
- 言語切替時の即時反映（全 `data-i18n` 要素）
- 変数埋込（`{var}` 展開）
- 動的生成 UI での `t()` 動作
- ARIA 属性の言語追従

## 14.12 章間相互参照表

| 本章節 | 参照先 | 内容 |
|-------|--------|------|
| §14.2.2 既定言語決定 | §10.4.2 `ui.default_language` | yoruu.yaml 設定 |
| §14.4 辞書配置 | §10.11.5 `I18n` クラス | サーバー側実装 |
| §14.6 UI 実装規約 | 第8章 §8.8 | UI モック i18n 方針 |
| §14.6.1 `data-i18n` | 第8章 §8.5 / §8.6 | 共通レイアウト |
| §14.7.3 i18n エンドポイント | §10.6.11 | REST API 仕様 |
| §14.7.5 alerts.message | §10.3.8 `alerts` テーブル | 日本語固定方針 |
| §14.8.1 変数埋込 | 第8章 §8.17.5 | アラートカード |
| §14.9 日時・数値 | §10.12.4 タイムゾーン規約 | Asia/Tokyo 固定 |
| §14.10.7 `markov.*` | 第8章 §8.20.5.1 / 第11章 §11.7 | wait_reason 6 値同期 |
| §14.10.8 `error.*` | 第18章 | エラーコード SSOT |
| §14.11.6 アクセシビリティ | 第8章 §8.22 | ARIA 連携 |
| §14.2.3 言語切替 | 第9章 §9.13 | ユーザーフロー |

## 14.13 品質チェック

### 14.13.1 章末チェックリスト

- [x] §14.1 目的・スコープ明示（含む／含まない両方）
- [x] §14.1.4 設計原則 5 項目明示
- [x] §14.2 二言語ポリシー（`ja` 一次、`en` 空辞書）
- [x] §14.2.2 既定言語決定順序 5 段階
- [x] §14.3 命名規則（namespace.context.element.variant、最大 4 階層）
- [x] §14.3.2 名前空間 11 種類全揃う
- [x] §14.3.7 禁止事項（文末記号・動詞活用・番号付け）
- [x] §14.4 辞書ファイル配置と JSON フラット構造
- [x] §14.4.3 ネスト非採用の理由明示
- [x] §14.5 フォールバック解決順序 3 段階
- [x] §14.5.2 フォールバック時ログレベル表
- [x] §14.6 UI 実装規約（`data-i18n` / 属性翻訳 / `t()` / 言語切替）
- [x] §14.7 サーバー側 i18n（言語非依存原則）
- [x] §14.7.2 エラーメッセージの英語フォールバック方針
- [x] §14.7.5 alerts.message 日本語固定の判断明示
- [x] §14.8 変数埋込・複数形・改行・HTML エスケープ
- [x] §14.9 日時・数値・通貨・パーセントフォーマット
- [x] §14.10 翻訳キー一覧（11 カテゴリ、代表例揃う）
- [x] §14.10.7 `markov.*` が §8.20.5.1 と同期
- [x] §14.11 開発時規約（追加・削除・CI バリデーション）
- [x] §14.11.6 アクセシビリティ連携（`a11y.*`）
- [x] §14.12 相互参照表が新章番号で整合

### 14.13.2 一次レビュー観点（7 項目）

| # | 観点 | 判定 |
|---|------|------|
| 1 | 二言語ポリシー（§14.2） | ✅ 合格 |
| 2 | 命名規則・名前空間（§14.3、`a11y.*` 含む） | ✅ 合格 |
| 3 | 辞書構造・SSOT 統合経路（§14.4 / §14.7.4） | ✅ 合格 |
| 4 | フォールバック規則（§14.5） | ✅ 合格 |
| 5 | UI 実装規約・JS 無効時フォールバック（§14.6） | ✅ 合格 |
| 6 | サーバー i18n と §10.6.11（§14.7） | ✅ 合格 |
| 7 | `markov.*` と wait_reason 6 値（§14.10.7） | ✅ 合格 |

**一次レビュー**: 2026-05-27、マスター承認（配置 `5868d2c`）。

### 14.13.3 既知の未確定事項

- §14.8.2 複数形対応（ICU MessageFormat）は v1.1 検討、v1.0 は単数固定
- §14.9.3 通貨は USD 固定、JPY / EUR 対応は v1.1 検討
- §14.11.3 翻訳ツール連携（`po2json` / `lingui`）は v1.1 検討
- §14.11.4 CI バリデーション実装は PHASE 4 以降
- §14.10.8 `error.*` 全 50〜100 件は第18章で確定後に追加
- §14.7.5 `alerts.message` を「code 経由翻訳」に移行する判断は PHASE 7 以降

### 14.13.4 PHASE 引き継ぎ

- **PHASE 2（UI モック）**: `docs/mockups/shared/locales/ja.json` を本章の §14.10 代表例から拡張し作成、`en.json` は空 `{}` で配置、全 11 HTML に `data-i18n` 属性を埋込、`shared/i18n.js` で `t()` / `switchLanguage()` を実装
- **PHASE 3（コア実装）**: `src/yoruu/ui/locales/*.json` を SSOT として配置、`I18n` クラス（§10.11.5）を実装、`GET /api/v1/i18n/{lang}` を実装、エラーコード `error.*` を第18章確定に合わせて追加
- **PHASE 4（UI 実装）**: PHASE 2 のモック辞書を `src/yoruu/ui/locales/` に統合、CI バリデーション（§14.11.4）を導入、ARIA ラベル `a11y.*` を §8.22 と統合
- **PHASE 5（統合テスト）**: §14.13.2 の 7 観点を E2E テスト化、フォールバック動作・言語切替即時性・変数埋込を検証
- **PHASE 6（ペーパー運用）**: 日本語のみで運用、未使用キー検出・キー数モニタリング（§14.11.5）
- **PHASE 7 以降**: 英語翻訳着手、`en.json` 完成、複数形対応（§14.8.2）、CI バリデーション拡張
