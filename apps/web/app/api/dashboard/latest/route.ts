import type { DashboardSnapshot } from "@limitboard/db-types";

import {
  buildDashboardUpstreamHeaders,
  buildDashboardUpstreamUrl,
  shapeDashboardSnapshot,
} from "../../../../lib/dashboard-snapshot";

export async function GET() {
  try {
    const response = await fetch(buildDashboardUpstreamUrl(), {
      headers: buildDashboardUpstreamHeaders(),
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
