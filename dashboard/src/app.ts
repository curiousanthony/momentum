import { loadState } from "./api";
import { loadStoredDataSource, saveDataSource, type DataSource } from "./data-source";
import { renderHomeView, renderLanguageUsage, renderModelUsage, renderXpBreakdown } from "./home";
import {
  loadRuntimeInfo,
  loadRuntimePreferences,
  loadStoredPreferences,
  saveRuntimePreferences,
  saveStoredPreferences,
  type DashboardRuntimeInfo,
  type DashboardPreferences,
} from "./preferences";
import { renderSettingsPanel, type SettingsStatus } from "./settings";
import type { DashboardState } from "./types";
import "./styles/app.css";

const $ = (id: string) => document.getElementById(id);
const fmt = (n: number | undefined | null) => (n ?? 0).toLocaleString();

const LEVEL_TITLES = [
  "",
  "Newcomer",
  "Apprentice",
  "Developer",
  "Engineer",
  "Senior Dev",
  "Tech Lead",
  "Architect",
  "Principal",
  "Staff Eng",
  "Distinguished",
  "Fellow",
  "Grandmaster",
];

function levelTitle(n: number): string {
  return LEVEL_TITLES[Math.min(n, LEVEL_TITLES.length - 1)] || `Level ${n}`;
}

const ACH_ICONS: Record<string, string> = {
  first_edit: "✏️",
  century_lines: "💯",
  file_surgeon: "🔬",
  polyglot: "🌐",
  tab_master: "⚡",
  tab_lord: "👑",
  streak_3: "🔥",
  streak_7: "🗓️",
  streak_30: "🏆",
  night_owl: "🦉",
  early_bird: "🐦",
  marathon: "🏃",
  deep_thought: "🧠",
  loop_starter: "🔄",
  loop_5: "♾️",
  subagent_first: "🤖",
  subagent_10: "🏭",
  subagent_parallel: "⚙️",
  first_shell: "💻",
  test_runner: "🧪",
  build_master: "🏗️",
  mcp_explorer: "🔌",
  tool_addict: "🛠️",
  comeback: "💪",
  zero_errors: "🧹",
  multi_project: "🗂️",
  project_veteran: "🎖️",
};

let prevState: DashboardState | null = null;
let currentSource: DataSource = loadStoredDataSource();
let currentPreferences: DashboardPreferences = loadStoredPreferences();
let currentRuntimeInfo: DashboardRuntimeInfo = {
  installedVersion: "dev",
  installedChannel: "dev-local",
  latestVersion: null,
  latestChannel: null,
  updateStatus: "managed-locally",
};
let settingsStatus: SettingsStatus = null;
const TAB_NAMES = ["overview", "achievements", "projects", "stats", "settings"] as const;
type TabName = (typeof TAB_NAMES)[number];

