import { describe, expect, mock, test } from "bun:test";

import {
  DASHBOARD_PREFERENCES_STORAGE_KEY,
  loadRuntimePreferences,
  loadStoredPreferences,
  saveRuntimePreferences,
  saveStoredPreferences,
} from "./preferences";

describe("dashboard preferences", () => {
  test("defaults to disabled auto-open when localStorage is unavailable", () => {
    expect(loadStoredPreferences()).toEqual({ openOnCursorStart: false });
  });

  test("persists the open-on-cursor-start preference locally", () => {
    const storage = new Map<string, string>();
    globalThis.localStorage = {
      getItem(key: string) {
        return storage.get(key) ?? null;
      },
      setItem(key: string, value: string) {
        storage.set(key, value);
      },
      removeItem(key: string) {
        storage.delete(key);
      },
      clear() {
        storage.clear();
      },
      key(index: number) {
        return Array.from(storage.keys())[index] ?? null;
      },
      get length() {
        return storage.size;
      },
    };

    saveStoredPreferences({ openOnCursorStart: true });

    expect(storage.get(DASHBOARD_PREFERENCES_STORAGE_KEY)).toBe('{"openOnCursorStart":true}');
    expect(loadStoredPreferences()).toEqual({ openOnCursorStart: true });
  });

  test("loads runtime preferences from the local runtime api", async () => {
    const fetchMock = mock(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ open_on_cursor_start: true }),
      }),
    );
    globalThis.fetch = fetchMock as typeof fetch;

    const prefs = await loadRuntimePreferences();

    expect(fetchMock).toHaveBeenCalledWith("./api/runtime-config", { cache: "no-store" });
    expect(prefs).toEqual({ openOnCursorStart: true });
  });

  test("saves runtime preferences through the local runtime api", async () => {
    const fetchMock = mock(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ open_on_cursor_start: true }),
      }),
    );
    globalThis.fetch = fetchMock as typeof fetch;

    const prefs = await saveRuntimePreferences({ openOnCursorStart: true });

    expect(fetchMock).toHaveBeenCalledWith("./api/runtime-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ open_on_cursor_start: true }),
    });
    expect(prefs).toEqual({ openOnCursorStart: true });
  });
});
