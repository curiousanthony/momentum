#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-7420}"
DIR="${HOME}/.cursor/dashboard"
exec python3 -m http.server "${PORT}" --directory "${DIR}"
