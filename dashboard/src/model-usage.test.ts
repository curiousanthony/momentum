import { describe, expect, test } from "bun:test";

import { getSortedModelUsage } from "./model-usage";

describe("getSortedModelUsage", () => {
  test("sorts model usage by descending count", () => {
    expect(
      getSortedModelUsage({
        "claude-sonnet-4": 5,
        "gpt-4o": 2,
        "gpt-5": 8,
      }),
    ).toEqual([
      ["gpt-5", 8],
      ["claude-sonnet-4", 5],
      ["gpt-4o", 2],
    ]);
  });

  test("returns an empty array when models are missing", () => {
    expect(getSortedModelUsage(undefined)).toEqual([]);
  });
});