function showToast(msg: string, type = ""): void {
  const c = $("toast-container");
  if (!c) return;
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  el.setAttribute("role", "status");
  c.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function diffAndNotify(state: DashboardState): void {
  if (!prevState) {
    prevState = state;
    return;
  }
  if (state.xp.level > prevState.xp.level) {
    showToast(
      `Level up! You are now Level ${state.xp.level} — ${levelTitle(state.xp.level)}`,
      "levelup",
    );
  }
  const prevIds = new Set((prevState.achievements?.unlocked ?? []).map((a) => a.id));
  for (const a of state.achievements?.unlocked ?? []) {
    if (!prevIds.has(a.id)) {
      showToast(`Achievement unlocked: ${a.name} (+${fmt(a.xp_awarded)} XP)`, "achievement");
    }
  }
  prevState = state;
}

function switchTab(name: TabName, btn: HTMLElement, focusTarget: "tab" | "panel" = "tab"): void {
  document.querySelectorAll<HTMLElement>(".tab-panel").forEach((panel) => {
    const isActive = panel.id === `tab-${name}`;
    panel.classList.toggle("active", isActive);
    panel.hidden = !isActive;
    panel.setAttribute("tabindex", isActive ? "0" : "-1");
  });

  document.querySelectorAll<HTMLElement>(".tab-btn").forEach((button) => {
    const isActive = button === btn;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
    button.setAttribute("tabindex", isActive ? "0" : "-1");
  });

  if (focusTarget === "panel") {
    $(`tab-${name}`)?.focus();
    return;
  }

  btn.focus();
}

function renderOverview(s: DashboardState): void {
  $("user-email")!.textContent = s.user?.email ?? "—";
  $("tab-overview")!.innerHTML = renderHomeView(s);
  $("xp-breakdown")!.innerHTML = renderXpBreakdown(s);
  $("lang-list")!.innerHTML = renderLanguageUsage(s);
  $("model-list")!.innerHTML = renderModelUsage(s);
}

function renderAchievements(s: DashboardState): void {
  const ach = s.achievements ?? { unlocked: [], in_progress: [], locked: [] };
  $("ach-count")!.textContent = `(${ach.unlocked?.length ?? 0})`;

  $("ach-unlocked")!.innerHTML = (ach.unlocked ?? []).length
    ? (ach.unlocked ?? [])
        .map(
          (a) => `
        <div class="ach-item">
          <span class="ach-icon">${ACH_ICONS[a.id] ?? "🏅"}</span>
          <div class="ach-body">
            <div class="ach-name">${a.name}</div>
            <div class="ach-desc muted small">${a.desc ?? ""}</div>
            <div class="ach-desc muted small">${a.unlocked_at ? `Unlocked ${new Date(a.unlocked_at).toLocaleDateString()}` : ""}</div>
          </div>
          <span class="ach-xp">+${fmt(a.xp_awarded)} XP</span>
        </div>`,
        )
        .join("")
    : '<div class="muted small">No achievements unlocked yet. Start coding!</div>';

  $("ach-progress")!.innerHTML = (ach.in_progress ?? []).length
    ? (ach.in_progress ?? [])
        .map(
          (a) => `
        <div class="ach-item">
          <span class="ach-icon">${ACH_ICONS[a.id] ?? "🔒"}</span>
          <div class="ach-body">
            <div class="ach-name">${a.name}</div>
            <div class="ach-desc muted small">${a.desc}</div>
            <div class="prog-bar-track">
              <div class="prog-bar-fill" style="width:${a.progress_pct ?? 0}%"></div>
            </div>
            <div class="muted small prog-meta">${fmt(a.progress)} / ${fmt(a.target)} (${a.progress_pct ?? 0}%)</div>
          </div>
        </div>`,
        )
        .join("")
    : '<div class="muted small">No achievements in progress.</div>';

  $("ach-locked")!.innerHTML = (ach.locked ?? [])
    .map(
      (a) => `
        <div class="ach-item locked">
          <span class="ach-icon">🔒</span>
          <div>
            <div class="ach-name">${a.name}</div>
            <div class="ach-desc muted small">Keep coding to unlock</div>
          </div>
        </div>`,
    )
    .join("");
}

function renderProjects(s: DashboardState): void {
  const projects = s.projects ?? {};
  const rows = Object.entries(projects)
    .sort((a, b) => b[1].xp - a[1].xp)
    .map(
      ([name, p]) => `
      <tr>
        <td><strong>${name}</strong></td>
        <td><span class="proj-level">Lv ${p.level}</span></td>
        <td>${fmt(p.xp)}</td>
        <td>${fmt(p.sessions)}</td>
        <td>${fmt(p.lines_added)}</td>
        <td>${fmt(p.files_edited)}</td>
        <td class="muted">${p.last_active ?? "—"}</td>
      </tr>`,
    )
    .join("");

  $("proj-tbody")!.innerHTML =
    rows ||
    '<tr><td colspan="7" class="muted pad">No project data yet.</td></tr>';
}

function renderLifetime(s: DashboardState): void {
  const l = s.lifetime as Record<string, number>;
  const TILES = [
    { label: "Sessions Started", value: fmt(l.sessions_started) },
    { label: "Sessions Completed", value: fmt(l.sessions_completed) },
    { label: "Sessions Aborted", value: fmt(l.sessions_aborted) },
    { label: "Prompts Submitted", value: fmt(l.prompts_submitted) },
    { label: "Lines Added", value: fmt(l.lines_added) },
    { label: "Lines Removed", value: fmt(l.lines_removed) },
    { label: "Files Edited", value: fmt(l.files_edited) },
    { label: "Unique Files", value: fmt(l.unique_files) },
    { label: "Tab Completions", value: fmt(l.tab_completions_accepted) },
    { label: "Commands Run", value: fmt(l.commands_run) },
    { label: "Test Runs", value: fmt(l.test_runs) },
    { label: "Build Runs", value: fmt(l.build_runs) },
    { label: "Tool Calls", value: fmt(l.tool_calls_total) },
    { label: "Tool Failures", value: fmt(l.tool_calls_failed) },
    { label: "Agent Loops", value: fmt(l.agent_loops_total) },
    { label: "Subagents Completed", value: fmt(l.subagents_completed) },
    { label: "Compactions", value: fmt(l.compactions_triggered) },
    {
      label: "Avg Session Length",
      value:
        l.sessions_started && l.total_session_duration_ms
          ? `${Math.round(l.total_session_duration_ms / (l.sessions_started * 60000))}m`
          : "—",
    },
  ];

  $("lifetime-grid")!.innerHTML = TILES.map(
    (t) => `
    <div class="stat-tile">
      <div class="stat-value">${t.value}</div>
      <div class="stat-label">${t.label}</div>
    </div>`,
  ).join("");
}

function renderSettings(): void {
  $("tab-settings")!.innerHTML = renderSettingsPanel(
    currentPreferences,
    currentRuntimeInfo,
    settingsStatus,
  );
}

export function renderShell(): string {
  return `
<div id="toast-container" aria-live="polite"></div>
<header class="header">
  <h1>Momentum</h1>
  <div class="header-actions">
    <div class="source-toggle" role="group" aria-label="Dashboard data source">
      <button type="button" class="source-btn" data-source="real">Real</button>
      <button type="button" class="source-btn" data-source="sample">Sample</button>
    </div>
    <span class="user-pill" id="user-email">loading…</span>
    <button type="button" class="refresh-btn" id="btn-refresh">Refresh</button>
  </div>
</header>
<nav class="tabs" role="tablist">
  <button type="button" class="tab-btn active" id="tab-btn-overview" data-tab="overview" role="tab" aria-selected="true" aria-controls="tab-overview" tabindex="0">Home</button>
  <button type="button" class="tab-btn" id="tab-btn-achievements" data-tab="achievements" role="tab" aria-selected="false" aria-controls="tab-achievements" tabindex="-1">Achievements</button>
  <button type="button" class="tab-btn" id="tab-btn-projects" data-tab="projects" role="tab" aria-selected="false" aria-controls="tab-projects" tabindex="-1">Projects</button>
  <button type="button" class="tab-btn" id="tab-btn-stats" data-tab="stats" role="tab" aria-selected="false" aria-controls="tab-stats" tabindex="-1">Lifetime Stats</button>
  <button type="button" class="tab-btn" id="tab-btn-settings" data-tab="settings" role="tab" aria-selected="false" aria-controls="tab-settings" tabindex="-1">Settings</button>
</nav>

<div class="tab-panel active" id="tab-overview" role="tabpanel" aria-labelledby="tab-btn-overview" tabindex="0"></div>

<div class="tab-panel grid" id="tab-achievements" role="tabpanel" aria-labelledby="tab-btn-achievements" tabindex="-1" hidden>
  <div class="card full">
    <h2>Unlocked <span id="ach-count" class="accent2"></span></h2>
    <div class="ach-list" id="ach-unlocked"></div>
  </div>
  <div class="card full">
    <h2>In Progress</h2>
    <div class="ach-list" id="ach-progress"></div>
  </div>
  <div class="card full">
    <h2>Locked</h2>
    <div class="ach-list" id="ach-locked"></div>
  </div>
</div>

<div class="tab-panel grid" id="tab-projects" role="tabpanel" aria-labelledby="tab-btn-projects" tabindex="-1" hidden>
  <div class="card full scroll-x">
    <h2>Per-Project Stats</h2>
    <table class="proj-table">
      <thead><tr>
        <th>Project</th><th>Level</th><th>XP</th><th>Sessions</th><th>Lines Added</th><th>Files Edited</th><th>Last Active</th>
      </tr></thead>
      <tbody id="proj-tbody"></tbody>
    </table>
  </div>
</div>

<div class="tab-panel grid" id="tab-stats" role="tabpanel" aria-labelledby="tab-btn-stats" tabindex="-1" hidden>
  <div class="card full">
    <h2>Lifetime Statistics</h2>
    <div class="stat-grid" id="lifetime-grid"></div>
  </div>
  <div class="card">
    <h2>XP Sources</h2>
    <div class="breakdown-list" id="xp-breakdown"></div>
  </div>
  <div class="card">
    <h2>Languages Edited</h2>
    <div class="lang-list" id="lang-list"></div>
  </div>
  <div class="card">
    <h2>Models</h2>
    <div class="metric-list" id="model-list"></div>
  </div>
</div>

<div class="tab-panel" id="tab-settings" role="tabpanel" aria-labelledby="tab-btn-settings" tabindex="-1" hidden></div>
`;
}

export function mountApp(root: HTMLElement): void {
  root.innerHTML = renderShell();
  document.querySelectorAll<HTMLButtonElement>(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.tab;
      if (name && TAB_NAMES.includes(name as TabName)) {
        switchTab(name as TabName, btn);
      }
    });
  });
  document.body.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const button = target.closest<HTMLButtonElement>(".tab-jump");
    if (!button) return;
    const name = button.dataset.targetTab;
    if (!name || !TAB_NAMES.includes(name as TabName)) return;
    const tabButton = document.querySelector<HTMLElement>(`.tab-btn[data-tab="${name}"]`);
    if (tabButton) switchTab(name as TabName, tabButton, "panel");
  });
  document.querySelectorAll<HTMLButtonElement>(".source-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const source = btn.dataset.source;
      if (source === "real" || source === "sample") {
        currentSource = source;
        saveDataSource(source);
        syncSourceButtons();
        void refresh();
      }
    });
  });
  $("btn-refresh")?.addEventListener("click", () => refresh());
  document.body.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (target.id !== "setting-open-on-cursor-start") return;
    void persistOpenOnCursorStart(target.checked);
  });

  syncSourceButtons();
  renderSettings();
  void hydrateRuntimePreferences();
  void refresh();
  setInterval(() => void refresh(), 30_000);
}

