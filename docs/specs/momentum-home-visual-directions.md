# Momentum Home Visual Directions

## Status

- `Status`: planned
- `Scope`: durable visual-direction spec for Task 2 of the Momentum home redesign plan
- `Primary audience`: future implementation agents and human reviewers validating home hierarchy before UI work

## Why This Exists

`docs/specs/momentum-home-experience.md` defines the approved product language, hierarchy rules, and supporting-surface roles for the new home. This document turns that direction into a small set of concrete visual approaches so implementation can choose a clear hierarchy and avoid drifting back into an equal-weight dashboard grid.

This document is grounded in:

- `docs/specs/momentum-home-experience.md`: approved `Momentum Brief` hierarchy, supporting-surface roles, and current-stack constraints
- `docs/north-star/mission-and-values.md`: users should understand growth, see proof, and know what to keep doing next
- `docs/north-star/product-principles.md`: competence first, momentum without guilt, and game mechanics with restraint
- `docs/personas/progression-stages.md`: primary optimization target is the `Growing Builder`
- `docs/research/design-principles-summary.md`: premium, credible, lightly gameful, self-comparison-first design
- `docs/memory/decision-log.md`: clean-premium bias and interpretation-first home are already approved

## Discovery Summary

### Implemented

- The current product already has a dark, premium card system in `dashboard/src/styles/app.css`.
- The current home is still an overview grid led by equal-weight cards for level, streak, today, XP sources, activity, language, and models.
- Existing state already provides enough raw proof surfaces to support a first-pass interpreted home later.

### Planned

- The approved next step is to validate concrete home hierarchy directions before broad implementation.
- The home is already approved to center on a `Momentum Brief`, with supporting proof surfaces beneath it.

### Discussing Only

- `Improvement Narratives`
- `Workflow Signature Cards`
- `Focus Prompt Of The Week`
- `Project Growth Stories`
- `Build And Test Confidence Signals`

These may appear only as subordinate ingredients of the chosen home direction. This document does not promote them into separate required top-level features.

## Evaluation Criteria

Each direction should be judged against the following criteria before implementation:

1. `Hierarchy clarity`: can a user identify the main takeaway in under 20 seconds?
2. `Interpretation before inventory`: does the first screen lead with meaning, not counts?
3. `Premium feel`: does the screen feel calm, credible, and intentional rather than busy or toy-like?
4. `Proof credibility`: are claims visibly tied to evidence on the same screen?
5. `Focus discipline`: is there one dominant next-step area instead of multiple competing prompts?
6. `Supporting-surface restraint`: do proof modules stay visibly subordinate to the brief?
7. `No equal-weight card sprawl`: could this accidentally collapse back into the current grid if implemented literally?
8. `Current-stack fit`: can the direction be built incrementally in the current dashboard shell without needing a brand-new app architecture?

## Shared Layout Rules

All directions below assume the same information hierarchy:

1. `Momentum Brief`
2. supporting proof
3. one oriented next move
4. deeper inspection paths

All directions should preserve these common guardrails:

- The brief is the largest surface on home.
- Supporting modules answer "why should I trust this brief?"
- `Today`, streaks, and activity become concise evidence, not identity cards.
- `XP breakdown`, default language usage, and default model usage move off the main home path.
- Accent energy is sparse and meaningful, never sprayed across every module.
- Low-confidence states are allowed to be shorter and calmer than high-confidence states.

## Direction A: Editorial Brief

### Summary

This direction makes home feel like a premium weekly note or executive summary. The brief is a large narrative surface with a strong headline, one interpretation paragraph, and a tidy evidence rail beneath it. Supporting modules read like annotations rather than dashboard cards.

### IA Sketch

```text
Home
|
+-- Momentum Brief hero
|   +-- state headline
|   +-- interpretation sentence
|   +-- proof statement
|   +-- momentum/recovery line
|   +-- single focus prompt
|
+-- Evidence rail
|   +-- progress proof
|   +-- cadence proof
|   +-- workflow proof
|
+-- Supporting detail row
|   +-- recent change summary
|   +-- project focus summary
|
+-- Deeper inspection links
    +-- achievements
    +-- projects
    +-- lifetime stats
```

### Structure And Hierarchy

- The top third of the page is dominated by one wide brief panel.
- The brief uses prose first, with one or two compact numeric anchors embedded inside supporting lines.
- Supporting proof appears as a low-height horizontal strip or quiet stacked rail.
- Lower sections are short summaries with clear "inspect more" affordances rather than full dashboards.

### Emotional Tone

- calm
- premium
- reflective
- confident without showing off

### Supporting Module Treatment

- `Today`: reduced to a compact recency note or mini-proof line
- `Streaks`: reframed as cadence context inside a recovery/momentum support block
- `Activity`: condensed to 2-3 notable events, not a feed-first card
- `Projects`: one focused project summary, not a full table
- `Achievements`: moved out of the main scan path

