"""XP rules and level curve (spec §3)."""

from __future__ import annotations

from typing import Final

# Event-sourced XP (aggregation layer), keyed for breakdown labels
XP_LINE_ADDED: Final = 1
XP_FILE_EDITED: Final = 5
XP_TAB_ACCEPTED: Final = 2
XP_SESSION_COMPLETED: Final = 20
XP_SESSION_ABORTED: Final = 2
XP_DAILY_LOGIN: Final = 10
XP_STREAK_BONUS_PER_DAY: Final = 15  # multiplied by streak length when streak >= 3
XP_COMMAND_RUN: Final = 3
XP_TEST_PASSED: Final = 10
XP_BUILD_SUCCEEDED: Final = 8
XP_AGENT_LOOP: Final = 10
XP_SUBAGENT_COMPLETED: Final = 15
XP_TOOL_CALL: Final = 2
XP_MCP_TOOL_CALL: Final = 5  # replaces base for MCP tools
XP_COMPACTION: Final = 25
XP_PROMPT_SUBMITTED: Final = 1
XP_NEW_LANGUAGE: Final = 30
XP_FIRST_EDIT_OF_DAY: Final = 5


def xp_for_level(n: int) -> int:
    """Total XP required to reach level n (n >= 1)."""
    if n < 1:
        return 0
    return int(100 * (n**1.5))


def level_from_xp(total_xp: int) -> int:
    """Current level for total lifetime XP (minimum level 1)."""
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    return level


def xp_progress_pct(total_xp: int, level: int) -> int:
    """Percent through current level toward next."""
    floor_xp = xp_for_level(level)
    ceil_xp = xp_for_level(level + 1)
    if ceil_xp <= floor_xp:
        return 0
    span = total_xp - floor_xp
    width = ceil_xp - floor_xp
    return int(max(0, min(100, (span / width) * 100)))
