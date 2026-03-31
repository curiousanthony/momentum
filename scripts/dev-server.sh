#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-7420}"
DIR="${HOME}/.cursor/dashboard"
exec python3 -m aggregator.runtime start --runtime-dir "${DIR}" --port "${PORT}"
