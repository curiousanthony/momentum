#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DASH="${HOME}/.cursor/dashboard"
HOOKS="${HOME}/.cursor/hooks"
HOOKS_JSON="${HOME}/.cursor/hooks.json"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "Installing Momentum from ${ROOT}"

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

if command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  "${PYTHON_BIN}" -m pip install -q -e "${DASH}/aggregator" --user 2>/dev/null || "${PYTHON_BIN}" -m pip install -q -e "${DASH}/aggregator"
  "${PYTHON_BIN}" "${ROOT}/aggregator/src/aggregator/hooks_config.py" \
    --example "${ROOT}/hooks.json.example" \
    --target "${HOOKS_JSON}"
  "${PYTHON_BIN}" "${AGG}"
  "${PYTHON_BIN}" -m aggregator.runtime register-startup --runtime-dir "${DASH}" >/dev/null
  "${PYTHON_BIN}" -m aggregator.runtime start --runtime-dir "${DASH}" >/dev/null
  "${PYTHON_BIN}" -m aggregator.runtime open-on-install --runtime-dir "${DASH}" >/dev/null
fi

echo ""
echo "Done."
echo "1) Hooks activated in ${HOOKS_JSON}"
echo "2) Aggregator bootstrapped: ${AGG}"
echo "3) Dashboard runtime registered and started from ${DASH}"
echo "4) Open the dashboard at the local URL reported by:"
echo "   ${PYTHON_BIN} -m aggregator.runtime status --runtime-dir ${DASH}"
echo ""
