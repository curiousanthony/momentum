"""Helpers for merging Cursor global hooks config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def merge_hook_config(existing: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "version": int(desired.get("version") or existing.get("version") or 1),
        "hooks": {},
    }

    existing_hooks = existing.get("hooks") if isinstance(existing.get("hooks"), dict) else {}
    desired_hooks = desired.get("hooks") if isinstance(desired.get("hooks"), dict) else {}

    for hook_name, hook_value in existing_hooks.items():
        if isinstance(hook_value, list):
            merged["hooks"][hook_name] = list(hook_value)

    for hook_name, hook_value in desired_hooks.items():
        current = merged["hooks"].setdefault(hook_name, [])
        if not isinstance(current, list):
            current = []
            merged["hooks"][hook_name] = current
        if not isinstance(hook_value, list):
            continue
        seen = {
            json.dumps(item, sort_keys=True)
            for item in current
            if isinstance(item, dict)
        }
        for item in hook_value:
            if not isinstance(item, dict):
                continue
            marker = json.dumps(item, sort_keys=True)
            if marker not in seen:
                current.append(item)
                seen.add(marker)

    return merged


def write_merged_hooks_file(example_path: Path, target_path: Path) -> None:
    desired = _load_json(example_path)
    existing = _load_json(target_path)
    merged = merge_hook_config(existing, desired)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(merged, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--example", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    write_merged_hooks_file(Path(args.example), Path(args.target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
