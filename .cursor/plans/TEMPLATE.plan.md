---
name: <Plan Name>
overview: >
  <One-paragraph summary of the approved outcome, why it matters, and the user-visible result.
  Keep this aligned with product-memory docs rather than code salience.>
docs_evidence:
  - path: docs/memory/agent-handoff.md
    why: <Why this file supports the task>
  - path: docs/product/roadmap-now-next-later.md
    why: <Why this file supports the task>
  - path: docs/product/feature-opportunities.md
    why: <Why this file supports the task>
open_questions:
  - <Relevant unresolved question from docs/product/open-questions.md, or "none">
decision_constraints:
  - <Constraint from north-star, product principles, decision log, or status model>
touched_systems:
  - <collector|aggregator|dashboard|docs|other>
verification:
  - <Command or check that proves the work is correct>
todos:
  - id: example-task
    content: <Concrete implementation step>
    status: pending
isProject: true
---

# <Plan Name>

## Goal

<State the specific outcome in product terms.>

## Docs Basis

- `docs/memory/agent-handoff.md`: <current direction or next recommended discussion>
- `docs/product/roadmap-now-next-later.md`: <priority or phase this work belongs to>
- `docs/product/feature-opportunities.md`: <candidate task or opportunity, if applicable>
- `docs/product/open-questions.md`: <blocking question, or state "none">
- `docs/memory/decision-log.md`: <relevant prior decision, or state "none">
- `specs.md`: <implementation fit, only if still aligned with newer product-memory docs>

## Scope

### In scope

- <What this plan will deliver>

### Out of scope

- <What this plan intentionally will not do>

## Implementation Notes

- <Target files or systems>
- <Data flow or architecture notes>
- <Risks, caveats, or migration notes>

## Verification

- <Tests, builds, screenshots, or doc checks required before completion>

## Task Checklist

- [ ] Replace this item with the first real task
- [ ] Add one checklist item per meaningful step

## Memory Updates Required

- [ ] Update `docs/product/current-state.md` if the factual product snapshot changes
- [ ] Update `docs/product/implemented-features.md` if shipped behavior changes
- [ ] Update `docs/memory/agent-handoff.md` if priorities or next steps change
- [ ] Update `docs/memory/decision-log.md` if a meaningful decision is made
- [ ] Use `docs/memory/status-model.md` when changing statuses
