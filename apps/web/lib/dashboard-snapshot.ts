import type {
  DashboardIndicator,
  DashboardSnapshot,
  ThemeSeries,
  TrackedStockSeries,
} from "@limitboard/db-types";

const DEFAULT_DASHBOARD_UPSTREAM = "http://127.0.0.1:8000";
const THEME_LIMIT = 8;
const STOCK_LIMIT = 12;

function normalizeUpstreamBaseUrl(value: string) {
  const url = new URL(value);
  if (url.hostname === "localhost") {
    url.hostname = "127.0.0.1";
  }
  url.pathname = "";
  url.search = "";
  url.hash = "";
  return url.toString().replace(/\/$/, "");
}

function toIndicatorList(value: unknown): DashboardIndicator[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(
    (item): item is DashboardIndicator =>
      Boolean(item && typeof item === "object" && "key" in item),
  );
}

function toThemeList(value: unknown): ThemeSeries[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(
    (item): item is ThemeSeries =>
      Boolean(item && typeof item === "object" && "theme_name" in item),
  );
}

function toTrackedStockList(value: unknown): TrackedStockSeries[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(
    (item): item is TrackedStockSeries =>
      Boolean(item && typeof item === "object" && "symbol" in item),
  );
}

export function getDashboardUpstreamBaseUrl() {
  return normalizeUpstreamBaseUrl(
    process.env.ALPHASCOPE_API_URL ??
      process.env.NEXT_PUBLIC_SERVER_URL ??
      DEFAULT_DASHBOARD_UPSTREAM,
  );
}

export function buildDashboardUpstreamUrl() {
  const upstreamUrl = new URL(
    `${getDashboardUpstreamBaseUrl()}/api/dashboard/latest`,
  );
  const bypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;

  if (bypassSecret) {
    upstreamUrl.searchParams.set("x-vercel-protection-bypass", bypassSecret);
  }

  return upstreamUrl;
}

export function buildDashboardUpstreamHeaders() {
  const headers = new Headers();
  const bypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;

  if (bypassSecret) {
    headers.set("x-vercel-protection-bypass", bypassSecret);
  }

  return headers;
}

export function shapeDashboardSnapshot(
  payload: DashboardSnapshot,
): DashboardSnapshot {
  const allIndicators = toIndicatorList(payload.indicators);
  const allThemes = toThemeList(payload.active_themes);
  const allTrackedStocks = toTrackedStockList(payload.tracked_stocks);

  const visibleIndicators = allIndicators.filter(
    (indicator) => indicator.key !== "active_themes",
  );
  const visibleThemes = allThemes.slice(0, THEME_LIMIT);
  const visibleTrackedStocks = allTrackedStocks.slice(0, STOCK_LIMIT);

  return {
    ...payload,
    indicators: visibleIndicators,
    active_themes: visibleThemes,
    tracked_stocks: visibleTrackedStocks,
    indicator_count: visibleIndicators.length,
    active_theme_count: allThemes.length,
    tracked_stock_count: allTrackedStocks.length,
    latest_run: payload.latest_run
      ? {
          id: payload.latest_run.id,
          trigger: payload.latest_run.trigger,
          reference_date: payload.latest_run.reference_date,
          target_date: payload.latest_run.target_date,
          status: payload.latest_run.status,
          created_at: payload.latest_run.created_at,
        }
      : null,
  };
}
