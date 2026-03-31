import { describe, expect, test } from "bun:test";

import { renderSettingsPanel } from "./settings";

describe("settings panel", () => {
  test("renders the auto-open toggle and checked state", () => {
    const markup = renderSettingsPanel(
      { openOnCursorStart: true },
      {
        installedVersion: "1.2.3",
        installedChannel: "stable",
        latestVersion: "1.2.4",
        latestChannel: "stable",
        updateStatus: "update-available",
      },
      { kind: "success", message: "Saved" },
    );

    expect(markup).toContain("Open Momentum automatically when Cursor starts");
    expect(markup).toContain('type="checkbox"');
    expect(markup).toContain("checked");
    expect(markup).toContain("Stable channel");
    expect(markup).toContain("Installed version");
    expect(markup).toContain("1.2.3");
    expect(markup).toContain("Latest available");
    expect(markup).toContain("1.2.4");
    expect(markup).toContain("Update available");
    expect(markup).toContain("Saved");
  });

  test("renders dev-local mode as intentionally separate from stable", () => {
    const markup = renderSettingsPanel(
      { openOnCursorStart: false },
      {
        installedVersion: "dev",
        installedChannel: "dev-local",
        latestVersion: "1.2.4",
        latestChannel: "stable",
        updateStatus: "managed-locally",
      },
      null,
    );

    expect(markup).not.toContain("checked");
    expect(markup).not.toContain("settings-status success");
    expect(markup).toContain("Dev-local channel");
    expect(markup).toContain("This install follows your local workspace");
  });

  test("renders a successful update state explicitly", () => {
    const markup = renderSettingsPanel(
      { openOnCursorStart: false },
      {
        installedVersion: "1.2.4",
        installedChannel: "stable",
        latestVersion: "1.2.4",
        latestChannel: "stable",
        updateStatus: "updated",
      },
      null,
    );

    expect(markup).toContain("Stable channel");
    expect(markup).toContain("Momentum was updated successfully");
  });
});
