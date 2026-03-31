import { getSortedModelUsage } from "./model-usage";
import type { DashboardState } from "./types";

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

function escapeHtml(value: string | number | null | undefined): string {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function compactDate(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function eventText(event: Record<string, unknown>): string {
  switch (String(event.type ?? "")) {
    case "achievement_unlocked":
      return `Unlocked ${String(event.id ?? "an achievement")}`;
    case "level_up":
      return `Reached Level ${String(event.level ?? "—")}`;
    case "xp_earned":
      return `Earned ${fmt(Number(event.amount ?? 0))} XP from ${String(event.reason ?? "recent work")}`;
    case "streak_extended":
      return `Extended your streak to ${String(event.streak ?? "—")} days`;
    default:
      return String(event.type ?? "Recent activity");
  }
}

function topProjectEntry(state: DashboardState): [string, DashboardState["projects"][string]] | null {
  const activeProjectsToday = new Set(state.today.active_projects ?? []);
  const todayDate = state.today.date;

  const entries = Object.entries(state.projects ?? {}).sort((a, b) => {
    const aActiveToday = activeProjectsToday.has(a[0]) ? 1 : 0;
    const bActiveToday = activeProjectsToday.has(b[0]) ? 1 : 0;
    if (bActiveToday !== aActiveToday) return bActiveToday - aActiveToday;

    const aRecent = a[1].last_active === todayDate ? 2 : a[1].last_active ? 1 : 0;
    const bRecent = b[1].last_active === todayDate ? 2 : b[1].last_active ? 1 : 0;
    if (bRecent !== aRecent) return bRecent - aRecent;

    if (a[1].last_active && b[1].last_active && a[1].last_active !== b[1].last_active) {
      return b[1].last_active.localeCompare(a[1].last_active);
    }

    if (b[1].sessions !== a[1].sessions) return b[1].sessions - a[1].sessions;
    if (b[1].lines_added !== a[1].lines_added) return b[1].lines_added - a[1].lines_added;
    if (b[1].xp !== a[1].xp) return b[1].xp - a[1].xp;
    return a[0].localeCompare(b[0]);
  });
  return entries[0] ?? null;
}

function todaySummary(state: DashboardState): string {
  const parts = [
    `${fmt(state.today.sessions)} sessions`,
    `${fmt(state.today.lines_added)} lines`,
    `${fmt(state.today.tool_calls)} tool calls`,
  ];
  if (state.today.active_projects.length > 0) {
    parts.push(`${fmt(state.today.active_projects.length)} active projects`);
  }
  return parts.join(" • ");
}

function cadenceSummary(state: DashboardState): string {
  const activeDays = state.insights.signals.consistency.active_days_7d;
  const cleanStreak = state.streaks.current_clean_streak;
  return `${activeDays}/7 recent active days • ${state.streaks.current_daily_streak}-day daily streak • ${cleanStreak}-day clean streak`;
}

function projectSummary(state: DashboardState): string {
  const featured = topProjectEntry(state);
  if (!featured) {
    return "Project context will appear here once Momentum sees repeated work across a tracked codebase.";
  }

  const [name, project] = featured;
  const language = Object.entries(project.languages ?? {}).sort((a, b) => b[1] - a[1])[0]?.[0];
  const languageText = language ? `Most edits landed in .${language}.` : "Language mix is still taking shape.";
  return `${name} is carrying the most momentum right now with ${fmt(project.sessions)} sessions and ${fmt(project.lines_added)} lines added. ${languageText}`;
}

function evidenceIdentity(item: DashboardState["insights"]["brief"]["proof_modules"][number]): string {
  return `${item.key}:${item.label}:${item.value}`;
}

function evidencePriority(
  state: DashboardState,
  item: DashboardState["insights"]["brief"]["proof_modules"][number],
): number {
  let score = 0;
  const focus = state.insights.brief.focus;
  const normalizedText = `${focus?.label ?? ""} ${focus?.reason ?? ""}`.toLowerCase();

  if (focus?.key === "reliability" || /repeatable|workflow|successful|checks|build|test/.test(normalizedText)) {
    if (item.key === "reliability") score += 8;
    if (item.key === "sessions") score += 2;
  }

  if (focus?.key === "consistency" || state.insights.brief.momentum.key === "momentum") {
    if (item.key === "consistency") score += 6;
    if (item.key === "streak") score += 5;
    if (item.key === "sessions") score += 2;
  }

  if (state.insights.brief.momentum.key === "recovery") {
    if (item.key === "streak" || item.key === "consistency" || item.key === "sessions") score += 4;
  }

  if (focus?.key === "project_follow_through") {
    if (item.key === "projects") score += 7;
    if (item.key === "reliability") score += 2;
  }

  if (state.insights.brief.growth_direction.key === "taking_shape" && item.key === "baseline") {
    score += 4;
  }

  if (item.key === "baseline") score -= 1;

  return score;
}

export function selectProofModules(state: DashboardState): DashboardState["insights"]["brief"]["proof_modules"] {
  const pool = [...state.insights.brief.proof_modules, ...state.insights.brief.validation.evidence];
  const unique = pool.filter((item, index, items) => {
    const identity = evidenceIdentity(item);
    return items.findIndex((candidate) => evidenceIdentity(candidate) === identity) === index;
  });

  return unique
    .map((item, index) => ({
      item,
      index,
      score: evidencePriority(state, item),
    }))
    .sort((left, right) => {
      if (right.score !== left.score) return right.score - left.score;
      return left.index - right.index;
    })
    .slice(0, 3)
    .map(({ item }) => item);
}

export function renderHomeView(state: DashboardState): string {
  const brief = state.insights.brief;
  const proofModules = selectProofModules(state);
  const events = (state.recent_events ?? []).slice().reverse().slice(0, 3);
  const showConfidenceChip = brief.confidence === "high" || brief.confidence === "medium";
  const isLowConfidence = brief.confidence === "low";
  const recentSummary =
    events.length > 0
      ? events.map((event) => eventText(event)).join(" • ")
      : "Recent activity will show up here once Momentum has notable events to explain.";

  return `
    <section class="home">
      <article class="brief-hero card">
        <div class="brief-hero-top">
          <div>
            <p class="eyebrow">Momentum Brief</p>
            <h2 class="brief-headline">${escapeHtml(brief.headline)}</h2>
          </div>
          <div class="brief-meta">
            <span class="brief-chip">${escapeHtml(brief.growth_direction.label)}</span>
            ${
              showConfidenceChip
                ? `<span class="brief-chip muted-chip">${escapeHtml(brief.confidence)} confidence</span>`
                : ""
            }
          </div>
        </div>
        <p class="brief-summary">${escapeHtml(brief.summary)}</p>
        <div class="brief-callouts">
          <div class="brief-callout">
            <span class="callout-label">Proof</span>
            <p>${escapeHtml(brief.validation.statement)}</p>
          </div>
          <div class="brief-callout">
            <span class="callout-label">Cadence</span>
            <p><strong>${escapeHtml(brief.momentum.label)}.</strong> ${escapeHtml(brief.momentum.detail)}</p>
          </div>
          ${
            brief.focus
              ? `<div class="brief-callout focus-callout">
            <span class="callout-label">Focus</span>
            <p><strong>${escapeHtml(brief.focus.label)}.</strong> ${escapeHtml(brief.focus.reason)}</p>
          </div>`
              : ""
          }
        </div>
      </article>

      <section class="evidence-rail" aria-label="Supporting proof">
        ${proofModules
          .map(
            (item) => `
          <article class="proof-card">
            <span class="proof-label">${escapeHtml(item.label)}</span>
            <strong class="proof-value">${escapeHtml(item.value)}</strong>
            <p class="proof-detail">${escapeHtml(item.detail)}</p>
          </article>`,
          )
          .join("")}
      </section>

      ${
        isLowConfidence
          ? ""
          : `
      <section class="home-support-grid">
        <article class="card support-card">
          <div class="support-heading">
            <div>
              <p class="eyebrow">Today</p>
              <h3>Recent work at a glance</h3>
            </div>
            <span class="support-kicker">+${fmt(state.today.xp_earned)} XP</span>
          </div>
          <p class="support-copy">${escapeHtml(todaySummary(state))}</p>
        </article>

        <article class="card support-card">
          <div class="support-heading">
            <div>
              <p class="eyebrow">Cadence</p>
              <h3>Momentum and recovery context</h3>
            </div>
            <span class="support-kicker">Best ${fmt(state.streaks.longest_daily_streak)}</span>
          </div>
          <p class="support-copy">${escapeHtml(cadenceSummary(state))}</p>
          <p class="support-footnote">Last active ${escapeHtml(compactDate(state.streaks.last_active_date))}</p>
        </article>
      </section>

      <section class="secondary-summary-strip" aria-label="Secondary summaries">
        <article class="secondary-summary">
          <div class="secondary-summary-heading">
            <div>
              <p class="eyebrow">Recent changes</p>
              <h4>Signals shaping this brief</h4>
            </div>
          </div>
          <p class="secondary-summary-copy">${escapeHtml(recentSummary)}</p>
          ${
            events[0]?.ts
              ? `<p class="secondary-summary-footnote">Latest signal ${escapeHtml(compactDate(String(events[0].ts)))}</p>`
              : ""
          }
        </article>

        <article class="secondary-summary">
          <div class="secondary-summary-heading">
            <div>
              <p class="eyebrow">Project context</p>
              <h4>Where your effort is concentrating</h4>
            </div>
          </div>
          <p class="secondary-summary-copy">${escapeHtml(projectSummary(state))}</p>
        </article>
      </section>`
      }

      <section class="deeper-strip card" aria-label="Deeper inspection">
        <div>
          <p class="eyebrow">Inspect more</p>
          <h3>Use the deeper views for records, detail, and longer-term context.</h3>
        </div>
        <div class="deeper-actions">
          <button type="button" class="tab-jump" data-target-tab="achievements">Achievements</button>
          <button type="button" class="tab-jump" data-target-tab="projects">Projects</button>
          <button type="button" class="tab-jump" data-target-tab="stats">Lifetime Stats</button>
          <button type="button" class="tab-jump" data-target-tab="settings">Settings</button>
        </div>
      </section>
    </section>
  `;
}

export function renderXpBreakdown(state: DashboardState): string {
  const breakdown = state.xp.breakdown ?? {};
  const maxXP = Math.max(...Object.values(breakdown), 1);
  const entries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);

  if (!entries.length) {
    return '<div class="muted small">No XP source data yet.</div>';
  }

  return entries
    .map(
      ([key, value]) => `
      <div class="breakdown-row">
        <span class="breakdown-label">${escapeHtml(BD_LABELS[key] ?? key)}</span>
        <div class="breakdown-track">
          <div class="breakdown-fill" style="width:${Math.round((value / maxXP) * 100)}%"></div>
        </div>
        <span class="breakdown-val">${fmt(value)}</span>
      </div>`,
    )
    .join("");
}

export function renderLanguageUsage(state: DashboardState): string {
  const languages = (state.lifetime.languages as Record<string, number>) ?? {};
  const maxCount = Math.max(...Object.values(languages), 1);
  const entries = Object.entries(languages).sort((a, b) => b[1] - a[1]);

  if (!entries.length) {
    return '<div class="muted small">No language usage data yet.</div>';
  }

  return entries
    .map(
      ([language, count], index) => `
      <div class="lang-row">
        <span class="lang-name">.${escapeHtml(language)}</span>
        <div class="lang-track">
          <div class="lang-fill" style="width:${Math.round((count / maxCount) * 100)}%;background:${LANG_COLORS[index % LANG_COLORS.length]}"></div>
        </div>
        <span class="lang-count">${fmt(count)}</span>
      </div>`,
    )
    .join("");
}

export function renderModelUsage(state: DashboardState): string {
  const models = getSortedModelUsage(state.lifetime.models_used);
  const maxCount = Math.max(...models.map(([, count]) => count), 1);

  if (!models.length) {
    return '<div class="muted small">No model usage data yet.</div>';
  }

  return models
    .map(
      ([name, count], index) => `
      <div class="metric-row">
        <span class="metric-name">${escapeHtml(name)}</span>
        <div class="metric-track">
          <div class="metric-fill" style="width:${Math.round((count / maxCount) * 100)}%;background:${LANG_COLORS[index % LANG_COLORS.length]}"></div>
        </div>
        <span class="metric-count">${fmt(count)}</span>
      </div>`,
    )
    .join("");
}
