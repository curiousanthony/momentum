import type { DashboardPreferences } from "./preferences";

export type SettingsStatus = {
  kind: "success" | "error";
  message: string;
} | null;

export function renderSettingsPanel(
  preferences: DashboardPreferences,
  status: SettingsStatus,
): string {
  const checked = preferences.openOnCursorStart ? "checked" : "";
  const statusMarkup = status
    ? `<p class="settings-status ${status.kind}">${status.message}</p>`
    : "";

  return `
    <section class="grid">
      <div class="card full settings-card">
        <p class="eyebrow">Settings</p>
        <h3>Launch behavior</h3>
        <p class="muted">Choose whether Momentum should open itself when Cursor starts a new session.</p>
        <label class="settings-toggle">
          <input type="checkbox" id="setting-open-on-cursor-start" ${checked}>
          <span>Open Momentum automatically when Cursor starts</span>
        </label>
        <p class="muted small">First install still opens Momentum once so the dashboard is immediately usable.</p>
        ${statusMarkup}
      </div>
    </section>
  `;
}
