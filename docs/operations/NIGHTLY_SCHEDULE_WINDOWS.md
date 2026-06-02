# 夜間レビュー自動化（Windows）

PHASE 6 M6.4 — OS タイマーで `yoruu nightly generate` を毎日 04:00 JST に実行する。

## 前提

- リポジトリルートで `uv sync` 済み
- `config/yoruu.yaml` が存在する

## 手動確認

```powershell
cd H:\CURSOR\YoRuu
.\tools\nightly_run.ps1 -Config config\yoruu.yaml
```

`logs/nightly_run.log` に exit 0、`reports/` に当日 JSON が生成されること。

## タスクスケジューラ登録（例）

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File H:\CURSOR\YoRuu\tools\nightly_run.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 4:00AM
Register-ScheduledTask -TaskName "YoRuu-Nightly" -Action $action -Trigger $trigger
```

登録後: `Get-ScheduledTask -TaskName YoRuu-Nightly | Get-ScheduledTaskInfo` で次回実行時刻を確認する。
