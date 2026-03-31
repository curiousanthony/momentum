# Momentum Auto-Update Channel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an automatic update channel so end users always receive the latest published Momentum dashboard/runtime from `main` without manual commands, while preserving an explicit local-development mode that can intentionally diverge from the published build.

**Architecture:** Publish a versioned Momentum runtime bundle from GitHub `main` as GitHub Release assets, including a public `stable.json` manifest and a downloadable archive, then teach the installed local runtime to track that stable channel by downloading and atomically applying newer published bundles. Keep local development separate through a dev-mode install/update channel that never auto-replaces the developer's local checkout with the published stable build.

**Tech Stack:** Python 3.11 runtime/install scripts, Bun/Vite dashboard build, GitHub Actions, GitHub Releases assets, local JSON config/metadata, existing `aggregator.runtime` HTTP API.

---

## Discovery Summary

- `Implemented`: Momentum already ships a local dashboard runtime, first-install browser open, opt-in open-on-start behavior, and a redesigned `Momentum Brief` home. The factual product snapshot and installed features are documented in `docs/product/current-state.md`, `docs/product/implemented-features.md`, and `docs/memory/agent-handoff.md`.
- `Implemented`: The runtime/install surface already exists in `scripts/install.sh`, `collector/collector.sh`, and `aggregator/src/aggregator/runtime.py`, so an updater should extend those paths instead of inventing a separate deployment mechanism.
- `Discussing` / not yet built: there is no published artifact pipeline, no auto-update channel, no installed-version metadata, and no separation between "local dev install" and "stable end-user install". The absence of `.github/workflows/` confirms this needs to be introduced.
- `Recommendation basis`: this work is explicitly user-requested, and it is principle-consistent with the docs because it improves accessibility, credibility, and "what users see" freshness without weakening user sovereignty. Evidence: `docs/memory/agent-handoff.md`, `docs/north-star/mission-and-values.md`, `docs/north-star/product-principles.md`. It is not already named as the next roadmap item in product memory.
- `Open questions to avoid`: do not make end users pull from arbitrary local checkouts; do not remove user sovereignty by forcing a dev workflow onto end users; do not make local development impossible by always replacing local installs with stable `main`.

## File Structure Map

### Create

- `.github/workflows/publish-runtime.yml`
  - Build/test Momentum on pushes to `main`.
  - Package release-ready dashboard/runtime assets.
  - Publish GitHub Release assets for `stable.json` plus the downloadable runtime archive.
- `scripts/package_runtime_release.py`
  - Assemble a deterministic release bundle from built dashboard + runtime files.
  - Emit version metadata (`version.json` / manifest payload).
- `aggregator/src/aggregator/updater.py`
  - Handle `stable.json` manifest fetch, version comparison, release-asset download, integrity checks, extraction, and atomic swap.
- `aggregator/tests/test_updater.py`
  - Focused tests for channel logic, manifest parsing, update decisions, and atomic install behavior.
- `docs/superpowers/plans/2026-03-31-momentum-auto-update-channel.md`
  - This plan artifact.

### Modify

- `scripts/install.sh`
  - Split stable end-user install from explicit local-dev install behavior.
  - Persist installed channel/version metadata.
  - Default normal installs to the published stable channel once available.
- `aggregator/src/aggregator/runtime.py`
  - Expose installed/latest version metadata.
  - Trigger safe update checks/apply flow on startup/open paths.
  - Preserve explicit dev mode without auto-replacing local work.
- `collector/collector.sh`
  - Keep session-start open behavior intact while avoiding update side effects in dev mode.
- `README.md`
  - Document stable install/update model and local-development mode.
- `dashboard/src/preferences.ts`
  - Add client helpers for runtime update metadata if surfaced in Settings.
- `dashboard/src/settings.ts`
  - Show installed channel/version and update status.
- `dashboard/src/settings.test.ts`
  - Cover new Settings status rendering.
- `dashboard/src/app.ts`
  - Wire settings/runtime status if needed.
- `docs/product/current-state.md`
  - Reflect automatic stable updates and dev-mode distinction once shipped.
