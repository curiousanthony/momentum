# Current State

## What Exists Today

The repository already implements a local data pipeline and a web dashboard:

- a global hook collector appends Cursor events to local `events.jsonl`
- an aggregator replays those events into `state.json`
- a local dashboard runtime serves the static Bun/Vite app over HTTP and renders user-facing cards

## Current Product Character

Today, `Momentum` is no longer just a stats-first gamified dashboard. The
primary home experience is now a guidance-led `Momentum Brief` that interprets
recent activity into a concise editorial-style summary, then supports that brief
with restrained proof, compact cadence context, and deeper inspection paths.

The product still includes XP, levels, streaks, achievements, per-project
stats, lifetime statistics, language usage, model usage, and recent activity.
Those details remain available, but they no longer define the default home path.

## Implemented Architecture

### Collector Layer

- `collector/collector.sh` reads hook payloads from stdin
- it enriches events with `_ts` and `_project`
- it appends normalized JSON lines to the local dashboard log
- it triggers the aggregator in the background when the installed aggregate script exists
- on `sessionStart`, it can ask the runtime to open the dashboard if the user enabled that setting

### Aggregation Layer

- `aggregator/src/aggregator/replay.py` replays hook events into lifetime metrics, per-day metrics, per-project metrics, XP, and behavior signals
- `aggregator/src/aggregator/achievements.py` evaluates unlocks and progress against the achievement catalog
- `aggregator/src/aggregator/insights.py` interprets replayed metrics into conservative insight signals and a `Momentum Brief` payload
- `aggregator/src/aggregator/state.py` merges replay output with prior state and emits the final dashboard schema, including interpreted `insights`
- `aggregator/src/aggregator/xp.py` defines XP constants and the level curve

### Dashboard Layer

- `dashboard/src/api.ts` fetches either real or sample data
- `dashboard/src/data-source.ts` manages the real/sample toggle and persistent local storage setting
- `dashboard/src/preferences.ts` manages the dashboard launch preference and syncs it with the local runtime
- `dashboard/src/home.ts` renders the redesigned home as a dominant `Momentum Brief`, proof rail, compact support modules, and deeper-inspection links
- `dashboard/src/app.ts` renders the dashboard shell, supporting tabs, and live refresh behavior
- `aggregator/src/aggregator/runtime.py` serves the local dashboard, exposes `api/runtime-config`, and handles browser-open behavior
- `dashboard/src/types.ts` defines the dashboard state contract, including interpreted insight signals and brief content

## What The UI Currently Shows

- a dominant `Momentum Brief` hero with interpreted headline, summary, validation, cadence, and optional focus direction
- a restrained proof rail that substantiates the brief with selected evidence
- compact `Today` and cadence support modules
- quieter summaries for recent changes and project context
- deeper-inspection entry points for achievements, projects, lifetime stats, and settings
- lifetime statistics, including `XP Sources`, `Languages Edited`, and `Models`
- unlocked, in-progress, and locked achievements
- per-project stats
- real vs sample data mode
- a Settings tab with a toggle for opening Momentum automatically when Cursor starts
- install-time startup registration plus a one-time browser open on first install

## Current Gaps

- signal quality is still conservative and should get richer before the product makes stronger claims
- brief copy quality is still bounded by the strength of the current interpreted signals and recent event evidence
- stage-aware progression is not yet implemented
- comeback and momentum systems still rely on first-pass framing rather than a fuller progression model
- outcome interpretation remains early and should become more project-meaningful over time

## Related Docs

- `implemented-features.md`
- `roadmap-now-next-later.md`
- `../memory/agent-handoff.md`
- `../memory/status-model.md`
