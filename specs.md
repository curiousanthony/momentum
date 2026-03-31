# Momentum: Achievements + XP/Leveling System

Here is a full design covering data collection, schema, scoring logic, and dashboard structure.

## 1. Hook-to-Metric Mapping

Here is exactly which hooks feed which game systems and which fields you extract:

| Hook                  | Fields used                                                                   | What it feeds                                |
| --------------------- | ----------------------------------------------------------------------------- | -------------------------------------------- |
| `sessionStart`        | `session_id`, `composer_mode`, `is_background_agent`, `model`                 | Session streak, daily activity               |
| `sessionEnd`          | `duration_ms`, `reason`, `final_status`                                       | Session XP, completion rate                  |
| `afterFileEdit`       | `file_path`, `edits[].old_string`, `edits[].new_string`                       | Lines changed, files touched, language stats |
| `afterTabFileEdit`    | `file_path`, `edits[].range`, `edits[].old_line`, `edits[].new_line`          | Tab acceptance count, inline edit precision  |
| `afterShellExecution` | `command`, `output`, `duration`                                               | Commands run, build time, test runs          |
| `postToolUse`         | `tool_name`, `duration`, `tool_output`                                        | Tool usage leaderboard, total tool calls     |
| `postToolUseFailure`  | `failure_type`, `error_message`, `is_interrupt`                               | Error tracking, "fragile streak" mechanic    |
| `stop`                | `status`, `loop_count`                                                        | Session complexity score, completion XP      |
| `subagentStop`        | `tool_call_count`, `message_count`, `duration_ms`, `modified_files`, `status` | "Deep work" score, subagent achievements     |
| `beforeSubmitPrompt`  | `prompt`                                                                      | Prompt count, prompt length milestones       |
| `preCompact`          | `context_tokens`, `context_usage_percent`, `message_count`                    | "Marathon session" achievement               |
| `afterAgentThought`   | `duration_ms`                                                                 | Reasoning time metric                        |

## 2. The Hook Collector Script

A single script handles all hooks, routes by hook_event_name, and appends structured events to a JSONL file.

```json
~/.cursor/hooks.json (global, cross-project)

{
"version": 1,
"hooks": {
"sessionStart": [{ "command": "~/.cursor/hooks/collector.sh" }],
"sessionEnd": [{ "command": "~/.cursor/hooks/collector.sh" }],
"afterFileEdit": [{ "command": "~/.cursor/hooks/collector.sh" }],
"afterTabFileEdit": [{ "command": "~/.cursor/hooks/collector.sh" }],
"afterShellExecution": [{ "command": "~/.cursor/hooks/collector.sh" }],
"postToolUse": [{ "command": "~/.cursor/hooks/collector.sh" }],
"postToolUseFailure": [{ "command": "~/.cursor/hooks/collector.sh" }],
"beforeSubmitPrompt": [{ "command": "~/.cursor/hooks/collector.sh" }],
"preCompact": [{ "command": "~/.cursor/hooks/collector.sh" }],
"afterAgentThought": [{ "command": "~/.cursor/hooks/collector.sh" }],
"stop": [{ "command": "~/.cursor/hooks/collector.sh" }],
"subagentStop": [{ "command": "~/.cursor/hooks/collector.sh" }]
}
}
```

```sh
~/.cursor/hooks/collector.sh

#!/bin/bash

# ============================================================

# collector.sh - Central event collector for the XP dashboard

#

# All hooks pipe through here. We read the JSON payload,

# enrich it with a timestamp and the project name derived

# from workspace_roots, then append to a JSONL event log.

#

# Output: ~/.cursor/dashboard/events.jsonl

# ============================================================

raw=$(cat)
LOG_DIR="$HOME/.cursor/dashboard"
LOG_FILE="$LOG_DIR/events.jsonl"
mkdir -p "$LOG_DIR"

# Derive a short project name from the first workspace root

# e.g. "/home/user/projects/my-app" -> "my-app"

project=$(echo "$raw" | jq -r '
(.workspace_roots[0] // "unknown") | split("/") | last
')

# Enrich the raw event with two extra fields:

# \_ts : ISO timestamp of when we received it

# \_project : short project folder name

echo "$raw" | jq -c \
  --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
 --arg project "$project" \
 '. + {\_ts: $ts, \_project: $project}' \

> > "$LOG_FILE"
> > exit 0
```

```sh
chmod +x ~/.cursor/hooks/collector.sh 3. XP Scoring Rules
```

These are the point values you assign during aggregation (in your backend or a nightly script). Not in the hook itself - the hook just records raw facts.

```js
// xp-rules.js (reference table for your aggregation layer)
const XP_RULES = {
	// --- File editing ---
	linesAdded: { xp: 1, per: "line" }, // net new lines written
	fileEdited: { xp: 5, per: "file" }, // unique file touched in a session
	tabAccepted: { xp: 2, per: "edit" }, // afterTabFileEdit fired
	// --- Sessions ---
	sessionCompleted: { xp: 20, per: "session" }, // sessionEnd reason=completed
	sessionAborted: { xp: 2, per: "session" }, // partial credit
	dailyLogin: { xp: 10, per: "day" }, // first session of the day
	streakBonus: { xp: 15, per: "day" }, // active N days in a row (multiplier)
	// --- Shell usage ---
	commandRun: { xp: 3, per: "command" },
	testPassed: { xp: 10, per: "run" }, // command contains "test" + exit 0
	buildSucceeded: { xp: 8, per: "run" }, // command contains "build" + exit 0
	// --- Agent depth ---
	agentLoopCompleted: { xp: 10, per: "loop" }, // stop.loop_count > 0
	subagentCompleted: { xp: 15, per: "subagent" }, // subagentStop.status=completed
	promptSubmitted: { xp: 1, per: "prompt" },
	// --- Tool usage ---
	toolCallMade: { xp: 2, per: "call" }, // postToolUse
	mcpToolUsed: { xp: 5, per: "call" }, // tool_name starts with MCP:
	// --- Context depth ---
	compactionReached: { xp: 25, per: "event" }, // preCompact fired (marathon session)
	// --- Bonuses ---
	firstEditOfDay: { xp: 5, per: "day" },
	newLanguageUnlocked: { xp: 30, per: "language" }, // first time editing a new extension
}
```

### Level Curve

Use a classic RPG square-root curve so early levels feel fast and later ones require real work:

`XP required to reach level N = 100 \* N^1.5`

`Level 1: 100 XP`
`Level 5: 1,118 XP`
`Level 10: 3,162 XP`
`Level 20: 8,944 XP`
`Level 50: 35,355 XP`

```py
import math
def xp_for_level(n):
return int(100 \* (n \*\* 1.5))
def level_from_xp(total_xp):
level = 1
while xp_for_level(level + 1) <= total_xp:
level += 1
return level
```

## 4. Achievements Catalog

Each achievement has a unique id, a trigger condition mapped to hook data, and an XP reward on unlock.