- `docs/product/implemented-features.md`
  - Add published runtime channel / auto-update feature.
- `docs/memory/agent-handoff.md`
  - Record next likely work after shipping.
- `docs/memory/decision-log.md`
  - Capture channel/source-of-truth decision.

### Verify Existing Files During Implementation

- `aggregator/src/aggregator/runtime.py`
- `scripts/install.sh`
- `collector/collector.sh`
- `dashboard/package.json`
- `dashboard/src/preferences.ts`
- `dashboard/src/settings.ts`
- `dashboard/src/settings.test.ts`

## Implementation Decisions Locked In

- Stable end users should update from a published artifact built from `main`, not from a local checkout.
- Stable end users should update from one explicit public source of truth: GitHub Release assets containing `stable.json` and the referenced runtime archive.
- Local development must remain explicit and opt-in. A developer-installed local build should be allowed to diverge from published stable until they choose otherwise.
- The updater should be atomic: download to temp location, verify metadata, then swap into `~/.cursor/dashboard`.
- The runtime should remain the single local authority for version/update state, so the dashboard can inspect it over localhost.
- End users should never need to run commands to stay current after the initial installation path is in place.
- Update checks must fail open: bounded timeout, backoff/cooldown, and "keep serving the current install" if manifest fetch, download, validation, or extraction fails.

## Channels And Behavior

- `stable`
  - Source of truth: latest GitHub Release assets published from `main`, discovered through public `stable.json`.
  - Audience: end users.
  - Behavior: automatic check/apply on safe runtime start points.
- `dev-local`
  - Source of truth: developer workspace and local install command.
  - Audience: local developer.
  - Behavior: never auto-replace with `stable` unless explicitly switched.

## Task 1: Publish A Stable Runtime Artifact

**Files:**
- Create: `.github/workflows/publish-runtime.yml`
- Create: `scripts/package_runtime_release.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing packaging test or validation helper**

Use a focused Python test or script assertion for the package output shape:

```python
def test_release_bundle_contains_runtime_metadata(tmp_path: Path):
    bundle_dir = build_bundle(tmp_path)
    version = json.loads((bundle_dir / "version.json").read_text())
    assert "commit_sha" in version
    assert "channel" in version
    assert (bundle_dir / "index.html").exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest aggregator/tests/test_updater.py::test_release_bundle_contains_runtime_metadata -v`
Expected: FAIL because packaging helper does not exist yet.

- [ ] **Step 3: Implement the minimal release packager**

Requirements:
- package built dashboard assets plus required runtime/install files
- emit deterministic `version.json`
- emit public `stable.json` metadata that points at the release archive URL and checksum
- avoid bundling developer-only files

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `pytest aggregator/tests/test_updater.py::test_release_bundle_contains_runtime_metadata -v`
Expected: PASS

- [ ] **Step 5: Add the GitHub Actions publish workflow**

Workflow must:
- trigger on pushes to `main`
- run dashboard tests/build
- run relevant Python tests
- build the release bundle
- publish GitHub Release assets for the runtime archive and `stable.json`

- [ ] **Step 6: Validate the workflow config locally**

Run: `python3 scripts/package_runtime_release.py --help`
Expected: exits successfully and documents required inputs.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/publish-runtime.yml scripts/package_runtime_release.py README.md aggregator/tests/test_updater.py
git commit -m "feat: publish stable Momentum runtime artifacts"
```

## Task 2: Add Runtime Updater Core

**Files:**
- Create: `aggregator/src/aggregator/updater.py`
- Create: `aggregator/tests/test_updater.py`
- Modify: `aggregator/src/aggregator/runtime.py`

- [ ] **Step 1: Write the failing updater tests**

Add focused tests for:
- manifest parsing
- semantic/version comparison
- `stable` updates apply when newer
- `dev-local` never auto-applies stable
- atomic swap leaves current install intact on failure

Example:

