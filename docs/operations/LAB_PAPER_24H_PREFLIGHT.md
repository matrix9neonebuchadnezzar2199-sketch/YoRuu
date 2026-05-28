# Lab 24h paper — pre-flight (M5.6)

**日付**: 2026-05-28  
**目的**: 本番 24h 実行前に CLI 引数・ハーネス動作を確認する。

## テンプレートとの整合

| テンプレート | 実装 (`cli.py` `paper-24h`) | 結果 |
|-------------|----------------------------|------|
| `--config config/yoruu.yaml` | `--config PATH`（既定 `config/yoruu.yaml`） | ✅ |
| `--hours 24` | `--hours FLOAT`（既定 24.0） | ✅ |
| `--interval-sec 300` | `--interval-sec INTEGER`（既定 300） | ✅ |
| — | `--max-cycles INTEGER`（lab smoke 用） | ✅ 追加オプション |

**推奨コマンド（本番）**:

```powershell
uv run yoruu paper-24h --config config/yoruu.yaml --hours 24 --interval-sec 300
```

**推奨コマンド（pre-flight / 数サイクルのみ）**:

```powershell
uv run yoruu paper-24h --config config/yoruu.yaml --hours 1 --interval-sec 1 --max-cycles 2
```

`--hours` はデッドライン（経過時間上限）。`--max-cycles` を付けるとサイクル数で早期終了する（24h 待たない）。

## 自動検証

- `uv run pytest tests/test_paper_24h_smoke.py -q` — **pass**（隔離 config、`--max-cycles 2`）

## 実装メモ

- 各サイクルは `yoruu paper evaluate-once --config <path>` を subprocess で実行。
- 非ゼロ exit で `paper-24h` 全体が終了。
- 成功時: `OK: N paper cycles` を stdout に出力。

## 本番前チェックリスト（マスター）

- [ ] `config/yoruu.yaml` 存在・`yoruu config validate` pass
- [ ] `yoruu db init` / migrate 済み
- [ ] lab VM 隔離・ログ/DB パス確保
- [ ] pre-flight: `--max-cycles 2` 以上で手動確認（任意）
- [ ] 24h 完了後 `LAB_PAPER_24H_TEMPLATE.md` を `LAB_PAPER_24H_YYYY-MM-DD.md` として保存
