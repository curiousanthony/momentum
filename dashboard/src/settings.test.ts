import { describe, expect, test } from "bun:test";

import { renderSettingsPanel } from "./settings";

describe("settings panel", () => {
  test("renders the auto-open toggle and checked state", () => {
    const markup = renderSettingsPanel(
      { openOnCursorStart: true },
      { kind: "success", message: "Saved" },
    );

    expect(markup).toContain("Open Momentum automatically when Cursor starts");
    expect(markup).toContain('type="checkbox"');
    expect(markup).toContain("checked");
    expect(markup).toContain("Saved");
  });

  test("renders an idle status without success styling", () => {
    const markup = renderSettingsPanel({ openOnCursorStart: false }, null);

    expect(markup).not.toContain("checked");
    expect(markup).not.toContain("settings-status success");
  });
});