```python
def test_dev_local_channel_never_auto_updates_from_stable(tmp_path: Path):
    state = RuntimeInstallState(channel="dev-local", version="local-dev", commit_sha="workspace")
    decision = evaluate_update(state, latest_manifest(version="1.2.3"))
    assert decision.should_update is False
```

- [ ] **Step 2: Run the failing tests**

Run: `pytest aggregator/tests/test_updater.py -v`
Expected: FAIL because updater module and helpers do not exist yet.

- [ ] **Step 3: Implement the updater module**

Include:
- `stable.json` manifest fetch
- installed-state load/save
- update decision logic by channel
- download/extract/apply flow
- temp-dir + atomic replace
- timeout/backoff/fail-open safeguards

- [ ] **Step 4: Run focused updater tests**

Run: `pytest aggregator/tests/test_updater.py -v`
Expected: PASS

- [ ] **Step 5: Integrate updater status into runtime**

Add runtime helpers/CLI support to:
- report installed/latest version
- run update checks
- apply update when channel allows

- [ ] **Step 6: Run relevant runtime tests**

Run: `pytest aggregator/tests/test_runtime.py -v`
Expected: PASS for runtime behavior touched by updater integration.

- [ ] **Step 7: Commit**

```bash
git add aggregator/src/aggregator/updater.py aggregator/src/aggregator/runtime.py aggregator/tests/test_updater.py aggregator/tests/test_runtime.py
git commit -m "feat: add Momentum runtime updater core"
```

## Task 3: Separate Stable End-User Install From Local Dev Install

**Files:**
- Modify: `scripts/install.sh`
- Modify: `README.md`
- Modify: `aggregator/src/aggregator/runtime.py`

- [ ] **Step 1: Write a failing installer behavior test or script-level assertion**

Cover:
- default install records `stable`
- explicit local-dev flag records `dev-local`
- local-dev install does not enable stable auto-replacement

Example:

```python
def test_install_defaults_to_stable_channel(tmp_path: Path):
    cfg = run_install_dry_run(tmp_path, args=[])
    assert cfg["channel"] == "stable"
```

- [ ] **Step 2: Run the failing install-focused test**

Run: `pytest aggregator/tests/test_updater.py::test_install_defaults_to_stable_channel -v`
Expected: FAIL until install/channel logic exists.

- [ ] **Step 3: Implement installer channel selection**

Requirements:
- default end-user path: stable artifact-backed install
- explicit developer path: `--dev-local` or similar
- preserve current convenience for local development
- store channel/version metadata in runtime dir

- [ ] **Step 4: Run focused installer tests**

Run: `pytest aggregator/tests/test_updater.py -v`
Expected: PASS with channel coverage.

- [ ] **Step 5: Update README**

Document:
- stable install/update behavior
- dev-local workflow
- how local development intentionally differs from stable

- [ ] **Step 6: Commit**

```bash
git add scripts/install.sh README.md aggregator/src/aggregator/runtime.py aggregator/tests/test_updater.py
git commit -m "feat: split stable installs from local dev mode"
```

## Task 4: Surface Version And Update State In Settings

**Files:**
- Modify: `dashboard/src/preferences.ts`
- Modify: `dashboard/src/settings.ts`
- Modify: `dashboard/src/settings.test.ts`
- Modify: `dashboard/src/app.ts`

- [ ] **Step 1: Write the failing Settings tests**

Cover:
- installed channel/version visible
- update status text visible
- dev-local mode clearly labeled

Example:

```typescript
test("renders stable version and update status", () => {
  const markup = renderSettingsPanel({
    runtime: { channel: "stable", installedVersion: "1.2.3", latestVersion: "1.2.4" },
  });
  expect(markup).toContain("Stable");
  expect(markup).toContain("1.2.3");
  expect(markup).toContain("Update available");
});
```

- [ ] **Step 2: Run the failing dashboard test**

Run: `cd dashboard && bun test src/settings.test.ts`
Expected: FAIL because update metadata is not rendered yet.

- [ ] **Step 3: Implement runtime preference/update status fetch**

Requirements:
- reuse localhost runtime API
- avoid exposing controls that let end users accidentally switch into dev mode
- keep wording factual and calm

