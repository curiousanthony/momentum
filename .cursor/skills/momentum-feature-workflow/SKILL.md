---
name: momentum-feature-workflow
description: Use when proposing, planning, or implementing a new feature or behavioral change in Momentum. Enforces discovery from product-memory docs, brainstorming with the human when needed, and mandatory Plan Mode before any code changes.
---

# Momentum Feature Workflow

## Overview

Feature work in `Momentum` must leave behind durable memory. Discovery, brainstorming, planning, and implementation are separate phases. The plan stays authoritative; implementation is disposable.

## Hard Gates

- Do not edit code during discovery.
- Do not edit code during brainstorming.
- Do not implement from an implicit plan in your head.
- Do not skip Plan Mode because the task looks small.
- Do not use code as the roadmap.
- Do not treat prototypes, spike edits, or "small exploratory changes" as exempt from this workflow.

## Required Sequence

1. Use `momentum-product-memory` to produce the docs-based discovery summary.
2. If the next step is not already clear and approved, brainstorm with the human.
3. After brainstorming, switch to Plan Mode and write or refine the implementation plan before touching code.
4. Implement only after the plan exists as a durable artifact.
5. If implementation goes off track, discard the code changes and return to the plan instead of improvising a new direction in code.

`approved` means either:

- the human approved the direction during brainstorming, or
- the work is already documented as `planned`, `building`, or `shipped` and no relevant open question blocks it

`approved` does not mean:

- a `Next` roadmap bullet
- a `discussing` opportunity
- obvious nearby code
- a feature that feels small enough to infer

## Brainstorming Rules

For new features or behavioral changes, use a short design checkpoint even when scope is small.

- Offer a default recommendation grounded in the docs.
- Ask one focused question at a time when clarification is required.
- Use the human mainly as a reviewer, tie-breaker, or constraint source.
- If `open-questions.md` contains a relevant unresolved product decision, surface it before planning.

## Plan Mode Rules

Plan Mode is mandatory before implementation.

- Switch to Plan Mode after brainstorming or after confirming a docs-explicit task.
- Start from `.cursor/plans/TEMPLATE.plan.md` when creating a new plan artifact.
- Write the implementation plan into the repo's plan system, such as `.cursor/plans/*.plan.md`.
- The plan must name the target outcome, touched systems, constraints, and verification steps.
- The plan must point back to the docs evidence that justified the task.
- Treat the plan as the durable source of truth during implementation.

If you cannot point to the written plan, you are not ready to code.

## Working From Existing Features

This workflow also applies when editing an existing feature.

- Read `docs/product/current-state.md` and `docs/product/implemented-features.md` first.
- Confirm the behavior really exists today.
- Check whether the proposed edit changes product behavior or only fixes a defect.
- If the edit changes behavior, run the same brainstorm -> Plan Mode -> implementation sequence.
- If the task is a defect fix that changes user-visible behavior, wording, thresholds, ordering, or recommendations, treat it as a behavior change.
- If the task changes visible layout, emphasis, defaults, affordances, or other dashboard UX, treat it as a UX change.
- Only purely internal, non-behavioral maintenance may skip brainstorming; it still needs a written plan before code if it changes system design or touches multiple areas.

## Conflict Handling

If code and docs disagree about what exists or what should happen next:

- stop and surface the conflict before planning
- do not use partial future-facing code as roadmap approval
- prefer product-memory docs for direction and code for factual implementation details
- if the docs are stale only in factual description, update the relevant product-memory docs before implementation
- if resolving the stale docs requires a product-direction choice, run the normal brainstorm -> Plan Mode flow first, then update the docs from the approved plan

## Memory Updates After Work

Keep repo memory current after planning or implementation:

- update `docs/product/implemented-features.md` when shipped behavior changes
- update `docs/product/current-state.md` when the factual product snapshot changes
- update `docs/memory/agent-handoff.md` when priorities, next steps, or current constraints change
- update `docs/memory/decision-log.md` when a meaningful product decision is made
- use `docs/memory/status-model.md` when changing statuses in `docs/product/`

## Common Mistakes

- "I'll make one small exploratory change first."
- "Minimal human involvement means I should avoid questions."
- "I already have the plan in my head."
- "I'll update the docs after the code settles."
- "This is just wiring up data that already exists."
- "This looks like a defect, so I can skip planning."
- "I'll make a prototype first and formalize it later."

## Quick Reference

Before code:

- docs discovery complete
- brainstorming complete or explicitly unnecessary because the docs-approved task is already clear
- Plan Mode entered
- written plan exists

After code:

- verification complete
- product-memory docs updated
- next recommended step recorded if it changed