async function refresh(): Promise<void> {
  const state = await loadState(currentSource);
  if (!state) {
    $("user-email")!.textContent =
      currentSource === "real"
        ? "Could not load real state.json"
        : "Could not load sample-state.json";
    return;
  }
  diffAndNotify(state);
  renderOverview(state);
  renderAchievements(state);
  renderProjects(state);
  renderLifetime(state);
  renderSettings();
}

function syncSourceButtons(): void {
  document.querySelectorAll<HTMLButtonElement>(".source-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.source === currentSource);
  });
}

async function hydrateRuntimePreferences(): Promise<void> {
  try {
    currentPreferences = await loadRuntimePreferences();
    currentRuntimeInfo = await loadRuntimeInfo();
    saveStoredPreferences(currentPreferences);
    settingsStatus = null;
  } catch {
    settingsStatus = {
      kind: "error",
      message: "Could not reach the local runtime settings yet. Local fallback is active.",
    };
  }
  renderSettings();
}

async function persistOpenOnCursorStart(enabled: boolean): Promise<void> {
  const previous = currentPreferences;
  currentPreferences = { openOnCursorStart: enabled };
  saveStoredPreferences(currentPreferences);
  settingsStatus = null;
  renderSettings();

  try {
    currentPreferences = await saveRuntimePreferences(currentPreferences);
    saveStoredPreferences(currentPreferences);
    settingsStatus = {
      kind: "success",
      message: "Launch preference saved.",
    };
  } catch {
    currentPreferences = previous;
    saveStoredPreferences(currentPreferences);
    settingsStatus = {
      kind: "error",
      message: "Could not save the launch preference to the local runtime.",
    };
  }

  renderSettings();
}
