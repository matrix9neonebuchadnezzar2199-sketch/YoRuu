"""Atomic strategy.json writer (ch15 §15.8)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from yoruu.strategy.models import StrategyConfig


class StrategyWriter:
    """Write strategy.json with backup (apply flow)."""

    def __init__(self, strategy_path: Path) -> None:
        self._path = strategy_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> StrategyConfig:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return StrategyConfig.from_json_dict(data)

    def apply(self, config: StrategyConfig, *, backup_dir: Path | None = None) -> Path:
        if self._path.exists():
            backup_root = backup_dir or self._path.parent / "backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup_file = backup_root / f"strategy_v{config.version - 1}.json"
            backup_file.write_text(self._path.read_text(encoding="utf-8"), encoding="utf-8")

        payload = json.dumps(config.to_json_dict(), indent=2, ensure_ascii=False)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, self._path)
        return self._path
