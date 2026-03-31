import { describe, expect, test } from "bun:test";

import {
  DATA_SOURCE_STORAGE_KEY,
  getDataSourceUrl,
  loadStoredDataSource,
  saveDataSource,
} from "./data-source";

describe("data source helpers", () => {
  test("maps real and sample sources to their JSON files", () => {
    expect(getDataSourceUrl("real")).toBe("./state.json");
    expect(getDataSourceUrl("sample")).toBe("./sample-state.json");
  });

  test("defaults to real when localStorage is unavailable", () => {
    expect(loadStoredDataSource()).toBe("real");
  });

  test("persists and reloads the selected source", () => {
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

    saveDataSource("sample");

    expect(storage.get(DATA_SOURCE_STORAGE_KEY)).toBe("sample");
    expect(loadStoredDataSource()).toBe("sample");
  });
});
