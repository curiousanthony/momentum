"""Achievement catalog (spec §4) and unlock / progress evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aggregator.replay import ReplayResult, longest_daily_streak


@dataclass(frozen=True)
class AchievementDef:
    id: str
    name: str
    desc: str
    xp: int


CATALOG: list[AchievementDef] = [
    AchievementDef("first_edit", "Hello, World", "Make your first file edit", 50),
    AchievementDef("century_lines", "Century", "Write 100 lines in a single session", 75),
    AchievementDef("file_surgeon", "File Surgeon", "Edit 10 unique files in one session", 100),
    AchievementDef("polyglot", "Polyglot", "Edit files in 5 different languages", 150),
    AchievementDef("tab_master", "Tab Master", "Accept 50 Tab completions", 100),
    AchievementDef("tab_lord", "Tab Lord", "Accept 500 Tab completions", 300),
    AchievementDef("streak_3", "Hat Trick", "3-day active streak", 50),
    AchievementDef("streak_7", "Week Warrior", "7-day active streak", 150),
    AchievementDef("streak_30", "Unstoppable", "30-day active streak", 500),
    AchievementDef("night_owl", "Night Owl", "Start a session after midnight", 30),
    AchievementDef("early_bird", "Early Bird", "Start a session before 6am", 30),
    AchievementDef("marathon", "Marathon Coder", "Reach context compaction in a session", 75),
    AchievementDef("deep_thought", "Deep Thought", "Agent thinking time exceeds 60s in one block", 50),
    AchievementDef("loop_starter", "Loop Starter", "Complete an agent loop (loop_count > 0)", 30),
    AchievementDef("loop_5", "Full Cycle", "Reach loop_count 5 in a single stop", 100),
    AchievementDef("subagent_first", "Delegator", "Complete your first subagent task", 75),
    AchievementDef("subagent_10", "Manager", "Complete 10 subagent tasks", 200),
    AchievementDef("subagent_parallel", "Parallel Thinker", "Run 3 subagents in the same session", 150),
    AchievementDef("first_shell", "Shell Shock", "Run your first shell command", 20),
    AchievementDef("test_runner", "Test Runner", "Run a test suite 10 times", 75),
    AchievementDef("build_master", "Build Master", "Trigger 25 successful builds", 150),
    AchievementDef("mcp_explorer", "MCP Explorer", "Use an MCP tool for the first time", 50),
    AchievementDef("tool_addict", "Tool Addict", "Make 100 total tool calls", 100),
    AchievementDef("comeback", "Comeback Kid", "Follow an error session with a completed one", 40),
    AchievementDef("zero_errors", "Clean Slate", "7-day streak with no postToolUseFailure", 200),
    AchievementDef("multi_project", "Context Switcher", "Be active in 3 different projects in one day", 75),
    AchievementDef("project_veteran", "Project Veteran", "Accumulate 1000 XP in a single project", 100),
]

CATALOG_BY_ID: dict[str, AchievementDef] = {a.id: a for a in CATALOG}


def _get_int(lt: dict[str, int], key: str) -> int:
    return int(lt.get(key, 0))


def _current_streak_days(sorted_days: list[str], today_str: str) -> int:
    if not sorted_days:
        return 0
    day_set = set(sorted_days)
    start = today_str if today_str in day_set else sorted_days[-1]
    from datetime import datetime, timedelta

    d = datetime.fromisoformat(start).date()
    streak = 0
    while d.isoformat() in day_set:
        streak += 1
        d -= timedelta(days=1)
    return streak


def _clean_streak_days(
    failure_days: set[str], today_str: str, active_days: set[str]
) -> int:
    """Consecutive days from today backward with activity and no tool failure."""
    from datetime import datetime, timedelta

    if not active_days:
        return 0
    d = datetime.fromisoformat(today_str).date()
    streak = 0
    for _ in range(366):
        ds = d.isoformat()
        if ds in failure_days:
            break
        if ds not in active_days:
            break
        streak += 1
        d -= timedelta(days=1)
    return streak


def _seven_days_no_failure(
    failure_days: set[str], today_str: str, active_days: set[str]
) -> bool:
    from datetime import datetime, timedelta

    d = datetime.fromisoformat(today_str).date()
    for i in range(7):
        ds = (d - timedelta(days=i)).isoformat()
        if ds in failure_days:
            return False
        if ds not in active_days:
            return False
    return True


def _max_subagents_session(r: ReplayResult) -> int:
    return max(r.session_subagents_done.values(), default=0)


def _max_projects_in_one_day(r: ReplayResult) -> int:
    return max((len(p) for p in r.days_projects.values()), default=0)


def _check(
    a: AchievementDef,
    r: ReplayResult,
    sorted_days: list[str],
) -> tuple[bool, int, int]:
    lt = r.lifetime
    cur_streak = _current_streak_days(sorted_days, r.today_str)
    match a.id:
        case "first_edit":
            v = _get_int(lt, "files_edited")
            return (v >= 1, min(v, 1), 1)
        case "century_lines":
            v = r.max_lines_one_session
            return (v >= 100, min(v, 100), 100)
        case "file_surgeon":
            v = r.max_unique_files_one_session
            return (v >= 10, min(v, 10), 10)
        case "polyglot":
            v = len(r.seen_languages)
            return (v >= 5, min(v, 5), 5)
        case "tab_master":
            v = _get_int(lt, "tab_completions_accepted")
            return (v >= 50, min(v, 50), 50)
        case "tab_lord":
            v = _get_int(lt, "tab_completions_accepted")
            return (v >= 500, min(v, 500), 500)
        case "streak_3":
            return (cur_streak >= 3, min(cur_streak, 3), 3)
        case "streak_7":
            return (cur_streak >= 7, min(cur_streak, 7), 7)
        case "streak_30":
            return (cur_streak >= 30, min(cur_streak, 30), 30)
        case "night_owl":
            v = _get_int(lt, "night_owl_flag")
            return (v >= 1, min(v, 1), 1)
        case "early_bird":
            v = _get_int(lt, "early_bird_flag")
            return (v >= 1, min(v, 1), 1)
        case "marathon":
            v = _get_int(lt, "compactions_triggered")
            return (v >= 1, min(v, 1), 1)
        case "deep_thought":
            v = 1 if r.max_thought_ms >= 60_000 else 0
            return (v >= 1, min(v, 1), 1)
        case "loop_starter":
            v = _get_int(lt, "agent_loops_total")
            return (v >= 1, min(v, 1), 1)
        case "loop_5":
            v = r.max_loop_in_stop
            return (v >= 5, min(v, 5), 5)
        case "subagent_first":
            v = _get_int(lt, "subagents_completed")
            return (v >= 1, min(v, 1), 1)
        case "subagent_10":
            v = _get_int(lt, "subagents_completed")
            return (v >= 10, min(v, 10), 10)
        case "subagent_parallel":
            v = _max_subagents_session(r)
            return (v >= 3, min(v, 3), 3)
        case "first_shell":
            v = _get_int(lt, "commands_run")
            return (v >= 1, min(v, 1), 1)
        case "test_runner":
            v = _get_int(lt, "test_runs")
            return (v >= 10, min(v, 10), 10)
        case "build_master":
            v = _get_int(lt, "build_runs")
            return (v >= 25, min(v, 25), 25)
        case "mcp_explorer":
            v = 1 if r.mcp_used else 0
            return (v >= 1, min(v, 1), 1)
        case "tool_addict":
            v = _get_int(lt, "tool_calls_total")
            return (v >= 100, min(v, 100), 100)
        case "comeback":
            v = _get_int(lt, "comeback_unlock")
            return (v >= 1, min(v, 1), 1)
        case "zero_errors":
            ok = _seven_days_no_failure(r.failure_days, r.today_str, r.active_days)
            cs = _clean_streak_days(r.failure_days, r.today_str, r.active_days)
            return (ok, min(cs, 7), 7)
        case "multi_project":
            mp = _max_projects_in_one_day(r)
            return (mp >= 3, min(mp, 3), 3)
        case "project_veteran":
            best = max(r.project_xp.values(), default=0)
            return (best >= 1000, min(best, 1000), 1000)
        case _:
            return (False, 0, 1)


def evaluate_achievements(
    r: ReplayResult,
    already_unlocked_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    """New unlocks (not previously in state), in_progress, locked, xp from new unlocks."""
    sorted_days = sorted(r.active_days)
    new_unlocked: list[dict[str, Any]] = []
    in_progress: list[dict[str, Any]] = []
    locked: list[dict[str, Any]] = []
    xp_new = 0

    for a in CATALOG:
        if a.id in already_unlocked_ids:
            continue
        ok, prog, target = _check(a, r, sorted_days)
        if ok:
            new_unlocked.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "desc": a.desc,
                    "unlocked_at": "",
                    "xp_awarded": a.xp,
                }
            )
            xp_new += a.xp
        elif prog > 0:
            pct = int(min(100, (prog / target) * 100)) if target else 0
            in_progress.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "desc": a.desc,
                    "progress": prog,
                    "target": target,
                    "progress_pct": pct,
                }
            )
        else:
            locked.append({"id": a.id, "name": a.name})

    return new_unlocked, in_progress, locked, xp_new


def merge_unlock_timestamps(
    unlocked: list[dict[str, Any]],
    previous: dict[str, dict[str, Any]],
    now_iso: str,
) -> None:
    for u in unlocked:
        pid = u["id"]
        if pid in previous:
            u["unlocked_at"] = previous[pid].get("unlocked_at") or now_iso
            u["xp_awarded"] = previous[pid].get("xp_awarded", u.get("xp_awarded"))
            u["desc"] = previous[pid].get("desc", u.get("desc"))
        else:
            u["unlocked_at"] = now_iso
