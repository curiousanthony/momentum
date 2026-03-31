import { describe, expect, test } from "bun:test";

import sampleState from "../public/sample-state.json";
import type { DashboardState } from "./types";

describe("DashboardState contract", () => {
  test("sample state includes the editorial brief insights contract", () => {
    const state = sampleState as DashboardState;

    expect(state.insights.signal_strength).toBe("high");
    expect(state.insights.brief.focus?.key).toBe("reliability");
    expect(state.insights.brief.proof_modules.length).toBeGreaterThan(0);
  });
});
