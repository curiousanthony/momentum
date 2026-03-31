"""Interpret replayed metrics into a conservative home brief contract."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from aggregator.replay import ReplayResult


def build_insights(
    r: ReplayResult, projects: dict[str, dict[str, Any]], events: list[dict[str, Any]]
) -> dict[str, Any]:
    today = _parse_day(r.today_str)
    recent_days = _recent_days(r.active_days, today, 7)
    current_streak = _current_streak(r.active_days, today)
    recent_completed_sessions = _recent_completed_sessions(events, today, 7)
    recent_tests = _recent_successful_shells(events, today, 7, kind="test")
    recent_builds = _recent_successful_shells(events, today, 7, kind="build")
    active_projects_recent = _active_projects_recent(projects, today, 7)
    project_count = len(projects)
    recovery = _is_recovery_state(r.active_days, today, current_streak)

    signal_strength = _signal_strength(
        active_days_7d=len(recent_days),
        current_streak=current_streak,
        completed_sessions_7d=recent_completed_sessions,
        tests_7d=recent_tests,
        builds_7d=recent_builds,
    )
    consistency_level = _consistency_level(len(recent_days), current_streak)
    validation_level = _validation_level(recent_tests, recent_builds, recent_completed_sessions)
    project_momentum_level = _project_momentum_level(active_projects_recent, project_count)

    growth_key = _growth_direction_key(signal_strength, recovery)
    momentum_key = _momentum_key(signal_strength, recovery, current_streak)
    focus = _focus_signal(
        signal_strength=signal_strength,
        consistency_level=consistency_level,
        validation_level=validation_level,
        project_momentum_level=project_momentum_level,
    )

    evidence = _validation_evidence(
        active_days_7d=len(recent_days),
        current_streak=current_streak,
        completed_sessions=recent_completed_sessions,
        tests=recent_tests,
        builds=recent_builds,
        active_projects_recent=active_projects_recent,
    )
    proof_modules = evidence[:3]

    signals = {
        "consistency": {
            "level": consistency_level,
            "active_days_7d": len(recent_days),
            "current_streak": current_streak,
        },
        "recovery": {
            "status": "recovering" if recovery else "steady",
            "detected": recovery,
            "current_streak": current_streak,
        },
        "validation": {
            "level": validation_level,
            "tests_run": recent_tests,
            "builds_run": recent_builds,
            "completed_sessions": recent_completed_sessions,
        },
        "projectMomentum": {
            "level": project_momentum_level,
            "active_projects_7d": active_projects_recent,
            "tracked_projects": project_count,
        },
        "growthDirection": _growth_direction(growth_key),
        "focus": focus,
    }

    brief = {
        "confidence": signal_strength,
        "headline": _headline(growth_key),
        "summary": _summary(growth_key),
        "growth_direction": signals["growthDirection"],
        "validation": {
            "statement": _validation_statement(signal_strength, evidence),
            "evidence": evidence,
        },
        "momentum": _momentum(momentum_key, current_streak),
        "focus": focus,
        "proof_modules": proof_modules,
    }

    return {
        "signal_strength": signal_strength,
        "signals": signals,
        "brief": brief,
    }


def _parse_day(day_str: str) -> date:
    return datetime.fromisoformat(day_str).date()


def _recent_days(days: set[str], today: date, window: int) -> list[date]:
    out: list[date] = []
    floor = today - timedelta(days=window - 1)
    for day_str in days:
        day = datetime.fromisoformat(day_str).date()
        if floor <= day <= today:
            out.append(day)
    return sorted(out)


def _current_streak(days: set[str], today: date) -> int:
    if not days:
        return 0
    if today.isoformat() not in days:
        return 0
    current = today
    streak = 0
    while current.isoformat() in days:
        streak += 1
        current -= timedelta(days=1)
    return streak


def _is_recovery_state(days: set[str], today: date, current_streak: int) -> bool:
    if current_streak < 2 or not days or today.isoformat() not in days:
        return False
    streak_start = today - timedelta(days=current_streak - 1)
    previous_window_floor = streak_start - timedelta(days=7)
    recent_prior_days = []
    for day_str in days:
        day = datetime.fromisoformat(day_str).date()
        if previous_window_floor <= day < streak_start:
            recent_prior_days.append(day)
    return bool(recent_prior_days) and (streak_start - timedelta(days=1)).isoformat() not in days


def _active_projects_recent(projects: dict[str, dict[str, Any]], today: date, window: int) -> int:
    floor = today - timedelta(days=window - 1)
    count = 0
    for project in projects.values():
        last_active = project.get("last_active")
        if not isinstance(last_active, str):
            continue
        day = datetime.fromisoformat(last_active).date()
        if floor <= day <= today:
            count += 1
    return count


def _recent_completed_sessions(events: list[dict[str, Any]], today: date, window: int) -> int:
    floor = today - timedelta(days=window - 1)
    count = 0
    for event in events:
        if event.get("hook_event_name") != "sessionEnd":
            continue
        if event.get("reason") != "completed":
            continue
        ts = event.get("_ts")
        if not isinstance(ts, str) or len(ts) < 10:
            continue
        day = datetime.fromisoformat(ts[:10]).date()
        if floor <= day <= today:
            count += 1
    return count


def _recent_successful_shells(
    events: list[dict[str, Any]], today: date, window: int, *, kind: str
) -> int:
    floor = today - timedelta(days=window - 1)
    total = 0
    for event in events:
        if event.get("hook_event_name") != "afterShellExecution":
            continue
        if not _shell_success(event):
            continue
        command = str(event.get("command") or "")
        is_match = _is_test_command(command) if kind == "test" else _is_build_command(command)
        if not is_match:
            continue
        ts = event.get("_ts")
        if not isinstance(ts, str) or len(ts) < 10:
            continue
        day = datetime.fromisoformat(ts[:10]).date()
        if floor <= day <= today:
            total += 1
    return total


def _shell_success(event: dict[str, Any]) -> bool:
    if "exit_code" in event:
        return int(event["exit_code"]) == 0
    if "success" in event:
        return bool(event["success"])
    return True


def _is_test_command(cmd: str) -> bool:
    command = cmd.lower()
    return any(key in command for key in ("test", "pytest", "jest", "vitest", "cargo test"))


def _is_build_command(cmd: str) -> bool:
    command = cmd.lower()
    return any(
        key in command
        for key in ("build", "tsc", "webpack", "cargo build", "vite build", "npm run build")
    )


def _signal_strength(
    *,
    active_days_7d: int,
    current_streak: int,
    completed_sessions_7d: int,
    tests_7d: int,
    builds_7d: int,
) -> str:
    if (
        active_days_7d >= 4
        and current_streak >= 2
        and completed_sessions_7d >= 3
        and (tests_7d + builds_7d) >= 2
    ):
        return "high"
    if active_days_7d >= 3 and current_streak >= 1 and completed_sessions_7d >= 2:
        return "medium"
    return "low"


def _consistency_level(active_days_7d: int, current_streak: int) -> str:
    if active_days_7d >= 4 or current_streak >= 4:
        return "strong"
    if active_days_7d >= 2 or current_streak >= 2:
        return "emerging"
    return "limited"


def _validation_level(tests: int, builds: int, completed_sessions: int) -> str:
    if (tests + builds) >= 3 and completed_sessions >= 3:
        return "strong"
    if (tests + builds) >= 1 and completed_sessions >= 1:
        return "emerging"
    return "limited"


def _project_momentum_level(active_projects_recent: int, project_count: int) -> str:
    if active_projects_recent >= 2:
        return "broad"
    if active_projects_recent == 1 or project_count == 1:
        return "concentrated"
    return "limited"


def _growth_direction_key(signal_strength: str, recovery: bool) -> str:
    if signal_strength == "low":
        return "taking_shape"
    if recovery:
        return "recovery"
    return "steady_growth"


def _growth_direction(key: str) -> dict[str, str]:
    mapping = {
        "steady_growth": {"key": "steady_growth", "label": "Steady growth"},
        "recovery": {"key": "recovery", "label": "Recovery"},
        "taking_shape": {"key": "taking_shape", "label": "Taking shape"},
    }
    return mapping[key]


def _momentum_key(signal_strength: str, recovery: bool, current_streak: int) -> str:
    if signal_strength == "low":
        return "insufficient_signal"
    if recovery:
        return "recovery"
    if current_streak >= 3:
        return "momentum"
    return "baseline"


def _focus_signal(
    *,
    signal_strength: str,
    consistency_level: str,
    validation_level: str,
    project_momentum_level: str,
) -> dict[str, str] | None:
    if signal_strength == "low" or validation_level == "limited":
        return None
    if consistency_level != "strong":
        return {
            "key": "consistency",
            "label": "Protect a steadier weekly rhythm",
            "reason": "Cadence is emerging, but it still needs more repeat days before the pattern is durable.",
        }
    if project_momentum_level == "concentrated":
        return {
            "key": "project_follow_through",
            "label": "Keep pushing the work that is already moving",
            "reason": "Recent evidence is concentrated in one active project, so follow-through is the best next bet.",
        }
    return {
        "key": "reliability",
        "label": "Keep reinforcing repeatable workflows",
        "reason": "The strongest signals come from steady sessions plus successful build and test follow-through.",
    }


def _validation_evidence(
    *,
    active_days_7d: int,
    current_streak: int,
    completed_sessions: int,
    tests: int,
    builds: int,
    active_projects_recent: int,
) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    if active_days_7d > 0:
        evidence.append(
            {
                "key": "consistency",
                "label": "Recent active days",
                "value": str(active_days_7d),
                "detail": f"Active on {active_days_7d} of the last 7 days.",
            }
        )
    if current_streak > 0:
        evidence.append(
            {
                "key": "streak",
                "label": "Current streak",
                "value": str(current_streak),
                "detail": f"Current active-day streak is {current_streak}.",
            }
        )
    if completed_sessions > 0:
        evidence.append(
            {
                "key": "sessions",
                "label": "Completed sessions",
                "value": str(completed_sessions),
                "detail": f"{completed_sessions} sessions completed in the last 7 days.",
            }
        )
    if tests + builds > 0:
        build_label = "build" if builds == 1 else "builds"
        evidence.append(
            {
                "key": "reliability",
                "label": "Successful checks",
                "value": str(tests + builds),
                "detail": f"{tests} tests and {builds} {build_label} completed successfully in the last 7 days.",
            }
        )
    if active_projects_recent > 0:
        evidence.append(
            {
                "key": "projects",
                "label": "Active projects",
                "value": str(active_projects_recent),
                "detail": f"{active_projects_recent} projects showed recent activity.",
            }
        )
    return evidence[:4] or [
        {
            "key": "baseline",
            "label": "Recent usage",
            "value": "1",
            "detail": "Recent activity exists, but the pattern is still too thin for stronger interpretation.",
        }
    ]


def _headline(growth_key: str) -> str:
    return {
        "steady_growth": "Your workflow is getting steadier",
        "recovery": "You're back in motion",
        "taking_shape": "Momentum is still taking shape",
    }[growth_key]


def _summary(growth_key: str) -> str:
    return {
        "steady_growth": "Recent activity suggests consistent follow-through across meaningful coding work.",
        "recovery": "Recent sessions suggest healthy re-entry after a slower patch, with enough repeat activity to treat it as recovery.",
        "taking_shape": "There is recent activity, but not enough consistent evidence yet to draw a strong growth read.",
    }[growth_key]


def _validation_statement(signal_strength: str, evidence: list[dict[str, str]]) -> str:
    if signal_strength == "low":
        return "The clearest proof so far is recent usage, not a durable pattern yet."
    top_labels = ", ".join(item["label"].lower() for item in evidence[:2])
    return f"The strongest proof right now comes from {top_labels}."


def _momentum(momentum_key: str, current_streak: int) -> dict[str, str]:
    mapping = {
        "momentum": {
            "key": "momentum",
            "label": "Momentum looks stable",
            "detail": f"Recent cadence is holding, with a current streak of {current_streak} active days.",
        },
        "recovery": {
            "key": "recovery",
            "label": "This looks like recovery",
            "detail": "Recent activity resumed after a gap and now looks repeatable rather than one-off.",
        },
        "baseline": {
            "key": "baseline",
            "label": "A baseline pattern is forming",
            "detail": "There is enough activity to describe a direction, but the cadence is not fully stable yet.",
        },
        "insufficient_signal": {
            "key": "insufficient_signal",
            "label": "A clearer pattern should emerge with more history",
            "detail": "The product can observe recent usage, but not enough evidence yet to call momentum or recovery.",
        },
    }
    return mapping[momentum_key]
