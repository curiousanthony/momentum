# Agent Handoff

## Current Direction

`Momentum` is being positioned as a premium, insight-rich progression system for the AI-native builder. The product should help developers grow from early experimentation into confident, high-leverage Cursor usage.

The approved home redesign direction is now live in the dashboard. `Task 2` selected `Direction A: Editorial Brief` from `../specs/momentum-home-visual-directions.md`, and the shipped home now follows that hierarchy: one dominant `Momentum Brief` hero, a restrained proof rail, compact `Today` and cadence support, quieter recent-changes and project-context summaries, and deeper-inspection links for secondary views. Future work should treat the shipped implementation plus `../specs/momentum-home-experience.md` as the reference for home hierarchy, canonical product language, sparse-signal behavior, and the supporting-versus-secondary weighting.

## Implemented Baseline

- local collector pipeline exists
- aggregator exists
- dashboard UI exists
- install now starts a local dashboard runtime and opens Momentum once on first install
- users can opt into opening Momentum automatically on future Cursor starts from the dashboard `Settings` tab
- home is now centered on a `Momentum Brief` instead of an equal-weight stats dashboard
- the aggregator/state contract now includes interpreted `insights` signals and a `brief` payload
- XP, levels, streaks, achievements, projects, lifetime stats, model usage, language usage, and recent activity still exist as supporting or deeper-inspection views

## Active Priorities

- keep future work aligned with competence-first, insight-first gamification
- preserve a clear distinction between shipped behavior and future opportunities
- keep install-time accessibility high so new users can reach the dashboard immediately after setup
- improve signal quality so the brief can say more only when evidence genuinely supports it
- strengthen brief copy and interpretation from better underlying data, not from looser wording
- keep deeper views available without letting raw metrics retake the main home path

## Next Recommended Discussions

- richer insight mechanics that explain improvement more clearly within the shipped `Momentum Brief`
- stronger signal inputs and evidence selection so brief copy becomes more specific without becoming less honest
- comeback and momentum system design that preserves low-pressure recovery framing
- stage-aware progression mechanics layered onto the brief without overwhelming the home
- stronger outcome-oriented interpretation that remains evidence-backed and project-aware

## Important Constraints

- keep tone premium and credible
- avoid shallow gamification and public-leaderboard-first thinking
- compare users primarily against their past selves
- treat docs in this tree as the durable context layer for future agent sessions
- do not treat sparse or contradictory signals as justification for strong narrative claims on home
- do not let raw metric cards retake primary-home status without revisiting the approved spec
- keep the `Momentum Brief` as one dominant hero surface, not a cluster of peer cards
- keep first-screen proof to a restrained evidence rail or quiet supporting stack, not a broad metric grid
- keep `Today`, streaks, recent activity, and project context compact and subordinate on home
- keep `XP breakdown`, default language usage, and default model usage off the main home path unless they directly support the brief; they still belong in deeper inspection
- allow low-confidence states to be shorter and calmer instead of filling space with weak claims

## Canonical References

- `../product/current-state.md`
- `../product/implemented-features.md`
- `../specs/momentum-home-experience.md`
- `../specs/momentum-home-visual-directions.md`
- `decision-log.md`
- `status-model.md`

