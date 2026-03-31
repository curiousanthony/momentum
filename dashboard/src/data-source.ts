export type DataSource = "real" | "sample";

export const DATA_SOURCE_STORAGE_KEY = "momentum.data-source";

export function getDataSourceUrl(source: DataSource): string {
  switch (source) {
    case "real":
      return "./state.json";
    case "sample":
      return "./sample-state.json";
    default: {
      const _exhaustive: never = source;
      return _exhaustive;
    }
  }
}

export function loadStoredDataSource(): DataSource {
  if (typeof localStorage === "undefined") {
    return "real";
  }

  const stored = localStorage.getItem(DATA_SOURCE_STORAGE_KEY);
  return stored === "sample" ? "sample" : "real";
}

export function saveDataSource(source: DataSource): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  localStorage.setItem(DATA_SOURCE_STORAGE_KEY, source);
}
