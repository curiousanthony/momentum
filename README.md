# Momentum

Momentum helps developers unlock achievements, track their progress, and maintain momentum while using agentic coding tools.

Gamified local dashboard for agentic coding tools: hooks → `events.jsonl` → aggregated `state.json` → web UI.

## Prerequisites

- Python 3.11+
- [Bun](https://bun.sh) 1.x (for the dashboard)
- `bash`, `jq`

## Development

```bash
cd aggregator && python3 -m pip install -e ".[dev]" && python3 -m pytest -q
cd dashboard && bun install && bun test && bun run build
```

## Install (to `~/.cursor/`)

After building the dashboard:

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

The installer now merges the dashboard hooks into `~/.cursor/hooks.json` automatically and installs `~/.cursor/hooks/collector.sh`. Existing unrelated hooks are preserved.

Run the aggregator (writes `~/.cursor/dashboard/state.json`):

```bash
python3 ~/.cursor/dashboard/aggregate.py
```

Serve the static UI (same folder as `state.json` for same-origin `fetch`):

```bash
chmod +x scripts/dev-server.sh
./scripts/dev-server.sh 7420
```

Open [http://localhost:7420/](http://localhost:7420/).

## Real vs sample data

- `Real` mode reads `~/.cursor/dashboard/state.json`, which is generated from your live Cursor hooks.
- `Sample` mode reads the checked-in `sample-state.json`, which is safe for demos and does not expose your real usage data.
- Use the header toggle in the dashboard to switch between them. The selected source is remembered in your browser with `localStorage`.

## Models section

The dashboard now includes a `Models` card showing the models you use most in Cursor. This is populated from the `model` field on `sessionStart` hook events and aggregated into `lifetime.models_used`.

Optional cron (every 15 minutes):

```text
*/15 * * * * python3 ~/.cursor/dashboard/aggregate.py >> ~/.cursor/dashboard/aggregate.log 2>&1
```

## Privacy & security

- All data stays on your machine under `~/.cursor/dashboard/`.
- No telemetry is sent by this project; the collector only appends local JSON lines.
- Demo mode uses a static sample file and never reads your real `state.json`.

## Hook payloads

Shell/test/build bonuses assume Cursor exposes success (`exit_code`, `success`, or missing). See [specs.md](specs.md) §1 and adjust parsers in [`aggregator/src/aggregator/replay.py`](aggregator/src/aggregator/replay.py) if your Cursor version differs.

## Design

See [specs.md](specs.md) for hook mapping, XP rules, achievements, and UI structure.
