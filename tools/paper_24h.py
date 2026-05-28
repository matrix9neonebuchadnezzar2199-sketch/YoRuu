#!/usr/bin/env python3
"""24h paper run harness (lab — shortened duration for CI)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="YoRuu paper loop harness")
    parser.add_argument("--config", type=Path, default=Path("config/yoruu.yaml"))
    parser.add_argument(
        "--hours",
        type=float,
        default=24.0,
        help="Target duration (lab: use small value in CI)",
    )
    parser.add_argument(
        "--interval-sec",
        type=int,
        default=300,
        help="Seconds between evaluate-once cycles",
    )
    args = parser.parse_args()

    deadline = time.time() + args.hours * 3600.0
    cycles = 0
    while time.time() < deadline:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "yoruu.cli",
                "paper",
                "evaluate-once",
                "--config",
                str(args.config),
            ],
            check=False,
        )
        if proc.returncode != 0:
            print(f"cycle {cycles} failed: exit {proc.returncode}", file=sys.stderr)
            return proc.returncode
        cycles += 1
        if time.time() >= deadline:
            break
        time.sleep(args.interval_sec)

    print(f"OK: {cycles} paper cycles in {args.hours}h window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
