# Implemented Features

This file documents what exists in the repository today. Each section should
remain factual and traceable to source files.

## Local Collector Pipeline

- `Status`: implemented
- `User value`: captures Cursor hook activity into a local append-only event stream
- `Source files`: `collector/collector.sh`
- `Notes`: enriches events with `_ts` and `_project`, then appends to `events.jsonl`

## Event Replay Aggregation

- `Status`: implemented
- `User value`: turns raw hook events into meaningful dashboard state
- `Source files`: `aggregator/src/aggregator/replay.py`, `aggregator/src/aggregator/state.py`
- `Notes`: computes lifetime, daily, per-project, and recent-event views

## XP And Leveling

- `Status`: implemented
- `User value`: makes progress legible through cumulative XP and level progression
- `Source files`: `aggregator/src/aggregator/xp.py`, `aggregator/src/aggregator/state.py`
- `Notes`: uses a curve-based level system and XP breakdown labels

## Achievement System

- `Status`: implemented
- `User value`: recognizes milestones and shows unlock progress
- `Source files`: `aggregator/src/aggregator/achievements.py`, `dashboard/src/app.ts`
- `Notes`: supports unlocked, in-progress, and locked states plus unlock timestamps

## Streak Tracking

- `Status`: implemented
- `User value`: shows consistency and clean-streak momentum
- `Source files`: `aggregator/src/aggregator/achievements.py`, `aggregator/src/aggregator/state.py`, `dashboard/src/app.ts`
- `Notes`: includes daily streak, longest streak, last active date, and clean streak

## Today Metrics

- `Status`: implemented
- `User value`: gives a compact summary of the current day's activity
- `Source files`: `aggregator/src/aggregator/state.py`, `dashboard/src/app.ts`
- `Notes`: includes XP, sessions, lines, tab completions, commands, tool calls, and active projects

## Per-Project View

- `Status`: implemented
- `User value`: helps users see how progress differs across projects
- `Source files`: `aggregator/src/aggregator/replay.py`, `aggregator/src/aggregator/state.py`, `dashboard/src/app.ts`
- `Notes`: includes project XP, level, sessions, lines, files edited, languages, and last active day

## Model Usage View

- `Status`: implemented
- `User value`: shows which Cursor models the user relies on most
- `Source files`: `aggregator/src/aggregator/replay.py`, `aggregator/src/aggregator/state.py`, `dashboard/src/app.ts`
- `Notes`: populated from `sessionStart` model fields and rendered as a metric list

## Activity Feed

- `Status`: implemented
- `User value`: surfaces recent progression events such as unlocks, level-ups, and streak changes
- `Source files`: `aggregator/src/aggregator/state.py`, `dashboard/src/app.ts`
- `Notes`: `state.json` keeps recent events and the dashboard renders them in reverse chronological order

## Real Vs Sample Data Mode

- `Status`: implemented
- `User value`: allows demo-safe browsing without exposing local usage data
- `Source files`: `README.md`, `dashboard/src/api.ts`, `dashboard/src/data-source.ts`, `dashboard/src/app.ts`
- `Notes`: selection persists in `localStorage`

## Lifetime Statistics View

- `Status`: implemented
- `User value`: provides an aggregate view of long-term usage
- `Source files`: `aggregator/src/aggregator/replay.py`, `aggregator/src/aggregator/state.py`, `dashboard/src/app.ts`
- `Notes`: includes sessions, lines, files, tools, builds, tests, loops, subagents, and compactions
