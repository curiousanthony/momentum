export type DashboardPreferences = {
  openOnCursorStart: boolean;
};

export const DASHBOARD_PREFERENCES_STORAGE_KEY = "momentum.preferences";

export function loadStoredPreferences(): DashboardPreferences {
  if (typeof localStorage === "undefined") {
    return { openOnCursorStart: false };
  }

  const stored = localStorage.getItem(DASHBOARD_PREFERENCES_STORAGE_KEY);
  if (!stored) {
    return { openOnCursorStart: false };
  }

  try {
    const parsed = JSON.parse(stored) as Partial<DashboardPreferences>;
    return { openOnCursorStart: Boolean(parsed.openOnCursorStart) };
  } catch {
    return { openOnCursorStart: false };
  }
}

export function saveStoredPreferences(preferences: DashboardPreferences): void {
  if (typeof localStorage === "undefined") {
    return;
  }

  localStorage.setItem(DASHBOARD_PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
}

export async function loadRuntimePreferences(): Promise<DashboardPreferences> {
  const res = await fetch("./api/runtime-config", { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Could not load runtime preferences");
  }

  const payload = (await res.json()) as { open_on_cursor_start?: boolean };
  return { openOnCursorStart: Boolean(payload.open_on_cursor_start) };
}

export async function saveRuntimePreferences(
  preferences: DashboardPreferences,
): Promise<DashboardPreferences> {
  const res = await fetch("./api/runtime-config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ open_on_cursor_start: preferences.openOnCursorStart }),
  });
  if (!res.ok) {
    throw new Error("Could not save runtime preferences");
  }

  const payload = (await res.json()) as { open_on_cursor_start?: boolean };
  return { openOnCursorStart: Boolean(payload.open_on_cursor_start) };
}