```json
[
	// ── EDITING ────────────────────────────────────────────────
	{
		"id": "first_edit",
		"name": "Hello, World",
		"desc": "Make your first file edit",
		"xp": 50
	},
	{
		"id": "century_lines",
		"name": "Century",
		"desc": "Write 100 lines in a single session",
		"xp": 75
	},
	{
		"id": "file_surgeon",
		"name": "File Surgeon",
		"desc": "Edit 10 unique files in one session",
		"xp": 100
	},
	{
		"id": "polyglot",
		"name": "Polyglot",
		"desc": "Edit files in 5 different languages",
		"xp": 150
	},
	{
		"id": "tab_master",
		"name": "Tab Master",
		"desc": "Accept 50 Tab completions",
		"xp": 100
	},
	{
		"id": "tab_lord",
		"name": "Tab Lord",
		"desc": "Accept 500 Tab completions",
		"xp": 300
	},
	// ── SESSIONS ────────────────────────────────────────────────
	{
		"id": "streak_3",
		"name": "Hat Trick",
		"desc": "3-day active streak",
		"xp": 50
	},
	{
		"id": "streak_7",
		"name": "Week Warrior",
		"desc": "7-day active streak",
		"xp": 150
	},
	{
		"id": "streak_30",
		"name": "Unstoppable",
		"desc": "30-day active streak",
		"xp": 500
	},
	{
		"id": "night_owl",
		"name": "Night Owl",
		"desc": "Start a session after midnight",
		"xp": 30
	},
	{
		"id": "early_bird",
		"name": "Early Bird",
		"desc": "Start a session before 6am",
		"xp": 30
	},
	{
		"id": "marathon",
		"name": "Marathon Coder",
		"desc": "Reach context compaction in a session",
		"xp": 75
	},
	{
		"id": "deep_thought",
		"name": "Deep Thought",
		"desc": "Agent thinking time exceeds 60s in one block",
		"xp": 50
	},
	// ── AGENT DEPTH ─────────────────────────────────────────────
	{
		"id": "loop_starter",
		"name": "Loop Starter",
		"desc": "Complete an agent loop (loop_count > 0)",
		"xp": 30
	},
	{
		"id": "loop_5",
		"name": "Full Cycle",
		"desc": "Reach loop_count 5 in a single stop",
		"xp": 100
	},
	{
		"id": "subagent_first",
		"name": "Delegator",
		"desc": "Complete your first subagent task",
		"xp": 75
	},
	{
		"id": "subagent_10",
		"name": "Manager",
		"desc": "Complete 10 subagent tasks",
		"xp": 200
	},
	{
		"id": "subagent_parallel",
		"name": "Parallel Thinker",
		"desc": "Run 3 subagents in the same session",
		"xp": 150
	},
	// ── SHELL / TOOLS ───────────────────────────────────────────
	{
		"id": "first_shell",
		"name": "Shell Shock",
		"desc": "Run your first shell command",
		"xp": 20
	},
	{
		"id": "test_runner",
		"name": "Test Runner",
		"desc": "Run a test suite 10 times",
		"xp": 75
	},
	{
		"id": "build_master",
		"name": "Build Master",
		"desc": "Trigger 25 successful builds",
		"xp": 150
	},
	{
		"id": "mcp_explorer",
		"name": "MCP Explorer",
		"desc": "Use an MCP tool for the first time",
		"xp": 50
	},
	{
		"id": "tool_addict",
		"name": "Tool Addict",
		"desc": "Make 100 total tool calls",
		"xp": 100
	},
	// ── RECOVERY ────────────────────────────────────────────────
	{
		"id": "comeback",
		"name": "Comeback Kid",
		"desc": "Follow an error session with a completed one",
		"xp": 40
	},
	{
		"id": "zero_errors",
		"name": "Clean Slate",
		"desc": "7-day streak with no postToolUseFailure",
		"xp": 200
	},
	// ── PROJECTS ────────────────────────────────────────────────
	{
		"id": "multi_project",
		"name": "Context Switcher",
		"desc": "Be active in 3 different projects in one day",
		"xp": 75
	},
	{
		"id": "project_veteran",
		"name": "Project Veteran",
		"desc": "Accumulate 1000 XP in a single project",
		"xp": 100
	}
]
```

## 5. Aggregated Data Schema

The aggregation layer (a script or small server) reads events.jsonl and writes state.json. This is what the dashboard reads.

```json
// ~/.cursor/dashboard/state.json
{
	"user": {
		"email": "you@example.com",
		"cursor_version": "1.7.2"
	},

	// ── XP & LEVELING ──────────────────────────────────────────
	"xp": {
		"total": 4821,
		"level": 12,
		"xp_current_level": 4821, // total XP earned at this level's floor
		"xp_next_level": 5627, // total XP needed to reach level 13
		"xp_progress_pct": 64, // percentage through current level
		"breakdown": {
			// where XP came from, all time
			"lines_added": 1200,
			"files_edited": 450,
			"tab_accepted": 300,
			"sessions_completed": 600,
			"daily_logins": 210,
			"streak_bonuses": 225,
			"commands_run": 180,
			"test_passes": 220,
			"build_successes": 176,
			"agent_loops": 340,
			"subagents_completed": 420,
			"tool_calls": 300,
			"compactions": 100,
			"prompts_submitted": 100
		}
	},

	// ── STREAKS ────────────────────────────────────────────────
	"streaks": {
		"current_daily_streak": 9, // consecutive active days
		"longest_daily_streak": 23,
		"last_active_date": "2025-07-10",
		"current_clean_streak": 4 // days without postToolUseFailure
	},

	// ── ACHIEVEMENTS ───────────────────────────────────────────
	"achievements": {
		"unlocked": [
			{
				"id": "first_edit",
				"name": "Hello, World",
				"unlocked_at": "2025-06-01T09:14:00Z",
				"xp_awarded": 50
			},
			{
				"id": "tab_master",
				"name": "Tab Master",
				"unlocked_at": "2025-06-15T14:30:00Z",
				"xp_awarded": 100
			}
		],
		"in_progress": [
			{
				"id": "tab_lord",
				"name": "Tab Lord",
				"desc": "Accept 500 Tab completions",
				"progress": 312,
				"target": 500,
				"progress_pct": 62
			},
			{
				"id": "streak_30",
				"name": "Unstoppable",
				"desc": "30-day active streak",
				"progress": 9,
				"target": 30,
				"progress_pct": 30
			}
		],
		"locked": [
			{ "id": "subagent_parallel", "name": "Parallel Thinker" },
			{ "id": "zero_errors", "name": "Clean Slate" }
		]
	},

	// ── LIFETIME STATS ─────────────────────────────────────────
	"lifetime": {
		"sessions_started": 142,
		"sessions_completed": 128,
		"sessions_aborted": 14,
		"total_session_duration_ms": 18400000,
		"prompts_submitted": 834,
		"lines_added": 12430,
		"lines_removed": 4210,
		"files_edited": 389,
		"unique_files": 204,
		"tab_completions_accepted": 312,
		"commands_run": 601,
		"test_runs": 88,
		"build_runs": 73,
		"tool_calls_total": 1502,
		"tool_calls_failed": 39,
		"agent_loops_total": 67,
		"subagents_completed": 28,
		"compactions_triggered": 4,
		"models_used": {
			"claude-sonnet-4-20250514": 98,
			"gpt-4o": 44
		},
		"languages": {
			"ts": 180,
			"py": 95,
			"go": 44,
			"css": 22,
			"sh": 18
		}
	},

	// ── TODAY ──────────────────────────────────────────────────
	"today": {
		"date": "2025-07-10",
		"xp_earned": 185,
		"sessions": 3,
		"lines_added": 220,
		"tab_completions": 18,
		"commands_run": 12,
		"tool_calls": 34,
		"active_projects": ["my-app", "api-server"]
	},

	// ── PER-PROJECT ────────────────────────────────────────────
	"projects": {
		"my-app": {
			"xp": 2910,
			"level": 9,
			"sessions": 84,
			"lines_added": 7300,
			"files_edited": 210,
			"languages": { "ts": 140, "css": 18 },
			"last_active": "2025-07-10"
		},
		"api-server": {
			"xp": 1911,
			"level": 7,
			"sessions": 58,
			"lines_added": 5130,
			"files_edited": 179,
			"languages": { "py": 95, "sh": 18 },
			"last_active": "2025-07-09"
		}
	},

	// ── RECENT EVENTS (feed for dashboard activity log) ────────
	"recent_events": [
		{
			"type": "achievement_unlocked",
			"id": "tab_master",
			"ts": "2025-07-10T14:30:00Z"
		},
		{ "type": "level_up", "level": 12, "ts": "2025-07-10T12:10:00Z" },
		{
			"type": "xp_earned",
			"amount": 25,
			"reason": "subagentCompleted",
			"ts": "2025-07-10T11:55:00Z"
		},
		{ "type": "streak_extended", "streak": 9, "ts": "2025-07-10T09:00:00Z" }
	],

	"last_aggregated_at": "2025-07-10T15:00:00Z"
}
```

