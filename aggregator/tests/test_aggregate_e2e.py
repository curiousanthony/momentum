import json
from pathlib import Path

from aggregator.__main__ import main


def test_aggregate_cli_writes_state(tmp_path: Path, monkeypatch):
    ev = tmp_path / "events.jsonl"
    st = tmp_path / "state.json"
    ev.write_text(
        json.dumps(
            {
                "hook_event_name": "sessionStart",
                "_ts": "2026-03-30T10:00:00Z",
                "_project": "p",
                "session_id": "s1",
            }
        )
        + "\n"
        + json.dumps(
            {
                "hook_event_name": "afterFileEdit",
                "_ts": "2026-03-30T10:01:00Z",
                "_project": "p",
                "session_id": "s1",
                "file_path": "/a/b.ts",
                "edits": [{"old_string": "", "new_string": "hi\n"}],
            }
        )
        + "\n"
    )
    monkeypatch.setenv("CURSOR_DASHBOARD_EVENTS", str(ev))
    monkeypatch.setenv("CURSOR_DASHBOARD_STATE", str(st))
    assert main() == 0
    data = json.loads(st.read_text())
    assert data["xp"]["total"] > 0
    assert any(a["id"] == "first_edit" for a in data["achievements"]["unlocked"])
