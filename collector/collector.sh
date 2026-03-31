#!/usr/bin/env bash
# Central event collector: read JSON from stdin, append one JSONL line with _ts and _project.
# Optional: trigger aggregator after sessionEnd or stop (background).

set -euo pipefail

LOG_DIR="${CURSOR_DASHBOARD_LOG_DIR:-$HOME/.cursor/dashboard}"
LOG_FILE="${CURSOR_DASHBOARD_LOG_FILE:-$LOG_DIR/events.jsonl}"
AGGREGATE_PY="${CURSOR_DASHBOARD_AGGREGATE:-$HOME/.cursor/dashboard/aggregate.py}"
RUNTIME_DIR="${CURSOR_DASHBOARD_RUNTIME_DIR:-$HOME/.cursor/dashboard}"

raw="$(cat || true)"
if [[ -z "${raw// }" ]]; then
  exit 0
fi

mkdir -p "$LOG_DIR"

RAW_PAYLOAD="$raw" python3 - "$LOG_FILE" "$AGGREGATE_PY" "$RUNTIME_DIR" <<'PY'
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

log_file = Path(sys.argv[1])
aggregate_py = Path(sys.argv[2])
runtime_dir = Path(sys.argv[3])
raw = __import__("os").environ.get("RAW_PAYLOAD", "")

try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    raise SystemExit(0)

roots = payload.get("workspace_roots") or []
if isinstance(roots, list) and roots:
    first_root = str(roots[0]).rstrip("/")
    project = first_root.split("/")[-1] if first_root else "unknown"
else:
    project = "unknown"

payload["_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
payload["_project"] = project or "unknown"

with log_file.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(payload, separators=(",", ":")) + "\n")

if aggregate_py.is_file():
    subprocess.Popen(
        [sys.executable, str(aggregate_py)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

if payload.get("hook_event_name") == "sessionStart":
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "aggregator.runtime",
            "maybe-open-on-session-start",
            "--runtime-dir",
            str(runtime_dir),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
PY

exit 0