## 6. The Aggregator Script

This runs after events.jsonl is populated and writes state.json. Run it on a schedule (cron, or triggered by your sessionEnd hook).

```py
#!/usr/bin/env python3
# ~/.cursor/dashboard/aggregate.py
#
# Reads:   ~/.cursor/dashboard/events.jsonl
# Writes:  ~/.cursor/dashboard/state.json
#
# Run manually:  python3 aggregate.py
# Or via cron:   */15 * * * * python3 ~/.cursor/dashboard/aggregate.py
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
EVENTS_FILE = Path.home() / ".cursor/dashboard/events.jsonl"
STATE_FILE  = Path.home() / ".cursor/dashboard/state.json"
# ── XP Rules ───────────────────────────────────────────────────────────────
XP = {
    "line_added":          1,
    "file_edited":         5,
    "tab_accepted":        2,
    "session_completed":   20,
    "session_aborted":     2,
    "daily_login":         10,
    "streak_bonus":        15,
    "command_run":         3,
    "test_passed":         10,
    "build_succeeded":     8,
    "agent_loop":          10,
    "subagent_completed":  15,
    "tool_call":           2,
    "compaction":          25,
    "prompt_submitted":    1,
    "new_language":        30,
}
def xp_for_level(n):
    return int(100 * (n ** 1.5))
def level_from_xp(total):
    level = 1
    while xp_for_level(level + 1) <= total:
        level += 1
    return level
def file_ext(path):
    return Path(path).suffix.lstrip(".") or "unknown"
# ── Load events ────────────────────────────────────────────────────────────
events = []
if EVENTS_FILE.exists():
    for line in EVENTS_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
# ── Aggregate ──────────────────────────────────────────────────────────────
lifetime  = defaultdict(int)
projects  = defaultdict(lambda: defaultdict(int))
xp_total  = 0
xp_breakdown = defaultdict(int)
seen_languages = set()
active_days    = set()
sessions_by_day = defaultdict(set)
today_str  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
today      = defaultdict(int)
recent_events = []
for e in events:
    ename   = e.get("hook_event_name", "")
    project = e.get("_project", "global")
    ts      = e.get("_ts", "")
    day     = ts[:10] if ts else ""
    # ── sessionStart ──────────────────────────────────────────
    if ename == "sessionStart":
        lifetime["sessions_started"] += 1
        if day:
            active_days.add(day)
            sessions_by_day[day].add(e.get("session_id", ts))
            if day == today_str:
                today["sessions"] += 1
        # Daily login XP (once per day)
        if day and day not in getattr(aggregate, "_login_days", set()):
            xp_total += XP["daily_login"]
            xp_breakdown["daily_logins"] += XP["daily_login"]
    # ── sessionEnd ────────────────────────────────────────────
    elif ename == "sessionEnd":
        reason = e.get("reason", "")
        if reason == "completed":
            lifetime["sessions_completed"] += 1
            xp_total += XP["session_completed"]
            xp_breakdown["sessions_completed"] += XP["session_completed"]
        else:
            lifetime["sessions_aborted"] += 1
            xp_total += XP["session_aborted"]
            xp_breakdown["sessions_completed"] += XP["session_aborted"]
        lifetime["total_session_duration_ms"] += e.get("duration_ms", 0)
    # ── afterFileEdit ─────────────────────────────────────────
    elif ename == "afterFileEdit":
        fp  = e.get("file_path", "")
        ext = file_ext(fp)
        for edit in e.get("edits", []):
            added   = len((edit.get("new_string") or "").splitlines())
            removed = len((edit.get("old_string") or "").splitlines())
            lifetime["lines_added"]   += added
            lifetime["lines_removed"] += removed
            projects[project]["lines_added"] += added
            xp_earned = added * XP["line_added"]
            xp_total += xp_earned
            xp_breakdown["lines_added"] += xp_earned
            if day == today_str:
                today["lines_added"] += added
        lifetime["files_edited"] += 1
        projects[project]["files_edited"] += 1
        xp_total += XP["file_edited"]
        xp_breakdown["files_edited"] += XP["file_edited"]
        # Language tracking
        if ext not in seen_languages:
            seen_languages.add(ext)
            xp_total += XP["new_language"]
            xp_breakdown["languages"] = xp_breakdown.get("languages", 0) + XP["new_language"]
    # ── afterTabFileEdit ──────────────────────────────────────
    elif ename == "afterTabFileEdit":
        lifetime["tab_completions_accepted"] += len(e.get("edits", []))
        gained = len(e.get("edits", [])) * XP["tab_accepted"]
        xp_total += gained
        xp_breakdown["tab_accepted"] += gained
        if day == today_str:
            today["tab_completions"] += len(e.get("edits", []))
    # ── afterShellExecution ───────────────────────────────────
    elif ename == "afterShellExecution":
        cmd = e.get("command", "")
        lifetime["commands_run"] += 1
        xp_total += XP["command_run"]
        xp_breakdown["commands_run"] += XP["command_run"]
        if any(k in cmd for k in ["test", "pytest", "jest", "vitest"]):
            lifetime["test_runs"] += 1
            xp_total += XP["test_passed"]
            xp_breakdown["commands_run"] += XP["test_passed"]
        if any(k in cmd for k in ["build", "tsc", "webpack", "cargo build"]):
            lifetime["build_runs"] += 1
            xp_total += XP["build_succeeded"]
            xp_breakdown["build_successes"] += XP["build_succeeded"]
        if day == today_str:
            today["commands_run"] += 1
    # ── postToolUse ───────────────────────────────────────────
    elif ename == "postToolUse":
        lifetime["tool_calls_total"] += 1
        xp_total += XP["tool_call"]
        xp_breakdown["tool_calls"] += XP["tool_call"]
        if day == today_str:
            today["tool_calls"] += 1
    # ── postToolUseFailure ────────────────────────────────────
    elif ename == "postToolUseFailure":
        lifetime["tool_calls_failed"] += 1
    # ── stop ──────────────────────────────────────────────────
    elif ename == "stop":
        lc = e.get("loop_count", 0)
        if lc > 0:
            lifetime["agent_loops_total"] += lc
            gained = lc * XP["agent_loop"]
            xp_total += gained
            xp_breakdown["agent_loops"] += gained
    # ── subagentStop ──────────────────────────────────────────
    elif ename == "subagentStop":
        if e.get("status") == "completed":
            lifetime["subagents_completed"] += 1
            xp_total += XP["subagent_completed"]
            xp_breakdown["subagents_completed"] += XP["subagent_completed"]
    # ── preCompact ────────────────────────────────────────────
    elif ename == "preCompact":
        lifetime["compactions_triggered"] += 1
        xp_total += XP["compaction"]
        xp_breakdown["compactions"] += XP["compaction"]
    # ── beforeSubmitPrompt ────────────────────────────────────
    elif ename == "beforeSubmitPrompt":
        lifetime["prompts_submitted"] += 1
        xp_total += XP["prompt_submitted"]
        xp_breakdown["prompts_submitted"] += XP["prompt_submitted"]
# ── Streak calculation ─────────────────────────────────────────────────────
sorted_days = sorted(active_days)
current_streak = 0
longest_streak = 0
streak = 1
for i in range(1, len(sorted_days)):
    d1 = datetime.fromisoformat(sorted_days[i-1])
    d2 = datetime.fromisoformat(sorted_days[i])
    if (d2 - d1).days == 1:
        streak += 1
    else:
        longest_streak = max(longest_streak, streak)
        streak = 1
longest_streak = max(longest_streak, streak)
# Current streak: count backwards from today
current_streak = 0
check = datetime.now(timezone.utc).date()
for d in reversed(sorted_days):
    if datetime.fromisoformat(d).date() == check:
        current_streak += 1
        check = check.replace(day=check.day - 1)
    else:
        break
# ── Streak XP bonuses ──────────────────────────────────────────────────────
if current_streak >= 3:
    bonus = current_streak * XP["streak_bonus"]
    xp_total += bonus
    xp_breakdown["streak_bonuses"] += bonus
# ── Level calc ─────────────────────────────────────────────────────────────
level      = level_from_xp(xp_total)
xp_floor   = xp_for_level(level)
xp_ceiling = xp_for_level(level + 1)
xp_pct     = int(((xp_total - xp_floor) / (xp_ceiling - xp_floor)) * 100)
# ── Build state.json (continued from aggregate.py) ─────────────────────────

# Achievement definitions with their check functions
ACHIEVEMENTS = [
    # Editing
    { "id": "first_edit",        "name": "Hello, World",      "check": lambda l, _: l["files_edited"] >= 1,                          "xp": 50  },
    { "id": "century_lines",     "name": "Century",           "check": lambda l, _: l["lines_added"] >= 100,                         "xp": 75  },
    { "id": "file_surgeon",      "name": "File Surgeon",      "check": lambda l, _: l["files_edited"] >= 10,                         "xp": 100 },
    { "id": "tab_master",        "name": "Tab Master",        "check": lambda l, _: l["tab_completions_accepted"] >= 50,             "xp": 100 },
    { "id": "tab_lord",          "name": "Tab Lord",          "check": lambda l, _: l["tab_completions_accepted"] >= 500,            "xp": 300 },
    # Sessions
    { "id": "streak_3",          "name": "Hat Trick",         "check": lambda _, s: s["current"] >= 3,                              "xp": 50  },
    { "id": "streak_7",          "name": "Week Warrior",      "check": lambda _, s: s["current"] >= 7,                              "xp": 150 },
    { "id": "streak_30",         "name": "Unstoppable",       "check": lambda _, s: s["current"] >= 30,                             "xp": 500 },
    { "id": "marathon",          "name": "Marathon Coder",    "check": lambda l, _: l["compactions_triggered"] >= 1,                "xp": 75  },
    # Agent depth
    { "id": "loop_starter",      "name": "Loop Starter",      "check": lambda l, _: l["agent_loops_total"] >= 1,                   "xp": 30  },
    { "id": "subagent_first",    "name": "Delegator",         "check": lambda l, _: l["subagents_completed"] >= 1,                 "xp": 75  },
    { "id": "subagent_10",       "name": "Manager",           "check": lambda l, _: l["subagents_completed"] >= 10,                "xp": 200 },
    # Shell
    { "id": "first_shell",       "name": "Shell Shock",       "check": lambda l, _: l["commands_run"] >= 1,                       "xp": 20  },
    { "id": "test_runner",       "name": "Test Runner",       "check": lambda l, _: l["test_runs"] >= 10,                         "xp": 75  },
    { "id": "build_master",      "name": "Build Master",      "check": lambda l, _: l["build_runs"] >= 25,                        "xp": 150 },
    { "id": "tool_addict",       "name": "Tool Addict",       "check": lambda l, _: l["tool_calls_total"] >= 100,                 "xp": 100 },
]

# Load existing state to preserve already-unlocked achievement timestamps
existing_state = {}
if STATE_FILE.exists():
    try:
        existing_state = json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        pass

already_unlocked = {
    a["id"]: a for a in existing_state.get("achievements", {}).get("unlocked", [])
}

streak_info = {"current": current_streak, "longest": longest_streak}
unlocked     = []
in_progress  = []
locked       = []

for ach in ACHIEVEMENTS:
    aid = ach["id"]
    if aid in already_unlocked:
        # Preserve original unlock timestamp
        unlocked.append(already_unlocked[aid])
        continue

    passed = False
    try:
        passed = ach["check"](lifetime, streak_info)
    except Exception:
        pass

    if passed:
        unlocked.append({
            "id":          aid,
            "name":        ach["name"],
            "unlocked_at": datetime.now(timezone.utc).isoformat(),
            "xp_awarded":  ach["xp"]
        })
        # Award achievement XP
        xp_total      += ach["xp"]
        xp_breakdown["achievements"] = xp_breakdown.get("achievements", 0) + ach["xp"]
    else:
        # For in_progress we need a progress value - use a simple heuristic
        # based on achievement id patterns
        locked.append({ "id": aid, "name": ach["name"] })

# Recalculate level after achievement XP is added
level      = level_from_xp(xp_total)
xp_floor   = xp_for_level(level)
xp_ceiling = xp_for_level(level + 1)
xp_pct     = int(((xp_total - xp_floor) / (xp_ceiling - xp_floor)) * 100)

# Per-project level
project_states = {}
for pname, pdata in projects.items():
    pxp    = sum([
        pdata.get("lines_added", 0)   * XP["line_added"],
        pdata.get("files_edited", 0)  * XP["file_edited"],
    ])
    plevel = level_from_xp(pxp)
    project_states[pname] = {
        "xp":          pxp,
        "level":       plevel,
        "lines_added": pdata.get("lines_added", 0),
        "files_edited":pdata.get("files_edited", 0),
    }

# Final state object
state = {
    "user": {
        "email":          next((e.get("user_email") for e in reversed(events) if e.get("user_email")), None),
        "cursor_version": next((e.get("cursor_version") for e in reversed(events) if e.get("cursor_version")), None),
    },
    "xp": {
        "total":              xp_total,
        "level":              level,
        "xp_current_level":   xp_floor,
        "xp_next_level":      xp_ceiling,
        "xp_progress_pct":    xp_pct,
        "breakdown":          dict(xp_breakdown),
    },
    "streaks": {
        "current_daily_streak": current_streak,
        "longest_daily_streak": longest_streak,
        "last_active_date":     sorted_days[-1] if sorted_days else None,
    },
    "achievements": {
        "unlocked":    unlocked,
        "in_progress": in_progress,
        "locked":      locked,
    },
    "lifetime":  dict(lifetime),
    "today": {
        "date":             today_str,
        "xp_earned":        today.get("xp_earned", 0),
        "sessions":         today.get("sessions", 0),
        "lines_added":      today.get("lines_added", 0),
        "tab_completions":  today.get("tab_completions", 0),
        "commands_run":     today.get("commands_run", 0),
        "tool_calls":       today.get("tool_calls", 0),
    },
    "projects":            project_states,
    "last_aggregated_at":  datetime.now(timezone.utc).isoformat(),
}

STATE_FILE.write_text(json.dumps(state, indent=2))
print(f"[aggregate] Level {level} | {xp_total} XP | {len(unlocked)} achievements unlocked")
```

