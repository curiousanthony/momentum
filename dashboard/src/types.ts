/** Mirrors aggregator state.json (spec §5). */

export type InsightSignalStrength = "high" | "medium" | "low";
export type ConsistencyLevel = "strong" | "emerging" | "limited";
export type RecoveryStatus = "recovering" | "steady";
export type ValidationLevel = "strong" | "emerging" | "limited";
export type ProjectMomentumLevel = "broad" | "concentrated" | "limited";
export type GrowthDirectionKey = "steady_growth" | "recovery" | "taking_shape";
export type MomentumKey = "momentum" | "recovery" | "baseline" | "insufficient_signal";
export type FocusKey = "reliability" | "consistency" | "project_follow_through";
export type InsightEvidenceKey =
  | "consistency"
  | "streak"
  | "sessions"
  | "reliability"
  | "projects"
  | "baseline";

export type InsightEvidenceItem = {
  key: InsightEvidenceKey;
  label: string;
  value: string;
  detail: string;
};

export type InsightFocus = {
  key: FocusKey;
  label: string;
  reason: string;
};

export type DashboardInsights = {
  signal_strength: InsightSignalStrength;
  signals: {
    consistency: {
      level: ConsistencyLevel;
      active_days_7d: number;
      current_streak: number;
    };
    recovery: {
      status: RecoveryStatus;
      detected: boolean;
      current_streak: number;
    };
    validation: {
      level: ValidationLevel;
      tests_run: number;
      builds_run: number;
      completed_sessions: number;
    };
    projectMomentum: {
      level: ProjectMomentumLevel;
      active_projects_7d: number;
      tracked_projects: number;
    };
    growthDirection: {
      key: GrowthDirectionKey;
      label: string;
    };
    focus: InsightFocus | null;
  };
  brief: {
    confidence: InsightSignalStrength;
    headline: string;
    summary: string;
    growth_direction: {
      key: GrowthDirectionKey;
      label: string;
    };
    validation: {
      statement: string;
      evidence: InsightEvidenceItem[];
    };
    momentum: {
      key: MomentumKey;
      label: string;
      detail: string;
    };
    focus: InsightFocus | null;
    proof_modules: InsightEvidenceItem[];
  };
};

export type DashboardState = {
  user: { email: string | null; cursor_version: string | null };
  xp: {
    total: number;
    level: number;
    xp_current_level: number;
    xp_next_level: number;
    xp_progress_pct: number;
    breakdown: Record<string, number>;
  };
  streaks: {
    current_daily_streak: number;
    longest_daily_streak: number;
    last_active_date: string | null;
    current_clean_streak: number;
  };
  achievements: {
    unlocked: Array<{
      id: string;
      name: string;
      desc?: string;
      unlocked_at?: string;
      xp_awarded?: number;
    }>;
    in_progress: Array<{
      id: string;
      name: string;
      desc: string;
      progress: number;
      target: number;
      progress_pct: number;
    }>;
    locked: Array<{ id: string; name: string }>;
  };
  lifetime: Record<string, unknown> & {
    models_used?: Record<string, number>;
    languages?: Record<string, number>;
  };
  today: {
    date: string;
    xp_earned: number;
    sessions: number;
    lines_added: number;
    tab_completions: number;
    commands_run: number;
    tool_calls: number;
    active_projects: string[];
  };
  projects: Record<
    string,
    {
      xp: number;
      level: number;
      sessions: number;
      lines_added: number;
      files_edited: number;
      languages: Record<string, number>;
      last_active: string | null;
    }
  >;
  recent_events: Array<Record<string, unknown>>;
  insights: DashboardInsights;
  last_aggregated_at: string | null;
};
