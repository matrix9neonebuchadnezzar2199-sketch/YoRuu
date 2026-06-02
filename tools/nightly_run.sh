#!/usr/bin/env bash
# YoRuu nightly report wrapper (PHASE 6 M6.4)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
CONFIG="${1:-config/yoruu.yaml}"
LOG_DIR="${LOG_DIR:-logs}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/nightly_run.log"
echo "[$(date -Iseconds)] start nightly generate" >>"$LOG_FILE"
uv run yoruu nightly generate --config "$CONFIG" >>"$LOG_FILE" 2>&1
code=$?
echo "[$(date -Iseconds)] exit=$code" >>"$LOG_FILE"
exit "$code"