### Likely Strengths

- Best matches the "trusted progress brief" framing from the approved spec.
- Most effective at avoiding card sprawl.
- Strongest fit for premium, competence-first brand expression.

### Likely Risks

- Could become too copy-heavy if the signal layer is weak.
- Requires disciplined writing so the hero does not feel vague.
- If over-minimal, some users may miss concrete anchors at a glance.

## Direction B: Command Center Brief

### Summary

This direction keeps more of the dashboard DNA, but reorganizes it around a dominant hero and a right-side proof column. It feels like a higher-end operational console: structured, precise, and information-dense, but no longer flat.

### IA Sketch

```text
Home
|
+-- Hero row
|   +-- wide Momentum Brief
|   +-- proof column
|       +-- cadence
|       +-- progress
|       +-- workflow quality
|
+-- Secondary grid
|   +-- recent changes
|   +-- project focus
|   +-- conditional outcome signal
|
+-- Navigation row
    +-- achievements
    +-- projects
    +-- lifetime stats
```

### Structure And Hierarchy

- The brief spans roughly two-thirds of the first row.
- A narrow proof column holds 2-3 stacked supporting cards with reduced contrast.
- The lower half still uses cards, but with stronger role separation than the current grid.
- The layout remains familiar to the current stack and likely easiest to wire incrementally.

### Emotional Tone

- credible
- composed
- analytical
- slightly more "serious console" than "editorial brief"

### Supporting Module Treatment

- `Today`: a compact proof card in the right column or lower grid
- `Streaks`: one cadence card, visually subordinate
- `Activity`: a trimmed recent-changes card
- `Projects`: one featured project card plus link to full projects view
- `Achievements`: stays outside the first viewport unless especially relevant

### Likely Strengths

- Strong implementation fit with the current dark card system.
- Easier transition from the existing UI without a full visual language rewrite.
- Gives users faster access to proof metrics while still elevating the brief.

### Likely Risks

- Most vulnerable to slipping back into equal-weight card behavior.
- Can feel "reorganized dashboard" rather than "new product experience" if contrast rules are not strict.
- More density can weaken the calm, premium mood.

## Direction C: Guided Narrative Stack

### Summary

This direction turns home into a sequential vertical story: state, proof, next move, then supporting context. It feels closer to a productized reflection flow than a dashboard, while still using lightweight cards and sections.

### IA Sketch

```text
Home
|
+-- Momentum Brief
|
+-- Why we believe this
|   +-- strongest proof
|   +-- momentum/recovery
|
+-- What to keep doing
|   +-- single focus block
|   +-- optional caution or confidence note
|
+-- Context below
    +-- recent changes
    +-- project focus
    +-- deeper links
```

### Structure And Hierarchy

- The page is a narrow, vertically stacked narrative with large spacing and clear section labels.
- Each section answers one question in sequence.
- Supporting surfaces are embedded in the story instead of arranged as a dashboard row.
- The rhythm is slower, with more whitespace and fewer simultaneous decisions.

### Emotional Tone

- calm
- thoughtful
- lightly guided
- less dashboard-like, more reflective

### Supporting Module Treatment

- `Today`: folded into "Why we believe this"
- `Streaks`: folded into cadence/recovery evidence
- `Activity`: transformed into "recent changes that shaped this brief"
- `Projects`: becomes context after the focus block
- `Achievements`: pushed behind deeper exploration

### Likely Strengths

- Clearest answer to the approved narrative order: interpretation, proof, next move, deeper inspection.
- Naturally discourages equal-weight card sprawl.
- Strong fit for low-confidence and sparse-signal states because sections can collapse cleanly.

### Likely Risks

- Could feel too linear for users who want rapid scanning of multiple signals.
- Requires more careful responsive layout work so it does not become a tall wall of copy.
- If the supporting evidence is too collapsed, advanced users may feel under-served.

## Direction Comparison

| Direction | Best at | Main risk | Stack fit |
| --- | --- | --- | --- |
| `A. Editorial Brief` | premium identity and hierarchy discipline | becoming too copy-led | medium-high |
| `B. Command Center Brief` | incremental implementation from current dashboard | reverting to card sprawl | highest |
| `C. Guided Narrative Stack` | narrative clarity and low-confidence handling | slower scan speed | high |

## Recommended Direction

Recommend `Direction A: Editorial Brief`.

### Why This Is The Best Fit

- It most directly expresses the approved product category: a trusted progress brief for serious builders, not a telemetry dashboard.
- It best supports the `Growing Builder`, who wants interpreted evidence of capability growth rather than more raw stats.
- It creates the strongest visual break from the current equal-weight card grid without demanding a fundamentally new frontend architecture.
- It preserves the current dark premium baseline while using restraint instead of adding more chrome.
- It gives Task 4 a clear hierarchy to implement: one dominant narrative surface, one quiet proof rail, and a small number of supporting summaries.

