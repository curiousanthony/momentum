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


def test_build_state_adds_high_confidence_editorial_brief():
    events = [
        _evt(hook_event_name="sessionStart", _ts="2026-03-28T09:00:00Z", session_id="d1", _project="app"),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-28T09:10:00Z",
            session_id="d1",
            _project="app",
            file_path="/x/app.ts",
            edits=[{"old_string": "", "new_string": "const a = 1;\nconst b = 2;\n"}],
        ),
        _evt(
            hook_event_name="afterShellExecution",
            _ts="2026-03-28T09:12:00Z",
            session_id="d1",
            _project="app",
            command="bun test",
            exit_code=0,
        ),
        _evt(
            hook_event_name="sessionEnd",
            _ts="2026-03-28T09:20:00Z",
            session_id="d1",
            _project="app",
            reason="completed",
        ),
        _evt(hook_event_name="sessionStart", _ts="2026-03-29T10:00:00Z", session_id="d2", _project="api"),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-29T10:05:00Z",
            session_id="d2",
            _project="api",
            file_path="/x/api.py",
            edits=[{"old_string": "", "new_string": "def run():\n    return True\n"}],
        ),
        _evt(
            hook_event_name="afterShellExecution",
            _ts="2026-03-29T10:10:00Z",
            session_id="d2",
            _project="api",
            command="pytest",
            exit_code=0,
        ),
        _evt(
            hook_event_name="sessionEnd",
            _ts="2026-03-29T10:20:00Z",
            session_id="d2",
            _project="api",
            reason="completed",
        ),
        _evt(hook_event_name="sessionStart", _ts="2026-03-30T11:00:00Z", session_id="d3", _project="app"),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-30T11:05:00Z",
            session_id="d3",
            _project="app",
            file_path="/x/feature.ts",
            edits=[{"old_string": "", "new_string": "export const feature = true;\n"}],
        ),
        _evt(
            hook_event_name="afterShellExecution",
            _ts="2026-03-30T11:10:00Z",
            session_id="d3",
            _project="app",
            command="npm run build",
            exit_code=0,
        ),
        _evt(
            hook_event_name="sessionEnd",
            _ts="2026-03-30T11:20:00Z",
            session_id="d3",
            _project="app",
            reason="completed",
        ),
        _evt(hook_event_name="sessionStart", _ts="2026-03-31T12:00:00Z", session_id="d4", _project="app"),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-31T12:05:00Z",
            session_id="d4",
            _project="app",
            file_path="/x/ui.ts",
            edits=[{"old_string": "", "new_string": "export const ready = true;\n"}],
        ),
        _evt(
            hook_event_name="afterShellExecution",
            _ts="2026-03-31T12:10:00Z",
            session_id="d4",
            _project="app",
            command="bun test",
            exit_code=0,
        ),
        _evt(
            hook_event_name="sessionEnd",
            _ts="2026-03-31T12:25:00Z",
            session_id="d4",
            _project="app",
            reason="completed",
        ),
    ]

    r = replay_events(events)
    r.today_str = "2026-03-31"
    state = build_state(r, events, {})

    insights = state["insights"]
    brief = insights["brief"]

    assert insights["signal_strength"] == "high"
    assert brief["confidence"] == "high"
    assert brief["growth_direction"]["key"] == "steady_growth"
    assert brief["momentum"]["key"] == "momentum"
    assert brief["focus"] is not None
    assert len(brief["validation"]["evidence"]) >= 2
    assert 1 <= len(brief["proof_modules"]) <= 3


def test_build_state_omits_focus_when_signal_is_weak():
    events = [
        _evt(hook_event_name="sessionStart", _ts="2026-03-31T12:00:00Z", session_id="s1"),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-31T12:05:00Z",
            session_id="s1",
            file_path="/x/a.ts",
            edits=[{"old_string": "", "new_string": "x\n"}],
        ),
    ]

    r = replay_events(events)
    r.today_str = "2026-03-31"
    state = build_state(r, events, {})

    insights = state["insights"]
    brief = insights["brief"]

    assert insights["signal_strength"] == "low"
    assert brief["confidence"] == "low"
    assert brief["growth_direction"]["key"] == "taking_shape"
    assert brief["momentum"]["key"] == "insufficient_signal"
    assert brief["focus"] is None
    assert len(brief["validation"]["evidence"]) >= 1


