import { describe, expect, mock, test } from "bun:test";

import { loadState } from "./api";

describe("loadState", () => {
  test("loads real state from state.json", async () => {
    const fetchMock = mock(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ xp: { level: 1 } }),
      }),
    );
    globalThis.fetch = fetchMock as typeof fetch;

    await loadState("real");

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("./state.json?_="), {
      cache: "no-store",
    });
  });

  test("loads sample state from sample-state.json", async () => {
    const fetchMock = mock(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ xp: { level: 1 } }),
      }),
    );
    globalThis.fetch = fetchMock as typeof fetch;

    await loadState("sample");

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("./sample-state.json?_="), {
      cache: "no-store",
    });
  });
});
