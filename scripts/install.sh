#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DASH="${HOME}/.cursor/dashboard"
HOOKS="${HOME}/.cursor/hooks"
HOOKS_JSON="${HOME}/.cursor/hooks.json"

echo "Installing Cursor Dashboard from ${ROOT}"

if [[ ! -d "${ROOT}/dashboard/dist" ]]; then
  echo "dashboard/dist missing. Run: cd dashboard && bun install && bun run build" >&2
  exit 1
fi

mkdir -p "${DASH}" "${HOOKS}"

cp "${ROOT}/collector/collector.sh" "${HOOKS}/collector.sh"
chmod +x "${HOOKS}/collector.sh"

cp -R "${ROOT}/dashboard/dist/." "${DASH}/"
rm -rf "${DASH}/aggregator"
cp -R "${ROOT}/aggregator" "${DASH}/aggregator"

AGG="${DASH}/aggregate.py"
cp "${ROOT}/aggregator/aggregate.py" "${AGG}"
chmod +x "${AGG}"

if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install -q -e "${DASH}/aggregator" --user 2>/dev/null || python3 -m pip install -q -e "${DASH}/aggregator"
  python3 "${ROOT}/aggregator/src/aggregator/hooks_config.py" \
    --example "${ROOT}/hooks.json.example" \
    --target "${HOOKS_JSON}"
fi

echo ""
echo "Done."
echo "1) Hooks activated in ${HOOKS_JSON}"
echo "2) Run aggregator: python3 ${AGG}"
echo "3) Serve dashboard: python3 -m http.server 7420 --directory ${DASH}"
echo "   Then open http://localhost:7420/"
echo ""
