import json
from pathlib import Path

from aggregator.replay import replay_events
from aggregator.state import build_state, load_events_jsonl


def _evt(**kwargs) -> dict:
    base = {"_ts": "2026-03-30T12:00:00Z", "_project": "demo", "session_id": "s1"}
    base.update(kwargs)
    return base


def test_replay_file_edit_and_daily_login():
    events = [
        _evt(hook_event_name="sessionStart", session_id="s1"),
        _evt(
            hook_event_name="afterFileEdit",
            file_path="/x/a.ts",
            edits=[{"old_string": "", "new_string": "a\nb\n"}],
        ),
    ]
    r = replay_events(events)
    assert r.lifetime["files_edited"] >= 1
    assert r.lifetime["lines_added"] >= 2


def test_build_state_roundtrip(tmp_path: Path):
    events = [
        _evt(hook_event_name="sessionStart"),
        _evt(
            hook_event_name="afterFileEdit",
            file_path="/x/a.ts",
            edits=[{"old_string": "", "new_string": "x\n"}],
        ),
    ]
    r = replay_events(events)
    state = build_state(r, events, {})
    assert state["xp"]["total"] > 0
    assert state["today"]["date"]


def test_build_state_includes_models_used():
    events = [
        _evt(hook_event_name="sessionStart", model="claude-sonnet-4"),
        _evt(
            hook_event_name="sessionStart",
            _ts="2026-03-30T13:00:00Z",
            session_id="s2",
            model="gpt-5",
        ),
        _evt(
            hook_event_name="sessionStart",
            _ts="2026-03-30T14:00:00Z",
            session_id="s3",
            model="claude-sonnet-4",
        ),
    ]

    r = replay_events(events)
    state = build_state(r, events, {})

    assert state["lifetime"]["models_used"] == {
        "claude-sonnet-4": 2,
        "gpt-5": 1,
    }


def test_events_jsonl_fixture(tmp_path: Path):
    p = tmp_path / "e.jsonl"
    p.write_text(
        json.dumps(
            {
                "hook_event_name": "sessionStart",
                "_ts": "2026-03-30T10:00:00Z",
                "_project": "p",
                "session_id": "a",
            }
        )
        + "\n"
    )
    assert len(load_events_jsonl(p)) == 1
