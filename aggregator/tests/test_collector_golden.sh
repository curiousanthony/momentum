#!/usr/bin/env bash
set -euo pipefail
if ! command -v jq >/dev/null 2>&1; then
  echo "skip: jq not installed"
  exit 0
fi
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
COLLECTOR="$ROOT/collector/collector.sh"
TMP="${TMPDIR:-/tmp}/cdash-test-$$"
mkdir -p "$TMP"
export CURSOR_DASHBOARD_LOG_DIR="$TMP"
export CURSOR_DASHBOARD_LOG_FILE="$TMP/events.jsonl"
unset CURSOR_DASHBOARD_AGGREGATE

FIXTURE='{"hook_event_name":"afterFileEdit","workspace_roots":["/Users/dev/my-app"],"session_id":"s1","file_path":"a.ts","edits":[{"old_string":"","new_string":"line\n"}]}'

echo "$FIXTURE" | bash "$COLLECTOR"

line=$(head -n1 "$TMP/events.jsonl")
echo "$line" | jq -e '._ts | test("^20[0-9]{2}-[0-9]{2}-[0-9]{2}T")' >/dev/null
echo "$line" | jq -e '._project == "my-app"' >/dev/null
echo "$line" | jq -e '.hook_event_name == "afterFileEdit"' >/dev/null

rm -rf "$TMP"
echo "ok collector golden"
