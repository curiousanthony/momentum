# Momentum Home Experience Spec

## Status

- `Status`: planned
- `Scope`: durable product spec for brand language, UX principles, and the home experience redesign
- `Primary audience`: future implementation agents and human reviewers

## Why This Spec Exists

`Momentum` already has a working local collector, aggregator, and premium dark dashboard, but the current home experience is still a stats-first card grid with equal visual weight across level, streaks, today metrics, XP sources, and activity. This spec defines the approved product identity foundation and the target home-screen hierarchy so implementation can move from a generic gamified dashboard toward a more insight-rich, competence-first experience.

This spec is grounded in the current product memory:

- `docs/north-star/mission-and-values.md`: the product promise is that users should understand how they are growing, see proof of progress, and know how to keep leveling up.
- `docs/north-star/product-principles.md`: the product must optimize for competence first, support momentum without guilt, connect behavior to outcomes, and use game mechanics with restraint.
- `docs/product/roadmap-now-next-later.md`: near-term work should prioritize documentation, then insight quality, then progression and momentum, then outcome intelligence.
- `docs/memory/agent-handoff.md`: richer insight mechanics, comeback and momentum design, and stronger outcome interpretation are the next recommended discussions.
- `docs/memory/decision-log.md`: the primary experience should start with the `Growing Builder`, use a blended progression arc, and keep a clean-premium bias.

## Discovery Summary

### Implemented

- The product has a working collector, replay pipeline, and dashboard with raw and derived metrics, achievements, streaks, projects, model usage, and recent events.
- The visual baseline is already dark, premium, and credible rather than playful-first.
- The current home experience is effectively an overview dashboard, not an interpreted brief.

### In Progress Or Approved For Planning

- Documentation and product-memory alignment are the current `Now` priority.
- This home redesign foundation is approved to be specified now so later implementation can follow one durable source of truth.

### Discussing Only, Not Yet Standalone Features

- `Improvement Narratives`
- `Workflow Signature Cards`
- `Focus Prompt Of The Week`
- `Project Growth Stories`
- `Build And Test Confidence Signals`

These ideas may appear inside the home experience as subordinate ingredients of the brief, but this spec does not promote them into separate top-level product surfaces yet. They remain inputs to the approved direction, not independent shipped commitments.

## Product Identity Foundation

### Product Category

`Momentum` is a personal growth and reflection layer for AI-assisted software development.

It is not primarily:

- a productivity analytics dashboard
- a habit tracker
- a gamified badge wall
- a project management system

It should feel like a trusted progress brief for serious builders using Cursor to become more capable, more consistent, and more effective over time.

### Brand Promise

When a user opens `Momentum`, the product should answer three questions quickly:

1. How am I growing?
2. What is the clearest proof of that progress?
3. What should I keep doing next?

### Tone

The tone should be:

- premium
- credible
- calm
- competence-first
- lightly gameful
- encouraging without flattery

The tone should avoid:

- hype language
- juvenile achievement framing
- guilt-driven streak pressure
- pseudo-certainty about outcomes the product cannot truly observe
- coaching language that sounds like a productivity influencer

## Product Language

The terms below are canonical for the redesign and should be used consistently in UI copy, implementation specs, and future docs unless a later decision log replaces them.

### Momentum

`Momentum` means sustained forward motion in the user's AI-assisted development practice.

It is not just daily activity or a fragile streak. It is the combined sense that:

- the user is showing up with some consistency
- their working rhythm is holding
- recent behavior suggests continued progress rather than drift

Implications:

- momentum language should reward continuation and recovery
- momentum should be described over windows, not only single-day snapshots
- losing a streak must not imply losing growth

### Focus

`Focus` means the clearest high-leverage area for the user to pay attention to next.

It is not a long to-do list and not a productivity mandate. In `Momentum`, focus should feel like a single helpful priority the system surfaces after interpreting recent signals.

Implications:

- home should usually present one focus direction, not many
- focus should emerge from evidence, not generic advice
- focus should guide attention without becoming a task manager

### Recovery

`Recovery` means returning to effective motion after interruption, inconsistency, or a rough patch.

Recovery is a positive part of growth, not an exception or failure state.

Implications:

- comeback framing should normalize breaks
- the product should celebrate re-entry and regained rhythm
- messaging should reduce shame and avoid "you fell behind" language

### Validation

`Validation` means credible proof that the user's behavior is producing meaningful progress.

Validation is not praise for its own sake. It is evidence-backed reinforcement such as:

- stronger consistency
- broader tool depth
- better workflow reliability
- clearer project follow-through
- notable improvement against the user's own past behavior

Implications:

- validation copy should point to evidence
- validation should sound earned, not complimentary
- home should surface proof before encouragement

### Confidence

`Confidence` means the user's justified belief that they are becoming more capable with Cursor and can trust their growth trajectory.

Confidence should emerge from insight plus validation, not from inflated scores alone.

Implications:

- confidence is a product outcome, not a standalone widget
- the brief should leave the user feeling more oriented and more capable
- scores and labels are supportive, but interpretation is what creates confidence

## Home Experience Goal

The home screen should become a `Momentum Brief`: a concise interpreted summary of the user's current growth state.

The brief is the top-level experience. Other dashboard surfaces exist to support, substantiate, or let the user inspect the evidence behind the brief.

The home screen should no longer feel like a flat collection of equally important cards. It should feel like a deliberate narrative with one primary takeaway.

## Primary User

The redesign should optimize first for the `Growing Builder`.

Why:

- this stage most strongly wants proof that behavior is turning into capability
- this user needs more interpretation than raw counts
- this stage creates the right bridge toward later momentum, mastery, and outcome layers

The experience must still remain credible for `Momentum Builder` and `Power User` users by avoiding beginner-only language and shallow rewards.

## Momentum Brief Definition

The `Momentum Brief` is the top module on home and the conceptual center of the screen.

It should summarize:

1. current growth state
2. strongest proof signal
3. momentum or recovery state
4. one primary focus direction

The brief is not:

- a generic welcome header
- a large stat cluster
- an exhaustive explanation of all available signals

It is a compact interpretation layer built from existing metrics first, with room for richer interpreted signals later.

## Sparse-Signal And Low-Confidence Behavior

The `Momentum Brief` must be able to say less when the available evidence is weak.

This is a product requirement, not a fallback afterthought. A restrained brief is more credible than a fully populated brief built on noisy or sparse signals.

### When To Enter A Low-Confidence State

Use low-confidence behavior when one or more of these conditions is true:

- the user has too little recent activity to support a meaningful interpretation
- current signals are contradictory enough that the product cannot state a clear pattern with confidence
- the available data is mostly raw counts without enough context for a credible claim
- the product can show activity, but cannot yet infer a trustworthy focus direction

### Low-Confidence Rules

When confidence is low:

- prefer neutral framing over evaluative language
- state observable facts before interpretation
- omit the focus prompt if there is no evidence-backed next direction
- avoid declaring momentum, recovery, improvement, or confidence unless the supporting signal is clear
- allow the brief to be shorter and less complete than the high-confidence state

### Not-Enough-Signal State

The brief may explicitly show a not-enough-signal state when the product can observe recent usage but cannot yet form a useful growth interpretation.

In that state, home should:

- acknowledge that the product is still building a clearer picture
- surface one or two neutral proof modules
- avoid pseudo-insight phrasing
- avoid filling empty space with generic advice

Recommended copy shape:

- headline: neutral and observational
- body: explain that more usage history or consistency is needed before stronger interpretation
- proof: show minimal supporting evidence such as recent activity or current baseline
- focus: omit unless there is an evidence-backed suggestion

### Early-User State

Very early users should receive orientation without overclaiming.

The brief may say that the system is starting to learn the user's working pattern, but it should not pretend to know whether momentum is strong, recovery is needed, or workflow quality is improving until the evidence supports that claim.

### Guardrail

If the product cannot complete the sentence "we believe this because..." with concrete evidence visible on screen, the brief should step down to more neutral language.

## Home-Screen Hierarchy

### Level 1: Momentum Brief

This is the dominant surface on home. It should occupy the highest-visibility position and carry the clearest narrative weight.

Core contents:

- a headline that names the user's current state in credible product language
- a short interpretation sentence that explains what is going well or changing
- a validation block that cites the clearest evidence
- a momentum or recovery block that frames recent cadence
- a single focus prompt that points to the next highest-leverage area