def test_build_state_does_not_promote_stale_history_to_high_confidence():
    events = [
        _evt(
            hook_event_name="sessionStart",
            _ts="2026-03-10T09:00:00Z",
            session_id="old1",
            _project="app",
        ),
        _evt(
            hook_event_name="afterShellExecution",
            _ts="2026-03-10T09:05:00Z",
            session_id="old1",
            _project="app",
            command="bun test",
            exit_code=0,
        ),
        _evt(
            hook_event_name="afterShellExecution",
            _ts="2026-03-10T09:06:00Z",
            session_id="old1",
            _project="app",
            command="npm run build",
            exit_code=0,
        ),
        _evt(
            hook_event_name="sessionEnd",
            _ts="2026-03-10T09:20:00Z",
            session_id="old1",
            _project="app",
            reason="completed",
        ),
        _evt(
            hook_event_name="sessionStart",
            _ts="2026-03-11T09:00:00Z",
            session_id="old2",
            _project="app",
        ),
        _evt(
            hook_event_name="afterShellExecution",
            _ts="2026-03-11T09:05:00Z",
            session_id="old2",
            _project="app",
            command="pytest",
            exit_code=0,
        ),
        _evt(
            hook_event_name="sessionEnd",
            _ts="2026-03-11T09:20:00Z",
            session_id="old2",
            _project="app",
            reason="completed",
        ),
        _evt(
            hook_event_name="sessionStart",
            _ts="2026-03-31T12:00:00Z",
            session_id="recent",
            _project="app",
        ),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-31T12:05:00Z",
            session_id="recent",
            _project="app",
            file_path="/x/a.ts",
            edits=[{"old_string": "", "new_string": "x\n"}],
        ),
    ]

    r = replay_events(events)
    r.today_str = "2026-03-31"
    state = build_state(r, events, {})

    insights = state["insights"]
    brief = insights["brief"]

    assert insights["signal_strength"] == "low"
    assert insights["signals"]["validation"]["level"] != "strong"
    assert brief["focus"] is None
    assert brief["momentum"]["key"] == "insufficient_signal"


def test_build_state_does_not_report_recovery_when_today_is_inactive():
    events = [
        _evt(hook_event_name="sessionStart", _ts="2026-03-24T10:00:00Z", session_id="a"),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-24T10:05:00Z",
            session_id="a",
            file_path="/x/a.ts",
            edits=[{"old_string": "", "new_string": "a\n"}],
        ),
        _evt(hook_event_name="sessionStart", _ts="2026-03-27T10:00:00Z", session_id="b"),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-27T10:05:00Z",
            session_id="b",
            file_path="/x/b.ts",
            edits=[{"old_string": "", "new_string": "b\n"}],
        ),
        _evt(hook_event_name="sessionStart", _ts="2026-03-28T10:00:00Z", session_id="c"),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-28T10:05:00Z",
            session_id="c",
            file_path="/x/c.ts",
            edits=[{"old_string": "", "new_string": "c\n"}],
        ),
    ]

    r = replay_events(events)
    r.today_str = "2026-03-31"
    state = build_state(r, events, {})

    insights = state["insights"]
    brief = insights["brief"]

    assert insights["signals"]["recovery"]["detected"] is False
    assert insights["signals"]["recovery"]["status"] != "recovering"
    assert brief["growth_direction"]["key"] != "recovery"
    assert brief["momentum"]["key"] != "recovery"


def test_build_state_keeps_low_confidence_states_internally_consistent():
    events = [
        _evt(
            hook_event_name="sessionStart",
            _ts="2026-03-20T09:00:00Z",
            session_id="old1",
            _project="app",
        ),
        _evt(
            hook_event_name="afterShellExecution",
            _ts="2026-03-20T09:05:00Z",
            session_id="old1",
            _project="app",
            command="bun test",
            exit_code=0,
        ),
        _evt(
            hook_event_name="sessionEnd",
            _ts="2026-03-20T09:20:00Z",
            session_id="old1",
            _project="app",
            reason="completed",
        ),
        _evt(
            hook_event_name="sessionStart",
            _ts="2026-03-31T12:00:00Z",
            session_id="recent",
            _project="app",
        ),
        _evt(
            hook_event_name="afterFileEdit",
            _ts="2026-03-31T12:05:00Z",
            session_id="recent",
            _project="app",
            file_path="/x/a.ts",
            edits=[{"old_string": "", "new_string": "x\n"}],
        ),
    ]

    r = replay_events(events)
    r.today_str = "2026-03-31"
    state = build_state(r, events, {})

    insights = state["insights"]
    brief = insights["brief"]

    assert insights["signal_strength"] == brief["confidence"] == "low"
    assert brief["growth_direction"]["key"] == "taking_shape"
    assert brief["momentum"]["key"] == "insufficient_signal"
    assert brief["focus"] is None


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
