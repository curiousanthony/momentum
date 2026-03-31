"""Single pass over hook events: lifetime metrics and XP from events (no achievements)."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aggregator import xp as xp_rules

LOG = logging.getLogger(__name__)

KNOWN_HOOKS = frozenset(
    {
        "sessionStart",
        "sessionEnd",
        "afterFileEdit",
        "afterTabFileEdit",
        "afterShellExecution",
        "postToolUse",
        "postToolUseFailure",
        "beforeSubmitPrompt",
        "preCompact",
        "afterAgentThought",
        "stop",
        "subagentStop",
    }
)


def _day(ts: str) -> str:
    return ts[:10] if ts and len(ts) >= 10 else ""


def _file_ext(path: str) -> str:
    return Path(path).suffix.lstrip(".").lower() or "unknown"


def _shell_success(event: dict[str, Any]) -> bool:
    if "exit_code" in event:
        return int(event["exit_code"]) == 0
    if "success" in event:
        return bool(event["success"])
    return True


def _is_test_command(cmd: str) -> bool:
    c = cmd.lower()
    return any(k in c for k in ("test", "pytest", "jest", "vitest", "cargo test"))


def _is_build_command(cmd: str) -> bool:
    c = cmd.lower()
    return any(k in c for k in ("build", "tsc", "webpack", "cargo build", "vite build", "npm run build"))


def _is_mcp_tool(name: str) -> bool:
    n = name.lower()
    return n.startswith("mcp") or n.startswith("mcp:")


@dataclass
class ReplayResult:
    lifetime: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    xp_breakdown: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    xp_from_events: int = 0
    xp_by_day: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    models_used: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    languages: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    projects: dict[str, dict[str, Any]] = field(
        default_factory=lambda: defaultdict(
            lambda: {"lines_added": 0, "files_edited": 0, "sessions": 0, "languages": defaultdict(int)}
        )
    )
    project_xp: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    project_last_day: dict[str, str] = field(default_factory=dict)
    active_days: set[str] = field(default_factory=set)
    sessions_by_day: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    days_projects: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    failure_days: set[str] = field(default_factory=set)
    login_days: set[str] = field(default_factory=set)
    first_edit_days: set[str] = field(default_factory=set)
    seen_languages: set[str] = field(default_factory=set)
    unique_files_ever: set[str] = field(default_factory=set)
    session_lines: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    session_files: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    session_exts: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    session_subagents_done: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    max_lines_one_session: int = 0
    max_unique_files_one_session: int = 0
    session_start_hour_utc: dict[str, int] = field(default_factory=dict)
    max_loop_in_stop: int = 0
    had_precompact: bool = False
    max_thought_ms: int = 0
    last_session_end_completed: bool | None = None
    mcp_used: bool = False
    today_str: str = ""
    recent_signal_events: list[dict[str, Any]] = field(default_factory=list)


def _add_xp(
    r: ReplayResult,
    amount: int,
    key: str,
    *,
    day: str,
    project: str,
) -> None:
    if amount == 0:
        return
    r.xp_from_events += amount
    r.xp_breakdown[key] += amount
    if day:
        r.xp_by_day[day] += amount
    if project:
        r.project_xp[project] += amount


def replay_events(events: list[dict[str, Any]]) -> ReplayResult:
    """Deterministic replay in `_ts` order."""
    sorted_events = sorted(
        events,
        key=lambda e: (e.get("_ts") or "", e.get("hook_event_name") or ""),
    )
    now = datetime.now(timezone.utc)
    r = ReplayResult(today_str=now.strftime("%Y-%m-%d"))

    for raw in sorted_events:
        ename = raw.get("hook_event_name")
        if not isinstance(ename, str):
            LOG.warning("event missing hook_event_name: %s", raw)
            continue
        if ename not in KNOWN_HOOKS:
            LOG.warning("unknown hook_event_name: %s", ename)

        ts = raw.get("_ts") or ""
        day = _day(ts)
        project = raw.get("_project") or "unknown"
        sid = raw.get("session_id") or "default"

        if day and project:
            cur = r.project_last_day.get(project, "")
            if not cur or day >= cur:
                r.project_last_day[project] = day

        if ename == "sessionStart":
            r.lifetime["sessions_started"] += 1
            r.projects[project]["sessions"] += 1
            if day:
                r.active_days.add(day)
                sess = raw.get("session_id") or ts
                r.sessions_by_day[day].add(str(sess))
                r.days_projects[day].add(project)
            if day and day not in r.login_days:
                r.login_days.add(day)
                _add_xp(
                    r,
                    xp_rules.XP_DAILY_LOGIN,
                    "daily_logins",
                    day=day,
                    project=project,
                )
            model = raw.get("model")
            if isinstance(model, str) and model:
                r.models_used[model] += 1
            if len(ts) >= 13:
                try:
                    h = int(ts[11:13])
                    r.session_start_hour_utc[sid] = h
                    # Early bird: 4–5 UTC; Night owl: 0–3 UTC (after midnight)
                    if 4 <= h < 6:
                        r.lifetime["early_bird_flag"] = 1
                    if 0 <= h < 4:
                        r.lifetime["night_owl_flag"] = 1
                except ValueError:
                    pass

        elif ename == "sessionEnd":
            prev_completed = r.last_session_end_completed
            reason = raw.get("reason", "")
            dur = int(raw.get("duration_ms") or 0)
            r.lifetime["total_session_duration_ms"] += dur
            if reason == "completed":
                r.lifetime["sessions_completed"] += 1
                _add_xp(
                    r,
                    xp_rules.XP_SESSION_COMPLETED,
                    "sessions_completed",
                    day=day,
                    project=project,
                )
                if prev_completed is False:
                    r.lifetime["comeback_unlock"] = 1
                r.last_session_end_completed = True
            else:
                r.lifetime["sessions_aborted"] += 1
                _add_xp(
                    r,
                    xp_rules.XP_SESSION_ABORTED,
                    "sessions_completed",
                    day=day,
                    project=project,
                )
                r.last_session_end_completed = False

        elif ename == "afterFileEdit":
            fp = raw.get("file_path") or ""
            ext = _file_ext(str(fp))
            added_session = 0
            for edit in raw.get("edits") or []:
                if not isinstance(edit, dict):
                    continue
                old_s = edit.get("old_string") or ""
                new_s = edit.get("new_string") or ""
                added = len(str(new_s).splitlines())
                removed = len(str(old_s).splitlines())
                r.lifetime["lines_added"] += added
                r.lifetime["lines_removed"] += removed
                r.languages[ext] += added
                r.projects[project]["languages"][ext] += added
                added_session += added
                r.projects[project]["lines_added"] += added
                line_xp = added * xp_rules.XP_LINE_ADDED
                _add_xp(r, line_xp, "lines_added", day=day, project=project)
            r.lifetime["files_edited"] += 1
            r.projects[project]["files_edited"] += 1
            if fp:
                r.unique_files_ever.add(str(fp))
                r.session_files[sid].add(str(fp))
            r.session_exts[sid].add(ext)
            r.session_lines[sid] += added_session
            r.max_lines_one_session = max(r.max_lines_one_session, r.session_lines[sid])
            mx = len(r.session_files[sid])
            r.max_unique_files_one_session = max(r.max_unique_files_one_session, mx)

            _add_xp(
                r,
                xp_rules.XP_FILE_EDITED,
                "files_edited",
                day=day,
                project=project,
            )
            if ext not in r.seen_languages:
                r.seen_languages.add(ext)
                _add_xp(
                    r,
                    xp_rules.XP_NEW_LANGUAGE,
                    "languages",
                    day=day,
                    project=project,
                )
            if day and day not in r.first_edit_days:
                r.first_edit_days.add(day)
                _add_xp(
                    r,
                    xp_rules.XP_FIRST_EDIT_OF_DAY,
                    "first_edits_day",
                    day=day,
                    project=project,
                )

        elif ename == "afterTabFileEdit":
            edits = raw.get("edits") or []
            n = len(edits) if isinstance(edits, list) else 0
            r.lifetime["tab_completions_accepted"] += n
            gain = n * xp_rules.XP_TAB_ACCEPTED
            _add_xp(r, gain, "tab_accepted", day=day, project=project)

        elif ename == "afterShellExecution":
            cmd = str(raw.get("command") or "")
            r.lifetime["commands_run"] += 1
            _add_xp(r, xp_rules.XP_COMMAND_RUN, "commands_run", day=day, project=project)
            ok = _shell_success(raw)
            if ok and _is_test_command(cmd):
                r.lifetime["test_runs"] += 1
                _add_xp(r, xp_rules.XP_TEST_PASSED, "test_passes", day=day, project=project)
            if ok and _is_build_command(cmd):
                r.lifetime["build_runs"] += 1
                _add_xp(r, xp_rules.XP_BUILD_SUCCEEDED, "build_successes", day=day, project=project)

        elif ename == "postToolUse":
            name = str(raw.get("tool_name") or "")
            r.lifetime["tool_calls_total"] += 1
            if _is_mcp_tool(name):
                r.mcp_used = True
                _add_xp(r, xp_rules.XP_MCP_TOOL_CALL, "tool_calls", day=day, project=project)
            else:
                _add_xp(r, xp_rules.XP_TOOL_CALL, "tool_calls", day=day, project=project)

        elif ename == "postToolUseFailure":
            r.lifetime["tool_calls_failed"] += 1
            if day:
                r.failure_days.add(day)

        elif ename == "stop":
            lc = int(raw.get("loop_count") or 0)
            if lc > 0:
                r.lifetime["agent_loops_total"] += lc
                _add_xp(
                    r,
                    lc * xp_rules.XP_AGENT_LOOP,
                    "agent_loops",
                    day=day,
                    project=project,
                )
                r.max_loop_in_stop = max(r.max_loop_in_stop, lc)

        elif ename == "subagentStop":
            if raw.get("status") == "completed":
                r.lifetime["subagents_completed"] += 1
                r.session_subagents_done[sid] += 1
                _add_xp(
                    r,
                    xp_rules.XP_SUBAGENT_COMPLETED,
                    "subagents_completed",
                    day=day,
                    project=project,
                )

        elif ename == "preCompact":
            r.lifetime["compactions_triggered"] += 1
            r.had_precompact = True
            _add_xp(r, xp_rules.XP_COMPACTION, "compactions", day=day, project=project)

        elif ename == "beforeSubmitPrompt":
            r.lifetime["prompts_submitted"] += 1
            _add_xp(
                r,
                xp_rules.XP_PROMPT_SUBMITTED,
                "prompts_submitted",
                day=day,
                project=project,
            )

        elif ename == "afterAgentThought":
            dm = int(raw.get("duration_ms") or 0)
            r.max_thought_ms = max(r.max_thought_ms, dm)

    # streak bonus (spec sample): current_streak * 15 when streak >= 3
    sorted_days = sorted(r.active_days)
    current_streak = _compute_current_streak(sorted_days, r.today_str)
    if current_streak >= 3:
        bonus = current_streak * xp_rules.XP_STREAK_BONUS_PER_DAY
        r.xp_from_events += bonus
        r.xp_breakdown["streak_bonuses"] += bonus

    # lifetime unique_files count
    r.lifetime["unique_files"] = len(r.unique_files_ever)

    return r


def _compute_current_streak(sorted_days: list[str], today_str: str) -> int:
    if not sorted_days:
        return 0
    day_set = set(sorted_days)
    start = today_str if today_str in day_set else sorted_days[-1]
    d = datetime.fromisoformat(start).date()
    streak = 0
    while d.isoformat() in day_set:
        streak += 1
        d = d - timedelta(days=1)
    return streak


def longest_daily_streak(sorted_days: list[str]) -> int:
    if not sorted_days:
        return 0
    best = 1
    cur = 1
    for i in range(1, len(sorted_days)):
        a = datetime.fromisoformat(sorted_days[i - 1]).date()
        b = datetime.fromisoformat(sorted_days[i]).date()
        if (b - a).days == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best
