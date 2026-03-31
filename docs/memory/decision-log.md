# Decision Log

## 2026-03-31

### Adopt AI-Native Builder Journey

- `Decision`: position the product as a personal progression system for the AI-native builder
- `Why`: this best combines insight, motivation, and empowerment without reducing the dashboard to either plain analytics or shallow gamification

### Start With Growing Builder

- `Decision`: design the primary experience for the `Growing Builder` stage first
- `Why`: this is the strongest fit for developers leveling up with Cursor and creates a natural arc toward `Power User`

### Use A Blended Progression Arc

- `Decision`: progression should start with capability mastery, reinforce consistency, and later emphasize project outcomes
- `Why`: it mirrors how developers actually evolve with AI tools and supports the MMORPG-style growth framing

### Use Hybrid Tone With Clean-Premium Bias

- `Decision`: keep the product credible and premium first, with restrained gameful energy layered underneath
- `Why`: this broadens appeal beyond gamer culture while still preserving delight and motivation

### Prioritize Deep Gamification

- `Decision`: favor competence, insight, progression, and recovery over points, badges, and leaderboards alone
- `Why`: the research and target audience both suggest that shallow gamification would be weaker and less trustworthy

### Add Durable Project Memory

- `Decision`: maintain a structured docs system for north star, personas, research, product state, and memory
- `Why`: future sessions and future agents need a canonical source of context that survives chat boundaries

### Approve Momentum Brief Home Direction

- `Decision`: the home redesign should center on a `Momentum Brief` instead of the current equal-weight stats dashboard
- `Why`: the product promise is to help users understand growth, see proof of progress, and know what to keep doing next, which requires interpretation-first hierarchy rather than a flat grid of cards

### Make Home Interpretation-First And Evidence-Backed

- `Decision`: home should prioritize interpreted growth state, validation, and one evidence-backed focus direction, while stepping down to neutral or not-enough-signal framing when confidence is low
- `Why`: this preserves credibility for serious builders and prevents the product from overstating weak or sparse signals

### Relegate Raw Metric Modules To Supporting Or Secondary Roles

- `Decision`: current modules like `Today`, streaks, activity, projects, and lifetime stats should support the brief, while `XP breakdown`, language usage, and model usage should move to secondary or conditional roles unless they directly substantiate the brief
- `Why`: raw metric inventory is useful as proof and inspection, but it should not define the primary home experience

### Choose Editorial Brief As The Home Visual Direction

- `Decision`: Task 2 selects `Direction A: Editorial Brief` from `docs/specs/momentum-home-visual-directions.md` as the default implementation target for the redesigned home
- `Why`: this direction most clearly expresses `Momentum` as a trusted progress brief for serious builders, creates the cleanest break from the current equal-weight card grid, and best matches the approved premium, credible, competence-first tone

### Carry Forward Editorial Brief Guardrails

- `Decision`: implementation should preserve hero-first hierarchy, a restrained evidence rail, compact supporting summaries, and low-confidence states that say less instead of filling space
- `Why`: these guardrails keep the chosen direction from degrading into a reorganized telemetry dashboard and preserve the approved `Momentum Brief` hierarchy during Task 4 implementation

### Open Momentum On First Install

- `Decision`: first install should start the local dashboard runtime and open Momentum in the default browser once automatically
- `Why`: users should feel the product immediately after setup instead of needing to discover and repeat a manual local-server workflow

### Keep Recurring Auto-Open Opt-In

- `Decision`: opening Momentum on later Cursor starts should remain user-controlled and default off after the first-install experience
- `Why`: this preserves user sovereignty and keeps the product accessible without turning it into an intrusive repeated browser-open behavior

### Ship The Editorial Brief Home As The Default Experience

- `Decision`: the dashboard home should now default to the shipped `Editorial Brief` hierarchy rather than the original stats-first card grid
- `Why`: the redesigned home is live locally, better matches the north-star promise, and more clearly orients users around interpretation, proof, and next direction before deeper inspection

### Keep Raw Detail Available But Off The Main Home Path

- `Decision`: XP source detail, language usage, model usage, and broader lifetime data should remain available in supporting or deeper views instead of reclaiming first-screen priority
- `Why`: these details still matter for inspection and self-understanding, but the main home path is stronger when it stays centered on the brief rather than metric inventory

### Extend State With Interpreted Insights And Brief Payload

- `Decision`: the aggregator/state contract should expose a durable interpreted `insights` object with signal strength, structured signals, and a `brief` payload for home rendering
- `Why`: this keeps home interpretation factual, reusable, and consistent across the dashboard instead of relying on ad hoc UI-only wording built directly from raw counts