Rules:

- this surface should be readable in under 20 seconds
- it should answer the three brand-promise questions with minimal scanning
- it should prioritize interpretation over quantity of metrics

### Level 2: Supporting Proof Surfaces

These modules sit below or beside the brief and substantiate it.

Their job is to provide inspectable proof without competing with the brief for attention.

Expected supporting roles:

- progress proof: stage, level, XP, or growth trajectory indicators
- cadence proof: streaks, weekly rhythm, or comeback-relevant context
- workflow proof: selected signals about tool depth, editing patterns, or reliability
- outcome-adjacent proof: early, carefully framed indicators tied to builds, tests, or project continuation

Rules:

- these surfaces should be selective, not exhaustive
- every supporting surface should justify why it exists beneath the brief
- if a module does not help explain, validate, or deepen the brief, it does not belong on home

### Current Surface Disposition

The currently implemented home surfaces should move into the redesign as follows unless a later approved implementation plan refines the exact presentation.

#### Today

`Today` should not remain a top-identity card on home.

Disposition:

- keep as a supporting proof module when it helps ground the brief in current activity
- reduce its visual weight relative to the brief
- prefer a concise summary over a large six-metric tile cluster

Why:

- it is useful as recency proof
- by itself it does not explain growth or capability

#### XP Breakdown

`XP breakdown` should move off the primary home path.

Disposition:

- remove from the default home surface
- keep available in a secondary or deeper-inspection view if still useful

Why:

- it is implementation-facing detail more than user-facing interpretation
- it competes with the brief while offering limited direct guidance

#### Language Usage

`Language usage` should move off the primary home path.

Disposition:

- keep as a secondary view or conditional supporting proof module only when it clearly supports a brief claim
- do not keep it as a default equal-weight home card

Why:

- it can occasionally support workflow identity or breadth
- it is rarely one of the most important first-screen answers

#### Model Usage

`Model usage` should move off the primary home path.

Disposition:

- keep as a secondary view or conditional supporting proof module only when it substantiates workflow interpretation
- do not keep it as a default equal-weight home card

Why:

- it is useful for deeper self-understanding
- it is usually supporting evidence, not the primary home narrative

#### Streak And Cadence Signals

Current streak surfaces should remain on home only as cadence proof, not as the main identity module.

Disposition:

- keep as a supporting proof module
- reframe around momentum and recovery rather than pure streak pride

#### Activity Feed

`Recent activity` may stay on home in a lighter form if it helps explain why the brief is saying what it says.

Disposition:

- keep only if concise and signal-rich
- otherwise move to a secondary view

### Level 3: Adjacent Exploration Surfaces

These are deeper-dive destinations such as achievements, projects, and lifetime stats.

Their role is not to define the home experience. Their role is to let users inspect underlying data after the brief has oriented them.

Rules:

- they should remain accessible but visually subordinate on home
- tabs or secondary navigation can continue to house these views
- they should inherit the same language system, but not interrupt the home narrative

## Supporting Surface Roles

### Achievements

Achievements should move from being a major identity surface to a supporting reinforcement surface.

Role:

- recognize meaningful milestones
- add delight and retention texture
- support validation when relevant

Non-role:

- they should not dominate the home screen
- they should not be the primary explanation of growth

### Projects

Projects should support outcome interpretation and continuity.

Role:

- show where effort is concentrating
- help connect behavior to real work
- provide context when the brief references project-level movement

Non-role:

- they should not turn home into a project management workspace

### Lifetime Stats

Lifetime stats should become archival evidence, not the opening experience.

Role:

- support self-comparison over time
- provide confidence that growth has substance

Non-role:

- they should not be the main decision-making layer on home

### Recent Activity

Recent activity should support recency and explain why the brief is saying what it says.

Role:

- show notable recent signals
- reinforce trust that the system is grounded in observed events

Non-role:

- it should not read like a noisy event log if a more concise evidence summary would work better

## Information Architecture Rules

The home screen should follow this order of importance:

1. interpretation
2. proof
3. orientation for next action
4. deeper inspection

This means:

