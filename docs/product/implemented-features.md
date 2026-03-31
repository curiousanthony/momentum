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
- `Source files`: `aggregator/src/aggregator/replay.py`, `aggregator/src/aggregator/insights.py`, `aggregator/src/aggregator/state.py`
- `Notes`: computes lifetime, daily, per-project, recent-event, interpreted signal, and brief views

## Momentum Brief Home

- `Status`: shipped
- `User value`: opens with an interpreted editorial-style home that explains growth, proof, and next direction faster than the old equal-weight dashboard
- `Source files`: `dashboard/src/app.ts`, `dashboard/src/home.ts`, `dashboard/src/styles/app.css`, `dashboard/src/types.ts`, `aggregator/src/aggregator/insights.py`, `aggregator/src/aggregator/state.py`
- `Notes`: home now centers on a dominant `Momentum Brief` hero, restrained proof rail, compact `Today` and cadence support, quieter recent-changes and project-context summaries, and deeper inspection links

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
- `Source files`: `aggregator/src/aggregator/replay.py`, `aggregator/src/aggregator/state.py`, `dashboard/src/home.ts`, `dashboard/src/app.ts`
- `Notes`: populated from `sessionStart` model fields and available in deeper inspection rather than the default home path

## Activity Feed

- `Status`: implemented
- `User value`: surfaces recent progression events such as unlocks, level-ups, and streak changes
- `Source files`: `aggregator/src/aggregator/state.py`, `dashboard/src/home.ts`, `dashboard/src/app.ts`
- `Notes`: `state.json` keeps recent events and home now renders them as a quieter recent-changes summary instead of a dominant feed card

## Real Vs Sample Data Mode

- `Status`: implemented
- `User value`: allows demo-safe browsing without exposing local usage data
- `Source files`: `README.md`, `dashboard/src/api.ts`, `dashboard/src/data-source.ts`, `dashboard/src/app.ts`
- `Notes`: selection persists in `localStorage`

## Dashboard Runtime Startup

- `Status`: implemented
- `User value`: makes the dashboard reachable immediately after install without requiring a manual server command each time Cursor restarts
- `Source files`: `scripts/install.sh`, `scripts/dev-server.sh`, `aggregator/src/aggregator/runtime.py`
- `Notes`: install starts the local runtime, attempts OS-native startup registration, and the runtime serves the dashboard plus a tiny localhost settings API

## Install-Time First Open

- `Status`: implemented
- `User value`: shows the product immediately after first install so users do not need to guess how to access Momentum
- `Source files`: `scripts/install.sh`, `aggregator/src/aggregator/runtime.py`
- `Notes`: first install opens the dashboard in the default browser once and records a marker so reinstalls do not keep reopening it

## Dashboard Launch Preference

- `Status`: implemented
- `User value`: lets users opt into opening Momentum automatically when Cursor starts while keeping the default experience non-intrusive after first install
- `Source files`: `collector/collector.sh`, `aggregator/src/aggregator/runtime.py`, `dashboard/src/preferences.ts`, `dashboard/src/settings.ts`, `dashboard/src/app.ts`
- `Notes`: the recurring auto-open toggle is exposed in `Settings`, mirrored in `localStorage`, synced through the local runtime API, and only acts on `sessionStart`

## Lifetime Statistics View

- `Status`: implemented
- `User value`: provides an aggregate view of long-term usage
- `Source files`: `aggregator/src/aggregator/replay.py`, `aggregator/src/aggregator/state.py`, `dashboard/src/home.ts`, `dashboard/src/app.ts`
- `Notes`: includes sessions, lines, files, tools, builds, tests, loops, subagents, compactions, `XP Sources`, `Languages Edited`, and `Models`; remains available as a deeper-inspection view rather than the primary home surface

## Insight Contract

- `Status`: shipped
- `User value`: gives the dashboard a durable interpreted state layer instead of requiring home copy to be composed ad hoc from raw metrics
- `Source files`: `aggregator/src/aggregator/insights.py`, `aggregator/src/aggregator/state.py`, `dashboard/src/types.ts`
- `Notes`: `state.json` now includes `insights.signal_strength`, structured interpreted signals, and a `brief` payload with headline, summary, validation, cadence, focus, and proof modules
