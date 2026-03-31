import { loadState } from "./api";
import { loadStoredDataSource, saveDataSource, type DataSource } from "./data-source";
import { getSortedModelUsage } from "./model-usage";
import type { DashboardState } from "./types";
import "./styles/app.css";

const $ = (id: string) => document.getElementById(id);
const fmt = (n: number | undefined | null) => (n ?? 0).toLocaleString();

const LANG_COLORS = [
  "#7c6af7",
  "#4fc8a0",
  "#f5a623",
  "#e05c5c",
  "#5cb8f5",
  "#b46cf5",
  "#f5c45c",
  "#5cf5a4",
];

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

const BD_LABELS: Record<string, string> = {
  lines_added: "Lines added",
  files_edited: "Files edited",
  tab_accepted: "Tab completions",
  sessions_completed: "Sessions completed",
  daily_logins: "Daily logins",
  streak_bonuses: "Streak bonuses",
  commands_run: "Commands run",
  test_passes: "Tests passed",
  build_successes: "Builds",
  agent_loops: "Agent loops",
  subagents_completed: "Subagents",
  tool_calls: "Tool calls",
  compactions: "Compactions",
  prompts_submitted: "Prompts",
  achievements: "Achievements",
  first_edits_day: "First edit of day",
  languages: "New languages",
};

let prevState: DashboardState | null = null;
let currentSource: DataSource = loadStoredDataSource();

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

function switchTab(name: string, btn: HTMLElement): void {
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
  $(`tab-${name}`)?.classList.add("active");
  btn.classList.add("active");
}

