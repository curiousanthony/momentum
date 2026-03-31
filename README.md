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

Default installs are intended to track the published `stable` channel.

For local development, install explicitly in `dev-local` mode so your local work can diverge from the published build:

```bash
./scripts/install.sh --dev-local
```

The installer now merges the dashboard hooks into `~/.cursor/hooks.json` automatically and installs `~/.cursor/hooks/collector.sh`. Existing unrelated hooks are preserved.

On first install, Momentum now also:

- runs the aggregator once so `~/.cursor/dashboard/state.json` exists immediately when possible
- registers a local dashboard startup entry for the current OS
- starts the local dashboard runtime
- opens the dashboard in your default browser once

Check the runtime status and local URL:

```bash
python3 -m aggregator.runtime status --runtime-dir ~/.cursor/dashboard
```

Manual runtime start is still available for troubleshooting:

```bash
chmod +x scripts/dev-server.sh
./scripts/dev-server.sh 7420
```

The runtime serves the dashboard from the same folder as `state.json`, so the app keeps same-origin access to both live and sample data.

## Stable releases

- Momentum now has a release-packaging helper at `scripts/package_runtime_release.py`.
- Published stable builds are intended to ship as GitHub Release assets:
  - `stable.json` as the public update manifest
  - `momentum-<version>.tar.gz` as the runtime archive
- The planned auto-update path should point installed `stable` environments at those published assets rather than at a local checkout.
- Local development can remain intentionally different through a separate `dev-local` install/update path.

## Real vs sample data

- `Real` mode reads `~/.cursor/dashboard/state.json`, which is generated from your live Cursor hooks.
- `Sample` mode reads the checked-in `sample-state.json`, which is safe for demos and does not expose your real usage data.
- Use the header toggle in the dashboard to switch between them. The selected source is remembered in your browser with `localStorage`.

## Settings

- Momentum now includes a `Settings` tab.
- `Open Momentum automatically when Cursor starts` is off by default after install.
- First install still opens Momentum once automatically so the dashboard is immediately usable.

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
