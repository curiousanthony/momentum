import type { DashboardPreferences, DashboardRuntimeInfo } from "./preferences";

export type SettingsStatus = {
  kind: "success" | "error";
  message: string;
} | null;

function channelLabel(channel: string): string {
  return channel === "dev-local" ? "Dev-local channel" : "Stable channel";
}

function updateMessage(runtimeInfo: DashboardRuntimeInfo): string {
  switch (runtimeInfo.updateStatus) {
    case "update-available":
      return "Update available";
    case "up-to-date":
      return "Up to date";
    case "updated":
      return "Momentum was updated successfully";
    case "managed-locally":
      return "This install follows your local workspace";
    case "error":
      return "Could not check for updates";
    default:
      return "Update status will appear when the local runtime reports it.";
  }
}

export function renderSettingsPanel(
  preferences: DashboardPreferences,
  runtimeInfo: DashboardRuntimeInfo,
  status: SettingsStatus,
): string {
  const checked = preferences.openOnCursorStart ? "checked" : "";
  const statusMarkup = status
    ? `<p class="settings-status ${status.kind}">${status.message}</p>`
    : "";
  const latestVersionMarkup = runtimeInfo.latestVersion
    ? `${runtimeInfo.latestVersion}${runtimeInfo.latestChannel ? ` (${runtimeInfo.latestChannel})` : ""}`
    : "Checking from local runtime";

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
        <div class="settings-runtime-meta">
          <p><strong>${channelLabel(runtimeInfo.installedChannel)}</strong></p>
          <p class="muted small">Installed version: ${runtimeInfo.installedVersion}</p>
          <p class="muted small">Latest available: ${latestVersionMarkup}</p>
          <p class="muted small">${updateMessage(runtimeInfo)}</p>
        </div>
        ${statusMarkup}
      </div>
    </section>
  `;
}
