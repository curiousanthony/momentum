# Current State

## What Exists Today

The repository already implements a local data pipeline and a web dashboard:

- a global hook collector appends Cursor events to local `events.jsonl`
- an aggregator replays those events into `state.json`
- a static Bun/Vite dashboard reads that state and renders user-facing cards

## Current Product Character

Today, `Cursor Dashboard` is a functioning local gamified dashboard with real live
data support. It already exposes XP, levels, streaks, achievements, per-project
stats, daily activity, model usage, and a recent activity feed.

What is missing is not the baseline product loop. What is missing is the durable
documentation and product memory layer that explains:

- the north star
- the intended personas
- the research-backed design principles
- the roadmap and current decision state

## Implemented Architecture

### Collector Layer

- `collector/collector.sh` reads hook payloads from stdin
- it enriches events with `_ts` and `_project`
- it appends normalized JSON lines to the local dashboard log
- it triggers the aggregator in the background when the installed aggregate script exists

### Aggregation Layer

- `aggregator/src/aggregator/replay.py` replays hook events into lifetime metrics, per-day metrics, per-project metrics, XP, and behavior signals
- `aggregator/src/aggregator/achievements.py` evaluates unlocks and progress against the achievement catalog
- `aggregator/src/aggregator/state.py` merges replay output with prior state and emits the final dashboard schema
- `aggregator/src/aggregator/xp.py` defines XP constants and the level curve

### Dashboard Layer

- `dashboard/src/api.ts` fetches either real or sample data
- `dashboard/src/data-source.ts` manages the real/sample toggle and persistent local storage setting
- `dashboard/src/app.ts` renders the dashboard shell, cards, tabs, and live refresh behavior
- `dashboard/src/types.ts` defines the current dashboard state contract

## What The UI Currently Shows

- level and XP progress
- current and longest streaks plus clean streak
- today's XP, sessions, lines, tab completions, commands, and tool calls
- XP breakdown by source
- recent activity feed
- language usage
- model usage
- unlocked, in-progress, and locked achievements
- per-project stats
- lifetime statistics
- real vs sample data mode

## Current Gaps

- no explicit north-star documentation
- no durable persona documentation
- no research archive for gamification and motivation decisions
- no canonical project memory or handoff workflow
- no documented status model for ideas, plans, and shipped work

## Related Docs

- `implemented-features.md`
- `roadmap-now-next-later.md`
- `../memory/agent-handoff.md`
- `../memory/status-model.md`
