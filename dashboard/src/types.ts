/** Mirrors aggregator state.json (spec §5). */

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
  last_aggregated_at: string | null;
};