## 7. Triggering the Aggregator Automatically

Add this to your collector.sh so aggregation runs after every sessionEnd:

```py
# At the bottom of collector.sh, after the jq append:
event_name=$(echo "$raw" | jq -r '.hook_event_name')
if [ "$event_name" = "sessionEnd" ] || [ "$event_name" = "stop" ]; then
  python3 "$HOME/.cursor/dashboard/aggregate.py" &
fi
```

Or add a cron job for every 15 minutes regardless:

```py
# crontab -e
*/15 * * * * python3 ~/.cursor/dashboard/aggregate.py >> ~/.cursor/dashboard/aggregate.log 2>&1
```

## 8. The Dashboard Webpage

A single self-contained HTML file that reads state.json via a tiny local server and renders everything. No framework needed.

### Local runtime

```py
# Normal install path:
# the installer starts the local runtime and opens Momentum once automatically.
#
# Manual fallback:
python3 -m aggregator.runtime start --runtime-dir ~/.cursor/dashboard --port 7420
```

Then open the local URL reported by `python3 -m aggregator.runtime status --runtime-dir ~/.cursor/dashboard`.

`~/.cursor/dashboard/dashboard.html`

```html
<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1.0" />
		<title>Momentum</title>
		<style>
			/* ── Reset & base ──────────────────────────────────────── */
			*,
			*::before,
			*::after {
				box-sizing: border-box;
				margin: 0;
				padding: 0;
			}
			:root {
				--bg: #0d0d0f;
				--surface: #16161a;
				--border: #2a2a35;
				--accent: #7c6af7;
				--accent2: #4fc8a0;
				--warn: #f5a623;
				--danger: #e05c5c;
				--text: #e8e8f0;
				--muted: #666680;
				--radius: 10px;
			}
			body {
				background: var(--bg);
				color: var(--text);
				font-family: "Inter", "Segoe UI", system-ui, sans-serif;
				font-size: 14px;
				line-height: 1.6;
				padding: 24px;
				max-width: 1200px;
				margin: 0 auto;
			}
			h1 {
				font-size: 22px;
				font-weight: 700;
				letter-spacing: -0.3px;
			}
			h2 {
				font-size: 13px;
				font-weight: 600;
				text-transform: uppercase;
				letter-spacing: 0.8px;
				color: var(--muted);
				margin-bottom: 12px;
			}
			h3 {
				font-size: 15px;
				font-weight: 600;
			}
			/* ── Layout grid ───────────────────────────────────────── */
			.grid {
				display: grid;
				grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
				gap: 16px;
				margin-top: 24px;
			}
			.card {
				background: var(--surface);
				border: 1px solid var(--border);
				border-radius: var(--radius);
				padding: 20px;
			}
			.card.wide {
				grid-column: span 2;
			}
			.card.full {
				grid-column: 1 / -1;
			}
			/* ── Header row ────────────────────────────────────────── */
			.header {
				display: flex;
				align-items: center;
				justify-content: space-between;
				margin-bottom: 24px;
			}
			.user-pill {
				font-size: 12px;
				color: var(--muted);
				background: var(--surface);
				border: 1px solid var(--border);
				border-radius: 99px;
				padding: 4px 12px;
			}
			/* ── Level badge ───────────────────────────────────────── */
			.level-badge {
				display: flex;
				align-items: center;
				gap: 16px;
				margin-bottom: 14px;
			}
			.level-number {
				font-size: 48px;
				font-weight: 800;
				color: var(--accent);
				line-height: 1;
			}
			.level-label {
				font-size: 12px;
				color: var(--muted);
			}
			.level-title {
				font-size: 16px;
				font-weight: 600;
			}
			/* ── XP bar ────────────────────────────────────────────── */
			.xp-bar-wrap {
				margin-top: 10px;
			}
			.xp-bar-track {
				height: 8px;
				background: var(--border);
				border-radius: 99px;
				overflow: hidden;
			}
			.xp-bar-fill {
				height: 100%;
				background: linear-gradient(90deg, var(--accent), var(--accent2));
				border-radius: 99px;
				transition: width 0.6s ease;
			}
			.xp-bar-labels {
				display: flex;
				justify-content: space-between;
				font-size: 11px;
				color: var(--muted);
				margin-top: 4px;
			}
			/* ── Stat tiles ────────────────────────────────────────── */
			.stat-grid {
				display: grid;
				grid-template-columns: repeat(3, 1fr);
				gap: 10px;
				margin-top: 4px;
			}
			.stat-tile {
				background: var(--bg);
				border: 1px solid var(--border);
				border-radius: 8px;
				padding: 12px;
				text-align: center;
			}
			.stat-value {
				font-size: 22px;
				font-weight: 700;
				color: var(--accent2);
			}
			.stat-label {
				font-size: 11px;
				color: var(--muted);
				margin-top: 2px;
			}
			/* ── Streak ────────────────────────────────────────────── */
			.streak-row {
				display: flex;
				gap: 12px;
				align-items: center;
			}
			.streak-count {
				font-size: 40px;
				font-weight: 800;
				color: var(--warn);
			}
			.streak-meta {
				font-size: 12px;
				color: var(--muted);
			}
			/* ── Achievements ──────────────────────────────────────── */
			.ach-list {
				display: flex;
				flex-direction: column;
				gap: 8px;
			}
			.ach-item {
				display: flex;
				align-items: center;
				gap: 12px;
				padding: 10px;
				background: var(--bg);
				border: 1px solid var(--border);
				border-radius: 8px;
			}
			.ach-item.locked {
				opacity: 0.35;
				filter: grayscale(1);
			}
			.ach-icon {
				font-size: 20px;
			}
			.ach-name {
				font-size: 13px;
				font-weight: 600;
			}
			.ach-desc {
				font-size: 11px;
				color: var(--muted);
			}
			.ach-xp {
				margin-left: auto;
				font-size: 11px;
				font-weight: 700;
				color: var(--accent);
				white-space: nowrap;
			}
			/* ── Progress bars (in-progress achievements) ──────────── */
			.prog-bar-track {
				height: 4px;
				background: var(--border);
				border-radius: 99px;
				margin-top: 4px;
				overflow: hidden;
			}
			.prog-bar-fill {
				height: 100%;
				background: var(--warn);
				border-radius: 99px;
			}
			/* ── XP breakdown chart ────────────────────────────────── */
			.breakdown-list {
				display: flex;
				flex-direction: column;
				gap: 6px;
			}
			.breakdown-row {
				display: flex;
				align-items: center;
				gap: 8px;
			}
			.breakdown-label {
				font-size: 12px;
				color: var(--muted);
				width: 160px;
				flex-shrink: 0;
			}
			.breakdown-track {
				flex: 1;
				height: 6px;
				background: var(--border);
				border-radius: 99px;
				overflow: hidden;
			}
			.breakdown-fill {
				height: 100%;
				background: var(--accent);
				border-radius: 99px;
			}
			.breakdown-val {
				font-size: 12px;
				color: var(--text);
				width: 48px;
				text-align: right;
			}
			/* ── Today card ────────────────────────────────────────── */
			.today-grid {
				display: grid;
				grid-template-columns: repeat(3, 1fr);
				gap: 8px;
			}
			/* ── Projects table ────────────────────────────────────── */
			.proj-table {
				width: 100%;
				border-collapse: collapse;
			}
			.proj-table th {
				text-align: left;
				font-size: 11px;
				color: var(--muted);
				text-transform: uppercase;
				letter-spacing: 0.6px;
				padding: 6px 8px;
				border-bottom: 1px solid var(--border);
			}
			.proj-table td {
				padding: 8px;
				font-size: 13px;
			}
			.proj-table tr:not(:last-child) td {
				border-bottom: 1px solid var(--border);
			}
			.proj-level {
				display: inline-block;
				background: var(--accent);
				color: #fff;
				font-size: 11px;
				font-weight: 700;
				border-radius: 4px;
				padding: 2px 6px;
			}

			/* ── Activity feed ─────────────────────────────────────── */
			.feed-list {
				display: flex;
				flex-direction: column;
				gap: 6px;
			}
			.feed-item {
				display: flex;
				align-items: center;
				gap: 10px;
				font-size: 12px;
				color: var(--muted);
			}
			.feed-dot {
				width: 6px;
				height: 6px;
				border-radius: 50%;
				background: var(--accent);
				flex-shrink: 0;
			}
			.feed-dot.achievement {
				background: var(--warn);
			}
			.feed-dot.levelup {
				background: var(--accent2);
			}
			.feed-dot.error {
				background: var(--danger);
			}

			/* ── Language bar ──────────────────────────────────────── */
			.lang-list {
				display: flex;
				flex-direction: column;
				gap: 6px;
			}
			.lang-row {
				display: flex;
				align-items: center;
				gap: 8px;
			}
			.lang-name {
				font-size: 12px;
				width: 40px;
				color: var(--muted);
			}
			.lang-track {
				flex: 1;
				height: 8px;
				background: var(--border);
				border-radius: 99px;
				overflow: hidden;
			}
			.lang-fill {
				height: 100%;
				border-radius: 99px;
			}
			.lang-count {
				font-size: 12px;
				width: 32px;
				text-align: right;
			}

			/* ── Refresh badge ─────────────────────────────────────── */
			.refresh-btn {
				background: var(--surface);
				border: 1px solid var(--border);
				color: var(--muted);
				font-size: 12px;
				padding: 4px 10px;
				border-radius: 6px;
				cursor: pointer;
			}
			.refresh-btn:hover {
				border-color: var(--accent);
				color: var(--accent);
			}

			/* ── Tab switcher ──────────────────────────────────────── */
			.tabs {
				display: flex;
				gap: 4px;
				margin-bottom: 20px;
			}
			.tab-btn {
				padding: 6px 14px;
				font-size: 13px;
				background: none;
				border: 1px solid var(--border);
				border-radius: 6px;
				color: var(--muted);
				cursor: pointer;
			}
			.tab-btn.active {
				background: var(--accent);
				border-color: var(--accent);
				color: #fff;
			}
			.tab-panel {
				display: none;
			}
			.tab-panel.active {
				display: contents;
			}

			/* ── Toasts ────────────────────────────────────────────── */
			#toast-container {
				position: fixed;
				bottom: 24px;
				right: 24px;
				display: flex;
				flex-direction: column;
				gap: 8px;
				z-index: 999;
			}
			.toast {
				background: var(--surface);
				border: 1px solid var(--accent);
				border-radius: 8px;
				padding: 12px 16px;
				font-size: 13px;
				min-width: 220px;
				animation: slideIn 0.3s ease;
			}
			.toast.achievement {
				border-color: var(--warn);
			}
			.toast.levelup {
				border-color: var(--accent2);
			}
			@keyframes slideIn {
				from {
					opacity: 0;
					transform: translateX(40px);
				}
				to {
					opacity: 1;
					transform: translateX(0);
				}
			}
		</style>
	</head>
	<body>
		<!-- ── Toast container (achievement popups) ──────────────────── -->
		<div id="toast-container"></div>

		<!-- ── Header ────────────────────────────────────────────────── -->
		<div class="header">
			<h1>Momentum</h1>
			<div style="display:flex;gap:8px;align-items:center">
				<span class="user-pill" id="user-email">loading...</span>
				<button class="refresh-btn" onclick="loadState()">Refresh</button>
			</div>
		</div>

		<!-- ── Tab switcher ───────────────────────────────────────────── -->
		<div class="tabs">
			<button class="tab-btn active" onclick="switchTab('overview')">
				Overview
			</button>
			<button class="tab-btn" onclick="switchTab('achievements')">
				Achievements
			</button>
			<button class="tab-btn" onclick="switchTab('projects')">Projects</button>
			<button class="tab-btn" onclick="switchTab('stats')">
				Lifetime Stats
			</button>
		</div>

		<!-- ═══════════════════════════════════════════════════════════
     TAB: OVERVIEW
═══════════════════════════════════════════════════════════════ -->
		<div class="tab-panel active grid" id="tab-overview">
			<!-- Level card -->
			<div class="card">
				<h2>Level</h2>
				<div class="level-badge">
					<div class="level-number" id="level-num">—</div>
					<div>
						<div class="level-title" id="level-title">—</div>
						<div class="level-label" id="level-xp-label">0 / 0 XP</div>
					</div>
				</div>
				<div class="xp-bar-wrap">
					<div class="xp-bar-track">
						<div class="xp-bar-fill" id="xp-bar" style="width:0%"></div>
					</div>
					<div class="xp-bar-labels">
						<span id="xp-floor">0</span>
						<span id="xp-pct">0%</span>
						<span id="xp-ceil">0</span>
					</div>
				</div>
			</div>

			<!-- Streak card -->
			<div class="card">
				<h2>Daily Streak</h2>
				<div class="streak-row">
					<div class="streak-count" id="streak-count">—</div>
					<div>
						<div style="font-size:15px;font-weight:600">days active</div>
						<div class="streak-meta" id="streak-best">Best: —</div>
						<div class="streak-meta" id="streak-last">Last active: —</div>
					</div>
				</div>
			</div>

			<!-- Today card -->
			<div class="card">
				<h2>Today</h2>
				<div class="today-grid">
					<div class="stat-tile">
						<div class="stat-value" id="today-xp">—</div>
						<div class="stat-label">XP earned</div>
					</div>
					<div class="stat-tile">
						<div class="stat-value" id="today-sessions">—</div>
						<div class="stat-label">Sessions</div>
					</div>
					<div class="stat-tile">
						<div class="stat-value" id="today-lines">—</div>
						<div class="stat-label">Lines added</div>
					</div>
					<div class="stat-tile">
						<div class="stat-value" id="today-tabs">—</div>
						<div class="stat-label">Tab accepts</div>
					</div>
					<div class="stat-tile">
						<div class="stat-value" id="today-cmds">—</div>
						<div class="stat-label">Commands</div>
					</div>
					<div class="stat-tile">
						<div class="stat-value" id="today-tools">—</div>
						<div class="stat-label">Tool calls</div>
					</div>
				</div>
			</div>

			<!-- XP breakdown -->
			<div class="card wide">
				<h2>XP Sources</h2>
				<div class="breakdown-list" id="xp-breakdown"></div>
			</div>

			<!-- Recent activity feed -->
			<div class="card">
				<h2>Recent Activity</h2>
				<div class="feed-list" id="activity-feed"></div>
			</div>

			<!-- Language breakdown -->
			<div class="card">
				<h2>Languages Edited</h2>
				<div class="lang-list" id="lang-list"></div>
			</div>
		</div>
		<!-- /tab-overview -->

		<!-- ═══════════════════════════════════════════════════════════
     TAB: ACHIEVEMENTS
═══════════════════════════════════════════════════════════════ -->
		<div class="tab-panel grid" id="tab-achievements">
			<div class="card full">
				<h2>
					Unlocked <span id="ach-count" style="color:var(--accent2)"></span>
				</h2>
				<div class="ach-list" id="ach-unlocked"></div>
			</div>

			<div class="card full">
				<h2>In Progress</h2>
				<div class="ach-list" id="ach-progress"></div>
			</div>

			<div class="card full">
				<h2>Locked</h2>
				<div class="ach-list" id="ach-locked"></div>
			</div>
		</div>
		<!-- /tab-achievements -->

		<!-- ═══════════════════════════════════════════════════════════
     TAB: PROJECTS
═══════════════════════════════════════════════════════════════ -->
		<div class="tab-panel grid" id="tab-projects">
			<div class="card full">
				<h2>Per-Project Stats</h2>
				<table class="proj-table">
					<thead>
						<tr>
							<th>Project</th>
							<th>Level</th>
							<th>XP</th>
							<th>Sessions</th>
							<th>Lines Added</th>
							<th>Files Edited</th>
							<th>Last Active</th>
						</tr>
					</thead>
					<tbody id="proj-tbody"></tbody>
				</table>
			</div>
		</div>
		<!-- /tab-projects -->

		<!-- ═══════════════════════════════════════════════════════════
     TAB: LIFETIME STATS
═══════════════════════════════════════════════════════════════ -->
		<div class="tab-panel grid" id="tab-stats">
			<div class="card full">
				<h2>Lifetime Statistics</h2>
				<div class="stat-grid" id="lifetime-grid"></div>
			</div>
		</div>
		<!-- /tab-stats -->

		<script>
			// ── Helpers ────────────────────────────────────────────────────────────────

			const $ = (id) => document.getElementById(id)
			const fmt = (n) => (n ?? 0).toLocaleString()

			const LANG_COLORS = [
				"#7c6af7",
				"#4fc8a0",
				"#f5a623",
				"#e05c5c",
				"#5cb8f5",
				"#b46cf5",
				"#f5c45c",
				"#5cf5a4",
			]

			const LEVEL_TITLES = [
				"",
				"Newcomer",
				"Apprentice",
				"Developer",
				"Engineer",
				"Senior Dev",
				"Tech Lead",
				"Architect",
				"Principal",
				"Staff Eng",
				"Distinguished",
				"Fellow",
				"Grandmaster",
			]

			function levelTitle(n) {
				return (
					LEVEL_TITLES[Math.min(n, LEVEL_TITLES.length - 1)] || `Level ${n}`
				)
			}

			// ── Toast notifications ────────────────────────────────────────────────────

			let _prevState = null

			function showToast(msg, type = "") {
				const el = document.createElement("div")
				el.className = `toast ${type}`
				el.textContent = msg
				$("toast-container").appendChild(el)
				setTimeout(() => el.remove(), 4000)
			}

			function diffAndNotify(state) {
				if (!_prevState) {
					_prevState = state
					return
				}

				// Level up
				if (state.xp.level > _prevState.xp.level) {
					showToast(
						`Level up! You are now Level ${state.xp.level} — ${levelTitle(state.xp.level)}`,
						"levelup",
					)
				}

				// New achievement
				const prevIds = new Set(
					(_prevState.achievements?.unlocked || []).map((a) => a.id),
				)
				for (const a of state.achievements?.unlocked || []) {
					if (!prevIds.has(a.id)) {
						showToast(
							`Achievement unlocked: ${a.name} (+${a.xp_awarded} XP)`,
							"achievement",
						)
					}
				}

				_prevState = state
			}

			// ── Tab switcher ───────────────────────────────────────────────────────────

			function switchTab(name) {
				document
					.querySelectorAll(".tab-panel")
					.forEach((p) => p.classList.remove("active"))
				document
					.querySelectorAll(".tab-btn")
					.forEach((b) => b.classList.remove("active"))
				$(`tab-${name}`).classList.add("active")
				event.target.classList.add("active")
			}

			// ── Render functions ───────────────────────────────────────────────────────

			function renderOverview(s) {
				// User
				$("user-email").textContent = s.user?.email || "unknown"

				// Level
				$("level-num").textContent = s.xp.level
				$("level-title").textContent = levelTitle(s.xp.level)
				$("level-xp-label").textContent = `${fmt(s.xp.total)} total XP`
				$("xp-bar").style.width = `${s.xp.xp_progress_pct}%`
				$("xp-floor").textContent = fmt(s.xp.xp_current_level)
				$("xp-ceil").textContent = fmt(s.xp.xp_next_level)
				$("xp-pct").textContent = `${s.xp.xp_progress_pct}%`

				// Streak
				$("streak-count").textContent = s.streaks.current_daily_streak
				$("streak-best").textContent =
					`Best: ${s.streaks.longest_daily_streak} days`
				$("streak-last").textContent =
					`Last active: ${s.streaks.last_active_date || "—"}`

				// Today
				$("today-xp").textContent = fmt(s.today.xp_earned)
				$("today-sessions").textContent = fmt(s.today.sessions)
				$("today-lines").textContent = fmt(s.today.lines_added)
				$("today-tabs").textContent = fmt(s.today.tab_completions)
				$("today-cmds").textContent = fmt(s.today.commands_run)
				$("today-tools").textContent = fmt(s.today.tool_calls)

				// XP Breakdown
				const bd = s.xp.breakdown || {}
				const maxXP = Math.max(...Object.values(bd), 1)
				const labels = {
					lines_added: "Lines added",
					files_edited: "Files edited",
					tab_accepted: "Tab completions",
					sessions_completed: "Sessions completed",
					daily_logins: "Daily logins",
					streak_bonuses: "Streak bonuses",
					commands_run: "Commands run",
					build_successes: "Builds",
					agent_loops: "Agent loops",
					subagents_completed: "Subagents",
					tool_calls: "Tool calls",
					compactions: "Compactions",
					prompts_submitted: "Prompts",
					achievements: "Achievements",
				}
				$("xp-breakdown").innerHTML = Object.entries(bd)
					.sort((a, b) => b[1] - a[1])
					.map(
						([k, v]) => `
      <div class="breakdown-row">
        <span class="breakdown-label">${labels[k] || k}</span>
        <div class="breakdown-track">
          <div class="breakdown-fill" style="width:${Math.round((v / maxXP) * 100)}%"></div>
        </div>
        <span class="breakdown-val">${fmt(v)}</span>
      </div>`,
					)
					.join("")

				// Activity feed
				const feed = s.recent_events || []
				$("activity-feed").innerHTML = feed.length
					? feed
							.map((ev) => {
								const dotClass =
									ev.type === "achievement_unlocked"
										? "achievement"
										: ev.type === "level_up"
											? "levelup"
											: ""
								const text =
									ev.type === "achievement_unlocked"
										? `Achievement: ${ev.id}`
										: ev.type === "level_up"
											? `Reached Level ${ev.level}`
											: ev.type === "xp_earned"
												? `+${ev.amount} XP — ${ev.reason}`
												: ev.type === "streak_extended"
													? `Streak extended to ${ev.streak} days`
													: ev.type
								const time = ev.ts ? new Date(ev.ts).toLocaleTimeString() : ""
								return `<div class="feed-item">
          <div class="feed-dot ${dotClass}"></div>
          <span>${text}</span>
          <span style="margin-left:auto;font-size:11px">${time}</span>
        </div>`
							})
							.join("")
					: '<div style="color:var(--muted);font-size:12px">No recent events yet.</div>'

				// Languages
				const langs = s.lifetime?.languages || {}
				const maxL = Math.max(...Object.values(langs), 1)
				$("lang-list").innerHTML = Object.entries(langs)
					.sort((a, b) => b[1] - a[1])
					.map(
						([lang, count], i) => `
      <div class="lang-row">
        <span class="lang-name">.${lang}</span>
        <div class="lang-track">
          <div class="lang-fill" style="width:${Math.round((count / maxL) * 100)}%;background:${LANG_COLORS[i % LANG_COLORS.length]}"></div>
        </div>
        <span class="lang-count">${fmt(count)}</span>
      </div>`,
					)
					.join("")
			}

			function renderAchievements(s) {
				const ach = s.achievements || {}

				$("ach-count").textContent = `(${(ach.unlocked || []).length})`

				const ICONS = {
					first_edit: "✏️",
					century_lines: "💯",
					file_surgeon: "🔬",
					tab_master: "⚡",
					tab_lord: "👑",
					streak_3: "🔥",
					streak_7: "🗓️",
					streak_30: "🏆",
					marathon: "🏃",
					deep_thought: "🧠",
					loop_starter: "🔄",
					loop_5: "♾️",
					subagent_first: "🤖",
					subagent_10: "🏭",
					subagent_parallel: "⚙️",
					first_shell: "💻",
					test_runner: "🧪",
					build_master: "🏗️",
					mcp_explorer: "🔌",
					tool_addict: "🛠️",
					comeback: "💪",
					zero_errors: "🧹",
					multi_project: "🗂️",
					project_veteran: "🎖️",
				}

				// Unlocked
				$("ach-unlocked").innerHTML = (ach.unlocked || []).length
					? ach.unlocked
							.map(
								(a) => `
        <div class="ach-item">
          <span class="ach-icon">${ICONS[a.id] || "🏅"}</span>
          <div>
            <div class="ach-name">${a.name}</div>
            <div class="ach-desc">Unlocked ${a.unlocked_at ? new Date(a.unlocked_at).toLocaleDateString() : ""}</div>
          </div>
          <span class="ach-xp">+${fmt(a.xp_awarded)} XP</span>
        </div>`,
							)
							.join("")
					: '<div style="color:var(--muted);font-size:12px">No achievements unlocked yet. Start coding!</div>'

				// In progress
				$("ach-progress").innerHTML = (ach.in_progress || []).length
					? ach.in_progress
							.map(
								(a) => `
        <div class="ach-item">
          <span class="ach-icon">${ICONS[a.id] || "🔒"}</span>
          <div style="flex:1">
            <div class="ach-name">${a.name}</div>
            <div class="ach-desc">${a.desc}</div>
            <div class="prog-bar-track">
              <div class="prog-bar-fill" style="width:${a.progress_pct || 0}%"></div>
            </div>
            <div style="font-size:11px;color:var(--muted);margin-top:3px">
              ${fmt(a.progress)} / ${fmt(a.target)} (${a.progress_pct || 0}%)
            </div>
          </div>
        </div>`,
							)
							.join("")
					: '<div style="color:var(--muted);font-size:12px">No achievements in progress.</div>'

				// Locked
				$("ach-locked").innerHTML = (ach.locked || []).length
					? ach.locked
							.map(
								(a) => `
        <div class="ach-item locked">
          <span class="ach-icon">🔒</span>
          <div>
            <div class="ach-name">${a.name}</div>
            <div class="ach-desc">Keep coding to unlock</div>
          </div>
        </div>`,
							)
							.join("")
					: ""
			}

			function renderProjects(s) {
				const projects = s.projects || {}
				const rows = Object.entries(projects)
					.sort((a, b) => b[1].xp - a[1].xp)
					.map(
						([name, p]) => `
      <tr>
        <td><strong>${name}</strong></td>
        <td><span class="proj-level">Lv ${p.level}</span></td>
        <td>${fmt(p.xp)}</td>
        <td>${fmt(p.sessions)}</td>
        <td>${fmt(p.lines_added)}</td>
        <td>${fmt(p.files_edited)}</td>
        <td style="color:var(--muted)">${p.last_active || "—"}</td>
      </tr>`,
					)
					.join("")

				$("proj-tbody").innerHTML =
					rows ||
					'<tr><td colspan="7" style="color:var(--muted);padding:16px">No project data yet.</td></tr>'
			}

			function renderLifetime(s) {
				const l = s.lifetime || {}

				const TILES = [
					{ label: "Sessions Started", value: fmt(l.sessions_started) },
					{ label: "Sessions Completed", value: fmt(l.sessions_completed) },
					{ label: "Sessions Aborted", value: fmt(l.sessions_aborted) },
					{ label: "Prompts Submitted", value: fmt(l.prompts_submitted) },
					{ label: "Lines Added", value: fmt(l.lines_added) },
					{ label: "Lines Removed", value: fmt(l.lines_removed) },
					{ label: "Files Edited", value: fmt(l.files_edited) },
					{ label: "Unique Files", value: fmt(l.unique_files) },
					{ label: "Tab Completions", value: fmt(l.tab_completions_accepted) },
					{ label: "Commands Run", value: fmt(l.commands_run) },
					{ label: "Test Runs", value: fmt(l.test_runs) },
					{ label: "Build Runs", value: fmt(l.build_runs) },
					{ label: "Tool Calls", value: fmt(l.tool_calls_total) },
					{ label: "Tool Failures", value: fmt(l.tool_calls_failed) },
					{ label: "Agent Loops", value: fmt(l.agent_loops_total) },
					{ label: "Subagents Completed", value: fmt(l.subagents_completed) },
					{ label: "Compactions", value: fmt(l.compactions_triggered) },
					{
						label: "Avg Session Length",
						value: l.sessions_started
							? Math.round(
									(l.total_session_duration_ms || 0) /
										(l.sessions_started * 60000),
								) + "m"
							: "—",
					},
				]

				$("lifetime-grid").innerHTML = TILES.map(
					(t) => `
    <div class="stat-tile">
      <div class="stat-value">${t.value}</div>
      <div class="stat-label">${t.label}</div>
    </div>`,
				).join("")
			}

			// ── Main load and poll ─────────────────────────────────────────────────────

			async function loadState() {
				let state
				try {
					// Fetch state.json served by the local Momentum runtime
					const res = await fetch("./state.json?_=" + Date.now())
					if (!res.ok) throw new Error(`HTTP ${res.status}`)
					state = await res.json()
				} catch (err) {
					console.error("Could not load state.json:", err)
					return
				}

				diffAndNotify(state)
				renderOverview(state)
				renderAchievements(state)
				renderProjects(state)
				renderLifetime(state)
			}

			// Load immediately, then poll every 30 seconds so the dashboard
			// stays live while you're coding without needing a manual refresh.
			loadState()
			setInterval(loadState, 30_000)
		</script>
	</body>
</html>
```