function renderOverview(s: DashboardState): void {
  $("user-email")!.textContent = s.user?.email ?? "—";
  $("level-num")!.textContent = String(s.xp.level);
  $("level-title")!.textContent = levelTitle(s.xp.level);
  $("level-xp-label")!.textContent = `${fmt(s.xp.total)} total XP`;
  $("xp-bar")!.style.width = `${s.xp.xp_progress_pct}%`;
  $("xp-floor")!.textContent = fmt(s.xp.xp_current_level);
  $("xp-ceil")!.textContent = fmt(s.xp.xp_next_level);
  $("xp-pct")!.textContent = `${s.xp.xp_progress_pct}%`;

  $("streak-count")!.textContent = String(s.streaks.current_daily_streak);
  $("streak-best")!.textContent = `Best: ${s.streaks.longest_daily_streak} days`;
  $("streak-last")!.textContent = `Last active: ${s.streaks.last_active_date ?? "—"}`;
  $("streak-clean")!.textContent = String(s.streaks.current_clean_streak);

  $("today-xp")!.textContent = fmt(s.today.xp_earned);
  $("today-sessions")!.textContent = fmt(s.today.sessions);
  $("today-lines")!.textContent = fmt(s.today.lines_added);
  $("today-tabs")!.textContent = fmt(s.today.tab_completions);
  $("today-cmds")!.textContent = fmt(s.today.commands_run);
  $("today-tools")!.textContent = fmt(s.today.tool_calls);

  const bd = s.xp.breakdown ?? {};
  const maxXP = Math.max(...Object.values(bd), 1);
  $("xp-breakdown")!.innerHTML = Object.entries(bd)
    .sort((a, b) => b[1] - a[1])
    .map(
      ([k, v]) => `
      <div class="breakdown-row">
        <span class="breakdown-label">${BD_LABELS[k] ?? k}</span>
        <div class="breakdown-track">
          <div class="breakdown-fill" style="width:${Math.round((v / maxXP) * 100)}%"></div>
        </div>
        <span class="breakdown-val">${fmt(v)}</span>
      </div>`,
    )
    .join("");

  const feed = s.recent_events ?? [];
  $("activity-feed")!.innerHTML = feed.length
    ? feed
        .slice()
        .reverse()
        .map((ev) => {
          const t = String(ev.type ?? "");
          const dotClass =
            t === "achievement_unlocked" ? "achievement" : t === "level_up" ? "levelup" : "";
          let text = t;
          if (t === "achievement_unlocked") text = `Achievement: ${String(ev.id)}`;
          else if (t === "level_up") text = `Reached Level ${String(ev.level)}`;
          else if (t === "xp_earned") text = `+${fmt(ev.amount as number)} XP — ${String(ev.reason)}`;
          else if (t === "streak_extended") text = `Streak extended to ${String(ev.streak)} days`;
          const time = ev.ts ? new Date(String(ev.ts)).toLocaleTimeString() : "";
          return `<div class="feed-item">
          <div class="feed-dot ${dotClass}"></div>
          <span>${text}</span>
          <span class="feed-time">${time}</span>
        </div>`;
        })
        .join("")
    : '<div class="muted small">No recent events yet.</div>';

  const langs = (s.lifetime.languages as Record<string, number>) ?? {};
  const maxL = Math.max(...Object.values(langs), 1);
  $("lang-list")!.innerHTML = Object.entries(langs)
    .sort((a, b) => b[1] - a[1])
    .map(
      ([lang, count], i) => `
      <div class="lang-row">
        <span class="lang-name">.${lang}</span>
        <div class="lang-track">
          <div class="lang-fill" style="width:${Math.round((count / maxL) * 100)}%;background:${LANG_COLORS[i % LANG_COLORS.length]}"></div>
        </div>
        <span class="lang-count">${fmt(count)}</span>
      </div>`,
    )
    .join("");

  const models = getSortedModelUsage(s.lifetime.models_used);
  const maxModelCount = Math.max(...models.map(([, count]) => count), 1);
  $("model-list")!.innerHTML = models.length
    ? models
        .map(
          ([name, count], i) => `
      <div class="metric-row">
        <span class="metric-name">${name}</span>
        <div class="metric-track">
          <div class="metric-fill" style="width:${Math.round((count / maxModelCount) * 100)}%;background:${LANG_COLORS[i % LANG_COLORS.length]}"></div>
        </div>
        <span class="metric-count">${fmt(count)}</span>
      </div>`,
        )
        .join("")
    : '<div class="muted small">No model usage data yet.</div>';
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

function shell(): string {
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
  <button type="button" class="tab-btn active" data-tab="overview" role="tab" aria-selected="true">Overview</button>
  <button type="button" class="tab-btn" data-tab="achievements" role="tab">Achievements</button>
  <button type="button" class="tab-btn" data-tab="projects" role="tab">Projects</button>
  <button type="button" class="tab-btn" data-tab="stats" role="tab">Lifetime Stats</button>
</nav>

<div class="tab-panel active grid" id="tab-overview">
  <div class="card">
    <h2>Level</h2>
    <div class="level-badge">
      <div class="level-number" id="level-num">—</div>
      <div>
        <div class="level-title" id="level-title">—</div>
        <div class="level-label" id="level-xp-label">0 / 0 XP</div>
      </div>
    </div>
    <div class="xp-bar-wrap">
      <div class="xp-bar-track"><div class="xp-bar-fill" id="xp-bar" style="width:0%"></div></div>
      <div class="xp-bar-labels">
        <span id="xp-floor">0</span>
        <span id="xp-pct">0%</span>
        <span id="xp-ceil">0</span>
      </div>
    </div>
  </div>
  <div class="card">
    <h2>Daily Streak</h2>
    <div class="streak-row">
      <div class="streak-count" id="streak-count">—</div>
      <div>
        <div class="streak-label">days active</div>
        <div class="streak-meta" id="streak-best">Best: —</div>
        <div class="streak-meta" id="streak-last">Last active: —</div>
        <div class="streak-meta">Clean streak: <span id="streak-clean">—</span> days</div>
      </div>
    </div>
  </div>
  <div class="card">
    <h2>Today</h2>
    <div class="today-grid">
      <div class="stat-tile"><div class="stat-value" id="today-xp">—</div><div class="stat-label">XP earned</div></div>
      <div class="stat-tile"><div class="stat-value" id="today-sessions">—</div><div class="stat-label">Sessions</div></div>
      <div class="stat-tile"><div class="stat-value" id="today-lines">—</div><div class="stat-label">Lines added</div></div>
      <div class="stat-tile"><div class="stat-value" id="today-tabs">—</div><div class="stat-label">Tab accepts</div></div>
      <div class="stat-tile"><div class="stat-value" id="today-cmds">—</div><div class="stat-label">Commands</div></div>
      <div class="stat-tile"><div class="stat-value" id="today-tools">—</div><div class="stat-label">Tool calls</div></div>
    </div>
  </div>
  <div class="card wide">
    <h2>XP Sources</h2>
    <div class="breakdown-list" id="xp-breakdown"></div>
  </div>
  <div class="card">
    <h2>Recent Activity</h2>
    <div class="feed-list" id="activity-feed"></div>
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

<div class="tab-panel grid" id="tab-achievements">
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

<div class="tab-panel grid" id="tab-projects">
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

<div class="tab-panel grid" id="tab-stats">
  <div class="card full">
    <h2>Lifetime Statistics</h2>
    <div class="stat-grid" id="lifetime-grid"></div>
  </div>
</div>
`;
}

export function mountApp(root: HTMLElement): void {
  root.innerHTML = shell();
  document.querySelectorAll<HTMLButtonElement>(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.tab;
      if (name) switchTab(name, btn);
    });
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

  syncSourceButtons();
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
}

function syncSourceButtons(): void {
  document.querySelectorAll<HTMLButtonElement>(".source-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.source === currentSource);
  });
}