- the most prominent copy should be narrative, not metric labels
- key numbers should support a claim, not act as the claim
- adjacent cards must visually reinforce the top narrative instead of competing with it

## UX Principles For Implementation

### 1. Interpretation Before Inventory

Start with what the signals mean, not with every available metric.

Implementation consequence:

- prefer a small number of interpreted modules over many neutral cards

### 2. Proof Before Praise

Encouragement should be backed by observable evidence.

Implementation consequence:

- whenever the UI says the user is improving, regaining rhythm, or building confidence, it should point to why

### 3. Recovery Is First-Class

Breaks and rough patches are part of the intended user journey.

Implementation consequence:

- home must be able to communicate healthy comeback framing, not only streak extension

### 4. Self-Comparison Over Abstract Scores

Numbers matter most when they help the user compare against their own recent baseline.

Implementation consequence:

- prefer deltas, shifts, and trend framing over isolated totals where possible

### 5. One Strong Next Step

The home experience should usually recommend one primary focus direction.

Implementation consequence:

- avoid multiple competing prompts, quests, or calls to action on the main surface

### 6. Premium Restraint

The interface should feel elegant and intentional, not busy or reward-saturated.

Implementation consequence:

- use emphasis sparingly
- reserve bright accent energy for genuinely important states
- keep copy concise and high-signal

### 7. Outcome Honesty

The product can suggest outcome-adjacent confidence signals, but it must not overclaim shipped value from incomplete evidence.

Implementation consequence:

- use language like "signals", "suggests", and "supports confidence" where certainty is not justified

## Visual And Interaction Principles

These principles should govern implementation decisions in the current dashboard stack.

### Hierarchy

- the brief should be visually largest and most prominent on home
- supporting proof modules should have lower contrast and lower visual weight than the brief
- archival or secondary views should be clearly subordinate

### Density

- keep the home screen tighter and more curated than the current equal-weight grid
- favor fewer modules with better synthesis over more modules with partial value

### Motion And Feedback

- motion should be subtle and premium
- celebratory moments may exist, but should stay restrained and earned

### Language

- headlines should sound reflective and precise
- avoid exaggerated motivational copy
- avoid jargon that would make the product feel like an analytics console

## Current-Stack Constraints

This spec should be implemented against the current architecture, not against imagined systems.

Known constraints:

- `dashboard/src/app.ts` currently renders tabbed, card-based overview surfaces
- `dashboard/src/styles/app.css` already establishes a strong dark premium baseline worth preserving
- `dashboard/src/types.ts` does not yet expose an interpreted brief or signal layer
- `aggregator/src/aggregator/replay.py` and `state.py` currently compute raw metrics, streaks, achievements, recent events, and supporting summary data rather than explicit home interpretations

Implementation guidance:

- start by composing the brief from existing reliable signals where possible
- add interpreted state fields only when the brief requires durable logic or clearer contracts
- preserve credibility by keeping derived claims simple before adding heavier inference

## Out Of Scope For This Spec

This spec does not define:

- the exact final visual layout dimensions
- the final data schema for interpreted brief fields
- stage inference mechanics
- a full comeback scoring algorithm
- a complete outcome intelligence system
- a quest or coaching framework

Those are implementation or follow-on specs. This document defines the governing product language and home experience rules they must satisfy.

## Approval-Level Decisions Captured Here

- home is centered on a `Momentum Brief`, not an equal-weight dashboard grid
- the brief is interpretation-first and must answer growth, proof, and next-step questions quickly
- achievements, projects, lifetime stats, and activity are supporting or adjacent surfaces, not the primary home identity
- the canonical language for `momentum`, `focus`, `recovery`, `validation`, and `confidence` is defined here
- the redesign should optimize first for the `Growing Builder` while remaining credible for more advanced users
- future implementation should preserve premium restraint and outcome honesty

## Implementation Checklist For Future Tasks

Use this spec as the reference before making home redesign changes. Future implementation plans should explicitly answer:

1. What is the brief headline, validation proof, momentum or recovery signal, and focus direction?
2. Which current modules stay on home, which become secondary, and which are removed or condensed?
3. Which interpretations can be composed in the UI from existing state, and which require new aggregator fields?
4. How does the final screen maintain premium hierarchy and avoid reverting to equal-weight cards?
