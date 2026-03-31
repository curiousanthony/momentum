"""CLI: replay events.jsonl and write state.json."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from aggregator.replay import replay_events
from aggregator.state import build_state, load_events_jsonl, load_json


def main() -> int:
    default_dir = Path.home() / ".cursor/dashboard"
    events_path = Path(
        os.environ.get("CURSOR_DASHBOARD_EVENTS", str(default_dir / "events.jsonl"))
    )
    state_path = Path(os.environ.get("CURSOR_DASHBOARD_STATE", str(default_dir / "state.json")))

    events = load_events_jsonl(events_path)
    previous = load_json(state_path)
    r = replay_events(events)
    state = build_state(r, events, previous)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2))
    xp = state.get("xp") or {}
    print(f"[aggregate] Level {xp.get('level')} | {xp.get('total')} XP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