- [ ] **Step 4: Run the focused dashboard test**

Run: `cd dashboard && bun test src/settings.test.ts`
Expected: PASS

- [ ] **Step 5: Run the dashboard suite**

Run: `cd dashboard && bun test`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/preferences.ts dashboard/src/settings.ts dashboard/src/settings.test.ts dashboard/src/app.ts
git commit -m "feat: show Momentum update status in settings"
```

## Task 5: Automatic Update Application On Safe Runtime Paths

**Files:**
- Modify: `aggregator/src/aggregator/runtime.py`
- Modify: `collector/collector.sh`
- Test: `aggregator/tests/test_runtime.py`

- [ ] **Step 1: Write the failing runtime update-flow tests**

Cover:
- startup/open path checks for stable updates
- dev-local skips auto-apply
- failed update keeps current runtime serving

- [ ] **Step 2: Run the failing runtime tests**

Run: `pytest aggregator/tests/test_runtime.py -v`
Expected: FAIL until update hooks are wired in.

- [ ] **Step 3: Implement safe update triggers**

Requirements:
- run update check before or during runtime start in a safe way
- avoid repeated noisy checks on every hook event
- preserve current install/open semantics
- keep session-start browser open behavior independent from update success
- use bounded timeouts and backoff so offline users still get a fast startup on the currently installed build

- [ ] **Step 4: Run runtime tests**

Run: `pytest aggregator/tests/test_runtime.py -v`
Expected: PASS

- [ ] **Step 5: Run the broader targeted backend coverage**

Run: `pytest aggregator/tests/test_replay.py aggregator/tests/test_runtime.py aggregator/tests/test_updater.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add aggregator/src/aggregator/runtime.py collector/collector.sh aggregator/tests/test_runtime.py aggregator/tests/test_updater.py
git commit -m "feat: auto-apply stable Momentum updates on runtime start"
```

## Task 6: Final Verification And Product Memory Updates

**Files:**
- Modify: `docs/product/current-state.md`
- Modify: `docs/product/implemented-features.md`
- Modify: `docs/memory/agent-handoff.md`
- Modify: `docs/memory/decision-log.md`

- [ ] **Step 1: Verify the end-user path**

Run:
- `cd dashboard && bun test`
- `cd dashboard && bun run build`
- relevant Python tests from this plan

Expected:
- all targeted tests pass
- publish/install/update behavior matches stable-channel design

- [ ] **Step 2: Verify the local-dev path**

Check:
- a dev-local install remains on local artifacts
- runtime status reports dev-local channel clearly
- stable auto-update does not overwrite the dev-local install

- [ ] **Step 3: Perform a browser sanity check**

Check:
- Settings shows channel/version/update state
- stable install reflects latest published version metadata
- dev-local install is clearly labeled and not auto-overwritten

- [ ] **Step 4: Update product-memory docs**

Record:
- stable artifact-backed auto-update exists
- local-dev channel exists for divergent development
- next likely work after shipping

- [ ] **Step 5: Commit**

```bash
git add docs/product/current-state.md docs/product/implemented-features.md docs/memory/agent-handoff.md docs/memory/decision-log.md README.md
git commit -m "docs: record Momentum auto-update channel"
```

## Verification Checklist

- Stable end-user installs no longer depend on a local workspace checkout.
- Publishing from `main` produces GitHub Release assets for a downloadable, versioned runtime archive plus public `stable.json`.
- Runtime can report installed and latest available versions.
- Stable installs auto-apply newer published versions without manual commands.
- Dev-local installs never auto-replace with stable unless explicitly changed.
- Dashboard Settings shows version/update state clearly.
- Browser verification confirms what users see matches the installed stable artifact.
- Offline or failed update checks still leave the current runtime serving successfully.

## Notes For Implementers

- Prefer GitHub Release assets over pulling raw repo source on user machines.
- Keep update logic conservative and reversible; preserve the existing runtime if download/apply fails.
- Do not make end users choose channels during normal use.
- Do not let local-dev behavior leak into the default stable user path.
