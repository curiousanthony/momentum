"""Assemble state.json and merge with previous run."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aggregator import achievements, xp as xp_rules
from aggregator.replay import ReplayResult, longest_daily_streak

RECENT_EVENTS_CAP = 50


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def load_events_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _sorted_days(r: ReplayResult) -> list[str]:
    return sorted(r.active_days)


def build_state(
    r: ReplayResult,
    events: list[dict[str, Any]],
    previous: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat().replace("+00:00", "Z")
    sorted_days = _sorted_days(r)

    prev_ach = previous.get("achievements") or {}
    prev_unlocked_list = list(prev_ach.get("unlocked") or [])
    for unlocked in prev_unlocked_list:
        aid = unlocked.get("id")
        if isinstance(aid, str):
            ach = achievements.CATALOG_BY_ID.get(aid)
            if ach and "desc" not in unlocked:
                unlocked["desc"] = ach.desc
    prev_by_id = {a["id"]: a for a in prev_unlocked_list if "id" in a}
    already_ids = set(prev_by_id.keys())

    new_unlocked, in_progress, locked, _xp_ach_new = achievements.evaluate_achievements(
        r, already_ids
    )
    achievements.merge_unlock_timestamps(new_unlocked, prev_by_id, now_iso)

    combined_unlocked = prev_unlocked_list + new_unlocked

    xp_achievement_total = sum(int(a.get("xp_awarded", 0)) for a in combined_unlocked)
    total_xp = r.xp_from_events + xp_achievement_total

    level = xp_rules.level_from_xp(total_xp)
    xp_floor = xp_rules.xp_for_level(level)
    xp_ceiling = xp_rules.xp_for_level(level + 1)
    xp_pct = xp_rules.xp_progress_pct(total_xp, level)

    breakdown = dict(r.xp_breakdown)
    breakdown["achievements"] = xp_achievement_total

    prev_level = int((previous.get("xp") or {}).get("level") or 1)
    prev_xp_total = int((previous.get("xp") or {}).get("total") or 0)

    recent = list(previous.get("recent_events") or [])
    for u in new_unlocked:
        recent.append(
            {
                "type": "achievement_unlocked",
                "id": u["id"],
                "ts": u.get("unlocked_at") or now_iso,
            }
        )
    if level > prev_level:
        recent.append({"type": "level_up", "level": level, "ts": now_iso})
    cur_streak = achievements._current_streak_days(sorted_days, r.today_str)
    prev_streak = int((previous.get("streaks") or {}).get("current_daily_streak") or 0)
    if cur_streak > prev_streak and cur_streak > 0:
        recent.append({"type": "streak_extended", "streak": cur_streak, "ts": now_iso})

    recent = recent[-RECENT_EVENTS_CAP:]

    lifetime_core = {k: int(v) for k, v in r.lifetime.items()}
    user_email = None
    cursor_ver = None
    for e in reversed(events):
        if user_email is None and e.get("user_email"):
            user_email = e.get("user_email")
        if cursor_ver is None and e.get("cursor_version"):
            cursor_ver = e.get("cursor_version")

    today_xp = int(r.xp_by_day.get(r.today_str, 0))

    projects_out: dict[str, Any] = {}
    for pname, pdata in r.projects.items():
        pxp = int(r.project_xp.get(pname, 0))
        langs = pdata.get("languages") or {}
        if hasattr(langs, "items"):
            lang_dict = dict(langs)
        else:
            lang_dict = {}
        projects_out[pname] = {
            "xp": pxp,
            "level": xp_rules.level_from_xp(pxp),
            "sessions": int(pdata.get("sessions", 0)),
            "lines_added": int(pdata.get("lines_added", 0)),
            "files_edited": int(pdata.get("files_edited", 0)),
            "languages": lang_dict,
            "last_active": r.project_last_day.get(pname),
        }

    today_sessions = len(r.sessions_by_day.get(r.today_str, set()))

    state: dict[str, Any] = {
        "user": {
            "email": user_email,
            "cursor_version": cursor_ver,
        },
        "xp": {
            "total": total_xp,
            "level": level,
            "xp_current_level": xp_floor,
            "xp_next_level": xp_ceiling,
            "xp_progress_pct": xp_pct,
            "breakdown": breakdown,
        },
        "streaks": {
            "current_daily_streak": cur_streak,
            "longest_daily_streak": longest_daily_streak(sorted_days),
            "last_active_date": sorted_days[-1] if sorted_days else None,
            "current_clean_streak": achievements._clean_streak_days(
                r.failure_days, r.today_str, r.active_days
            ),
        },
        "achievements": {
            "unlocked": combined_unlocked,
            "in_progress": in_progress,
            "locked": locked,
        },
        "lifetime": {
            **lifetime_core,
            "models_used": dict(r.models_used),
            "languages": dict(r.languages),
        },
        "today": {
            "date": r.today_str,
            "xp_earned": today_xp,
            "sessions": today_sessions,
            "lines_added": _today_lines(events, r.today_str),
            "tab_completions": _today_tab_edits(events, r.today_str),
            "commands_run": _today_hook_count(events, r.today_str, "afterShellExecution"),
            "tool_calls": _today_hook_count(events, r.today_str, "postToolUse"),
            "active_projects": list(r.days_projects.get(r.today_str, [])),
        },
        "projects": projects_out,
        "recent_events": recent,
        "last_aggregated_at": now_iso,
    }

    return state


def _day(ts: str) -> str:
    return ts[:10] if ts and len(ts) >= 10 else ""


def _today_lines(events: list[dict[str, Any]], today: str) -> int:
    n = 0
    for e in events:
        if e.get("hook_event_name") != "afterFileEdit":
            continue
        if _day(e.get("_ts") or "") != today:
            continue
        for ed in e.get("edits") or []:
            if isinstance(ed, dict):
                n += len(str(ed.get("new_string") or "").splitlines())
    return n


def _today_tab_edits(events: list[dict[str, Any]], today: str) -> int:
    n = 0
    for e in events:
        if e.get("hook_event_name") != "afterTabFileEdit":
            continue
        if _day(e.get("_ts") or "") != today:
            continue
        n += len(e.get("edits") or [])
    return n


def _today_hook_count(events: list[dict[str, Any]], today: str, hook: str) -> int:
    return sum(
        1
        for e in events
        if e.get("hook_event_name") == hook and _day(e.get("_ts") or "") == today
    )
