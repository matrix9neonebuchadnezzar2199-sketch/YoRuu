# 夜間レビュー自動化（Linux / VPS）

PHASE 6 M6.4 — systemd timer で `yoruu nightly generate` を毎日 04:00 に実行する。

## 手動確認

```bash
cd /path/to/YoRuu
chmod +x tools/nightly_run.sh
./tools/nightly_run.sh config/yoruu.yaml
```

## systemd ユニット例

`~/.config/systemd/user/yoruu-nightly.service`:

```ini
[Unit]
Description=YoRuu nightly report

[Service]
Type=oneshot
WorkingDirectory=/path/to/YoRuu
ExecStart=/path/to/YoRuu/tools/nightly_run.sh config/yoruu.yaml
```

`yoruu-nightly.timer`:

```ini
[Unit]
Description=YoRuu nightly timer

[Timer]
OnCalendar=*-*-* 04:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now yoruu-nightly.timer
systemctl --user list-timers yoruu-nightly.timer
```