### Why Not The Others

- `Direction B` is the safest mechanically, but it is too easy to implement in a way that still feels like the old dashboard with a larger hero card.
- `Direction C` is strong conceptually, but it risks over-serializing the experience and asking the user to read too much before gaining orientation.

## Recommended Direction Implementation Guardrails

Task 4 should treat these as hard constraints unless a later approved plan says otherwise.

### 1. Hero Dominance

- The `Momentum Brief` should occupy the full primary width on desktop.
- It should feel like one composed surface, not a cluster of nested mini-cards.
- The first scan should reveal headline, interpretation, proof, momentum/recovery, and focus without scrolling on common desktop widths.

### 2. Evidence Rail Discipline

- Supporting proof should appear in a low-height strip or quiet stack directly beneath or beside the brief.
- Limit first-screen proof to 3 modules max.
- Each proof module should validate a specific brief claim.
- Avoid six-tile stat clusters on home.

### 3. Card Treatment

- Use fewer, larger surfaces rather than many small cards.
- Supporting cards should use lower contrast, softer borders, and less accent color than the brief.
- Do not give every module a bright metric number as its visual center.

### 4. Density

- Default home should fit in roughly 4-6 meaningful surfaces, not a dashboard wall.
- Use compact summaries for `Today`, cadence, recent changes, and project context.
- Reserve deeper data like XP sources, full project tables, and language/model distributions for secondary views.

### 5. Copy Shape

- Headline: 4-10 words naming the current state
- Interpretation: 1 concise sentence
- Proof: 1 sentence or compact bullet citing observable evidence
- Momentum/recovery: 1 short line
- Focus: exactly 1 primary recommendation when confidence is high enough

### 6. Accent Usage

- Keep the dark premium base from `dashboard/src/styles/app.css`.
- Use accent gradients or bright color only for state emphasis, not as persistent decoration.
- Avoid achievement-style celebratory styling on the home hero.

### 7. Supporting Surface Rules

- `Today`: brief recency proof only
- `Streaks`: cadence context only
- `Recent activity`: notable changes only, max 3 items in default home
- `Projects`: one focused project summary, not the full project table
- `Achievements`: secondary destination, not home centerpiece
- `Language/model usage`: secondary unless directly supporting a claim

### 8. Low-Confidence Behavior

- Allow the brief to shrink when evidence is weak.
- Omit focus if no evidence-backed next move exists.
- Prefer neutral observational copy over motivational framing.
- Do not add filler modules to "balance" the page when the brief is intentionally sparse.

## Sample Copy Shapes For The Recommended Direction

### High-Confidence

- headline: `Your workflow is getting steadier`
- interpretation: `Recent sessions suggest stronger follow-through across meaningful coding work, not just more activity.`
- proof: `You sustained active days, broadened tool usage, and kept project work moving in the same period.`
- momentum: `Momentum looks stable this week, with no sign that a slower day broke the pattern.`
- focus: `Keep reinforcing the workflows that lead to completed sessions and build/test follow-through.`

### Recovery

- headline: `You're back in motion`
- interpretation: `Recent activity suggests healthy re-entry after a gap, with enough consistency to treat this as recovery rather than a one-off spike.`
- proof: `Activity resumed across multiple recent sessions and the cadence signal is improving against your prior lull.`
- momentum: `This looks like recovery, not reset.`
- focus: `Protect repeatability this week rather than chasing volume.`

### Low Confidence

- headline: `Momentum is still taking shape`
- interpretation: `There is recent activity, but not enough consistent evidence yet to draw a strong growth read.`
- proof: `The clearest signals so far are recent sessions and baseline project activity.`
- momentum: `A clearer pattern should emerge with more consistent usage history.`
- focus: omit

## Self-Review Against The Approved Spec

### Spec Fit Check

- `Momentum Brief` remains the dominant home surface: pass
- interpretation comes before metric inventory: pass
- supporting proof surfaces stay subordinate: pass
- one primary focus direction only: pass
- premium, credible, calm tone: pass
- recovery and low-confidence states can say less: pass
- raw metric modules do not retake primary-home status: pass

### Residual Risks

- The recommended direction depends on disciplined copywriting and layout restraint; a careless implementation could still add too many supporting cards.
- The current dashboard stack is card-oriented, so Task 4 will need explicit CSS hierarchy rules to keep the brief from becoming just another card.
- The first implementation should avoid overpromising with inferred language until Task 3 defines the signal contract.

## Decision For Task 4

Use `Direction A: Editorial Brief` as the default implementation target.

Task 4 may borrow limited structural ideas from `Direction B` where needed for responsive behavior or incremental migration, but it should not preserve a dashboard-first first impression. If implementation pressure forces a choice between more metrics and clearer hierarchy, prefer clearer hierarchy.
