import { describe, expect, test } from "bun:test";

import sampleState from "../public/sample-state.json";
import { renderShell } from "./app";
import { renderHomeView, selectProofModules } from "./home";
import type { DashboardState } from "./types";

describe("dashboard home", () => {
  test("renders the editorial-brief home around the insights payload", () => {
    const markup = renderHomeView(sampleState);

    expect(markup).toContain(sampleState.insights.brief.headline);
    expect(markup).toContain(sampleState.insights.brief.validation.statement);
    expect(markup).toContain("Momentum Brief");
    expect(markup).not.toContain("XP Sources");
    expect(markup).not.toContain("Languages Edited");
    expect(markup).not.toContain("Models");
  });

  test("steps down metadata in low-confidence states", () => {
    const lowConfidenceState: DashboardState = {
      ...sampleState,
      insights: {
        ...sampleState.insights,
        brief: {
          ...sampleState.insights.brief,
          confidence: "low",
        },
      },
    };

    const markup = renderHomeView(lowConfidenceState);

    expect(markup).not.toContain("low confidence");
    expect(markup).toContain(lowConfidenceState.insights.brief.growth_direction.label);
    expect(markup).not.toContain("Recent work at a glance");
    expect(markup).not.toContain("Signals shaping this brief");
  });

  test("shell wires tab semantics for buttons and panels", () => {
    const markup = renderShell();

    expect(markup).toContain('role="tablist"');
    expect(markup).toContain('id="tab-btn-overview"');
    expect(markup).toContain('aria-controls="tab-overview"');
    expect(markup).toContain('role="tabpanel"');
    expect(markup).toContain('aria-labelledby="tab-btn-projects"');
  });

  test("prioritizes proof that matches a reliability-focused brief", () => {
    const reliabilityState: DashboardState = {
      ...sampleState,
      insights: {
        ...sampleState.insights,
        brief: {
          ...sampleState.insights.brief,
          focus: {
            key: "reliability",
            label: "Keep reinforcing repeatable workflows",
            reason: "Successful checks and repeatable workflows are the clearest signal right now.",
          },
          proof_modules: [
            {
              key: "projects",
              label: "Active projects",
              value: "2",
              detail: "Work is spread across two active projects.",
            },
            {
              key: "consistency",
              label: "Recent active days",
              value: "5",
              detail: "Active on 5 of the last 7 days.",
            },
            {
              key: "streak",
              label: "Current streak",
              value: "4",
              detail: "Current active-day streak is 4.",
            },
          ],
          validation: {
            ...sampleState.insights.brief.validation,
            evidence: [
              {
                key: "reliability",
                label: "Successful checks",
                value: "3",
                detail: "2 tests and 1 build completed successfully in the last 7 days.",
              },
            ],
          },
        },
      },
    };

    const modules = selectProofModules(reliabilityState);

    expect(modules).toHaveLength(3);
    expect(modules.some((item) => item.key === "reliability")).toBe(true);
    expect(modules[0]?.key).toBe("reliability");
  });

  test("project context prefers current relevance over lifetime xp dominance", () => {
    const currentProjectState: DashboardState = {
      ...sampleState,
      today: {
        ...sampleState.today,
        active_projects: ["current-ship"],
      },
      projects: {
        "legacy-monolith": {
          xp: 9000,
          level: 15,
          sessions: 120,
          lines_added: 25000,
          files_edited: 600,
          languages: { ts: 300 },
          last_active: "2026-03-10",
        },
        "current-ship": {
          xp: 800,
          level: 4,
          sessions: 9,
          lines_added: 540,
          files_edited: 28,
          languages: { py: 20 },
          last_active: sampleState.today.date,
        },
      },
    };

    const markup = renderHomeView(currentProjectState);

    expect(markup).toContain("current-ship is carrying the most momentum right now");
    expect(markup).not.toContain("legacy-monolith is carrying the most momentum right now");
  });
});
