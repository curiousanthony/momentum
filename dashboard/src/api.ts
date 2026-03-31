import type { DashboardState } from "./types";
import { getDataSourceUrl, type DataSource } from "./data-source";

export async function loadState(source: DataSource): Promise<DashboardState | null> {
  try {
    const res = await fetch(`${getDataSourceUrl(source)}?_=${Date.now()}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as DashboardState;
  } catch {
    return null;
  }
}
