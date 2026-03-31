#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DASH="${HOME}/.cursor/dashboard"
HOOKS="${HOME}/.cursor/hooks"
HOOKS_JSON="${HOME}/.cursor/hooks.json"
PYTHON_BIN="${PYTHON_BIN:-python3}"
INSTALL_CHANNEL="stable"
INSTALL_VERSION="${MOMENTUM_INSTALL_VERSION:-dev}"
INSTALL_COMMIT_SHA="${MOMENTUM_INSTALL_COMMIT_SHA:-}"
UPDATE_MANIFEST_URL="${MOMENTUM_UPDATE_MANIFEST_URL:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dev-local)
      INSTALL_CHANNEL="dev-local"
      INSTALL_VERSION="dev"
      INSTALL_COMMIT_SHA=""
      shift
      ;;
    --stable-version)
      INSTALL_VERSION="$2"
      shift 2
      ;;
    --commit-sha)
      INSTALL_COMMIT_SHA="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${INSTALL_COMMIT_SHA}" ]] && command -v git >/dev/null 2>&1; then
  INSTALL_COMMIT_SHA="$(git -C "${ROOT}" rev-parse HEAD 2>/dev/null || true)"
fi

if [[ -z "${UPDATE_MANIFEST_URL}" ]] && [[ -f "${ROOT}/version.json" ]]; then
  UPDATE_MANIFEST_URL="$(ROOT="${ROOT}" "${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["ROOT"]) / "version.json"
payload = json.loads(path.read_text())
print(payload.get("manifest_url", ""))
PY
)"
fi

if [[ -z "${UPDATE_MANIFEST_URL}" ]] && command -v git >/dev/null 2>&1; then
  REMOTE_URL="$(git -C "${ROOT}" remote get-url origin 2>/dev/null || true)"
  if [[ "${REMOTE_URL}" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    UPDATE_MANIFEST_URL="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}/releases/latest/download/stable.json"
  fi
fi

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
  INSTALL_VERSION="${INSTALL_VERSION}" \
    INSTALL_CHANNEL="${INSTALL_CHANNEL}" \
    INSTALL_COMMIT_SHA="${INSTALL_COMMIT_SHA}" \
    UPDATE_MANIFEST_URL="${UPDATE_MANIFEST_URL}" \
    DASH="${DASH}" \
    PYTHONPATH="${DASH}/aggregator/src${PYTHONPATH:+:${PYTHONPATH}}" \
    "${PYTHON_BIN}" - <<'PY'
from aggregator.runtime import RuntimeConfig, load_runtime_config, save_runtime_config
import os
from pathlib import Path

runtime_dir = Path(os.environ["DASH"])
config = load_runtime_config(runtime_dir)
save_runtime_config(
    RuntimeConfig(
        port=config.port,
        open_on_cursor_start=config.open_on_cursor_start,
        first_install_open_completed=config.first_install_open_completed,
        platform_registration=config.platform_registration,
        update_manifest_url=os.environ.get("UPDATE_MANIFEST_URL") or None,
    ),
    runtime_dir,
)
PY
  INSTALL_VERSION="${INSTALL_VERSION}" \
    INSTALL_CHANNEL="${INSTALL_CHANNEL}" \
    INSTALL_COMMIT_SHA="${INSTALL_COMMIT_SHA}" \
    DASH="${DASH}" \
    PYTHONPATH="${DASH}/aggregator/src${PYTHONPATH:+:${PYTHONPATH}}" \
    "${PYTHON_BIN}" - <<'PY'
from aggregator.runtime import save_installed_version
import os
from pathlib import Path

save_installed_version(
    version=os.environ["INSTALL_VERSION"],
    channel=os.environ["INSTALL_CHANNEL"],
    commit_sha=os.environ.get("INSTALL_COMMIT_SHA") or None,
    runtime_dir=Path(os.environ["DASH"]),
)
PY
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
echo "5) Install channel: ${INSTALL_CHANNEL} (${INSTALL_VERSION})"
echo ""
