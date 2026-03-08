export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      indicator_definitions: {
        Row: {
          key: string;
          type: string;
          name: string;
          enabled: boolean;
          config: Json;
          description: string | null;
          created_at: string;
          updated_at: string;
        };
      };
      daily_indicators: {
        Row: {
          id: number;
          key: string;
          indicator_date: string;
          title: string;
          type: string;
          value_numeric: number | null;
          value_text: string | null;
          delta: number | null;
          unit: string | null;
          raw_data: Json;
          created_at: string;
          updated_at: string;
        };
      };
      daily_themes_volume: {
        Row: {
          id: number;
          indicator_date: string;
          theme_name: string;
          turnover: number;
          rank: number;
          metadata: Json;
          created_at: string;
        };
      };
      stock_kline_daily: {
        Row: {
          ts: string;
          symbol: string;
          name: string | null;
          open: number | null;
          high: number | null;
          low: number | null;
          close: number | null;
          volume: number | null;
          turnover: number | null;
          amplitude: number | null;
          pct_change: number | null;
          metadata: Json;
        };
      };
      board_documents: {
        Row: {
          id: string;
          slug: string;
          title: string;
          snapshot: Json;
          created_at: string;
          updated_at: string;
        };
      };
    };
  };
}

export interface DashboardIndicator {
  key: string;
  title: string;
  type: string;
  value_numeric?: number | null;
  value_text?: string | null;
  delta?: number | null;
  unit?: string | null;
  raw_data?: Json;
  history?: Array<{ date: string; value: number | null }>;
  indicator_date: string;
}

export interface ThemeSeries {
  theme_name: string;
  rank: number;
  latest_turnover: number;
  history: Array<{ date: string; turnover: number }>;
  metadata?: {
    pct_change?: number | null;
    leader?: string | null;
    advancers?: number | null;
    decliners?: number | null;
  };
}

export interface StockKlinePoint {
  ts: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  turnover: number | null;
  amplitude: number | null;
  pct_change: number | null;
}

export interface TrackedStockSeries {
  symbol: string;
  name: string | null;
  latest_close: number | null;
  latest_pct_change: number | null;
  latest_turnover: number | null;
  history: StockKlinePoint[];
}

export interface FetchRunSourceStatus {
  status: string;
  attempts?: number;
  row_count?: number;
  errors?: string[];
}

export interface FetchRunSummary {
  id: number;
  trigger: string;
  reference_date: string;
  target_date: string;
  status: string;
  skipped_reason?: string | null;
  source_statuses?: Record<string, FetchRunSourceStatus>;
  warnings?: string[];
  counts?: Record<string, number>;
  created_at: string;
}

export interface DashboardSnapshot {
  as_of: string | null;
  generated_at?: string | null;
  source?: "live" | "stored";
  storage_mode?: "supabase" | "memory";
  warnings?: string[];
  latest_run?: FetchRunSummary | null;
  market_breadth?: {
    advancers: number;
    decliners: number;
    unchanged: number;
  } | null;
  indicators: DashboardIndicator[];
  active_themes: ThemeSeries[];
  tracked_stocks: TrackedStockSeries[];
}