## 9. Full File Structure Summary

Here is every file this system creates and what it does:

`~/.cursor/`

```
├── hooks.json                     ← global hook config, all events routed here
├── hooks/
│   └── collector.sh               ← universal hook receiver, writes events.jsonl
└── dashboard/
    ├── events.jsonl               ← raw append-only event log (one JSON per line)
    ├── aggregate.py               ← reads events.jsonl, writes state.json
    ├── state.json                 ← aggregated game state, read by dashboard
    ├── runtime-config.json        ← local runtime config and launch preferences
    └── index.html                 ← built dashboard UI entrypoint
```

## 10. Getting It Running End to End

```py
# 1. Make the collector executable
chmod +x ~/.cursor/hooks/collector.sh
# 2. Do some work in Cursor — edit files, run commands, chat with the agent
# 3. Run the installer from the repo after building the dashboard
./scripts/install.sh
# 4. Check the local dashboard runtime status
python3 -m aggregator.runtime status --runtime-dir ~/.cursor/dashboard
# 5. The installer opens your dashboard once automatically on first install
# 6. Optional: auto-aggregate every 15 minutes via cron
# Run: crontab -e  then add:
# */15 * * * * python3 ~/.cursor/dashboard/aggregate.py >> ~/.cursor/dashboard/aggregate.log 2>&1
```

## Key Design Decisions to Note

| Decision                                                           | Reason                                                                           |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| `events.jsonl` is append-only and never modified                   | Safe to write from a hook script with no locking; always recoverable             |
| Aggregator is idempotent                                           | Re-running it always produces the same `state.json` from the same `events.jsonl` |
| Dashboard polls `state.json` via HTTP                              | No WebSocket complexity; works with Python's built-in server                     |
| Achievement unlock timestamps are preserved across aggregator runs | Once unlocked, the original timestamp is kept from the previous `state.json`     |
| All hook exit codes are 0                                          | The collector is purely observational and never blocks Cursor actions            |
| XP is calculated only in the aggregator, not in the hook           | Hooks are kept fast and dumb; all game logic lives in one place                  |
