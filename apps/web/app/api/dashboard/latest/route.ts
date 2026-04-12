import type { DashboardSnapshot, DashboardIndicator, ThemeSeries, TrackedStockSeries } from "@limitboard/db-types";

const upstreamBaseUrl =
  process.env.ALPHASCOPE_API_URL ??
  process.env.NEXT_PUBLIC_SERVER_URL ??
  "http://localhost:8000";
const THEME_LIMIT = 8;
const STOCK_LIMIT = 12;

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

function shapeDashboardSnapshot(payload: DashboardSnapshot): DashboardSnapshot {
  const visibleIndicators = toIndicatorList(payload.indicators).filter(
    (indicator) => indicator.key !== "active_themes",
  );
  const visibleThemes = toThemeList(payload.active_themes).slice(0, THEME_LIMIT);
  const visibleTrackedStocks = toTrackedStockList(payload.tracked_stocks).slice(
    0,
    STOCK_LIMIT,
  );

  return {
    ...payload,
    indicators: visibleIndicators,
    active_themes: visibleThemes,
    tracked_stocks: visibleTrackedStocks,
    indicator_count: visibleIndicators.length,
    active_theme_count: toThemeList(payload.active_themes).length,
    tracked_stock_count: toTrackedStockList(payload.tracked_stocks).length,
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

export async function GET() {
  const headers = new Headers();
  const bypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;
  const upstreamUrl = new URL(`${upstreamBaseUrl}/api/dashboard/latest`);

  if (bypassSecret) {
    headers.set("x-vercel-protection-bypass", bypassSecret);
    upstreamUrl.searchParams.set("x-vercel-protection-bypass", bypassSecret);
  }
  try {
    const response = await fetch(upstreamUrl, {
      headers,
      signal: AbortSignal.timeout(15_000),
    });

    const contentType =
      response.headers.get("content-type") ?? "application/json";

    if (!response.ok) {
      const body = await response.text();
      return new Response(body, {
        status: response.status,
        headers: {
          "content-type": contentType,
          "cache-control": "no-store",
        },
      });
    }

    if (!contentType.includes("application/json")) {
      const body = await response.text();
      return new Response(body, {
        status: response.status,
        headers: {
          "content-type": contentType,
          "cache-control": "private, max-age=60, stale-while-revalidate=300",
        },
      });
    }

    const payload = (await response.json()) as DashboardSnapshot;
    const shapedPayload = shapeDashboardSnapshot(payload);

    return Response.json(shapedPayload, {
      status: response.status,
      headers: {
        "cache-control": "private, max-age=60, stale-while-revalidate=300",
      },
    });
  } catch (error) {
    const detail =
      error instanceof Error ? error.message : "upstream fetch failed";

    return Response.json(
      { detail: `Failed to reach dashboard backend: ${detail}` },
      { status: 504 },
    );
  }
}
