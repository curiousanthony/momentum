---
name: momentum-product-memory
description: Use when starting feature work or editing existing behavior in Momentum and you need to determine what is already implemented, what is in progress, and what should come next from the repo's product-memory docs before touching code.
---

# Momentum Product Memory

## Overview

`docs/` is the durable product memory for this repo. Treat product docs as the source of truth for intent, status, and next-step selection; treat code as the source of truth for implementation details only after the docs say a direction is in play.

## Required Reading Order

Read these before proposing or planning feature work:

1. `docs/README.md`
2. `docs/north-star/mission-and-values.md`
3. `docs/north-star/product-principles.md`
4. `docs/personas/progression-stages.md`
5. `docs/research/design-principles-summary.md`
6. `docs/product/current-state.md`
7. `docs/product/implemented-features.md`
8. `docs/memory/agent-handoff.md`

Read these next when choosing or validating the next task:

- `docs/product/roadmap-now-next-later.md`
- `docs/product/feature-opportunities.md`
- `docs/product/open-questions.md`
- `docs/memory/status-model.md`
- `docs/memory/decision-log.md`
- `specs.md` for implementation-oriented system intent

## Discovery Output

Before touching code, summarize:

- what is already implemented
- what is currently only `discussing`, `planned`, or otherwise not yet built
- what the docs say should come next
- which open questions or decisions could block implementation

Base that summary on docs, not code salience. Cite the exact docs that support each conclusion.

## Choosing The Next Task

Use this order:

1. `agent-handoff.md` for current direction and next recommended discussions
2. `roadmap-now-next-later.md` for priority order
3. `feature-opportunities.md` for candidate work items
4. `open-questions.md` and `decision-log.md` for blockers and constraints
5. code only to verify feasibility after the docs point at a direction

If docs do not make the next step explicit, do not invent one from nearby code. Move to brainstorming with the human.

Treat a task as docs-explicit only when one of these is true:

- the human has already approved that direction during brainstorming
- the relevant work is already represented in product memory as `planned`, `building`, or `shipped`

A roadmap bullet, `Next` item, or `discussing` opportunity is not approval.

## Source Of Truth Rules

Use this precedence:

1. `docs/` product-memory files for roadmap, status, intent, and next-step selection
2. `docs/product/current-state.md` and `docs/product/implemented-features.md` for documented current behavior
3. source code for factual implementation details and feasibility
4. `specs.md` for architecture and older implementation intent that does not override newer product-memory docs

If code contains a partial implementation of a feature that docs still treat as `discussing`, `Next`, unresolved, or absent, do not treat that code as approval. Treat it as one of:

- experimental or incomplete work
- doc drift that must be surfaced
- evidence that the next task may be to update product memory first

## Docs-Vs-Code Conflict

If docs and code conflict in a way that changes the recommendation:

1. stop before proposing implementation
2. describe the conflict explicitly
3. give one default recommendation
4. ask one focused question only if needed to resolve direction

If a current-state or implemented-features doc is stale, call that out directly. In this repo, fixing stale product memory can itself be the next task.

## Status Rules

Use every status from `docs/memory/status-model.md` exactly. Do not restate or invent local variants. Do not treat roadmap bullets or opportunity entries as approved implementation plans.

## Questions To Ask The Human

The human is a brainstorming companion, not the backlog manager. Prefer one focused question with a default recommendation when needed.

Ask only when:

- multiple doc-aligned directions are plausible
- `open-questions.md` leaves a material product choice unresolved
- docs and code conflict in a way that changes the recommendation

## Common Mistakes

- Inferring roadmap from code hotspots, TODOs, or recent edits
- Treating `discussing` items as ready to build
- Ignoring `agent-handoff.md` because another file looks more concrete
- Using implementation feasibility as proof that a feature is the right next step
- Treating partial code for a future idea as product approval
- Letting a stale current-state doc quietly stand without surfacing it

## Red Flags

- "I can infer the roadmap from the code."
- "The docs are probably stale."
- "I already know what the next feature is."
- "This opportunity is listed, so it is approved."
- "The code already has most of it, so I can finish it."

Any of these means: stop, return to the docs, and produce the discovery summary first.
