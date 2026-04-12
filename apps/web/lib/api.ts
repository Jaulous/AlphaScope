import type { DashboardSnapshot } from "@limitboard/db-types";

import {
  buildDashboardUpstreamHeaders,
  buildDashboardUpstreamUrl,
  shapeDashboardSnapshot,
} from "./dashboard-snapshot";

function toDashboardFetchError(detail: unknown) {
  return detail instanceof Error ? detail.message : "Failed to fetch dashboard snapshot";
}

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const response = await fetch("/api/dashboard/latest", {
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail =
      payload && typeof payload.detail === "string"
        ? payload.detail
        : "Failed to fetch dashboard snapshot";
    throw new Error(detail);
  }
  return response.json();
}

export async function fetchDashboardSnapshotServer(): Promise<DashboardSnapshot> {
  const response = await fetch(buildDashboardUpstreamUrl(), {
    headers: buildDashboardUpstreamHeaders(),
    cache: "no-store",
    signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail =
      payload && typeof payload.detail === "string"
        ? payload.detail
        : "Failed to fetch dashboard snapshot";
    throw new Error(detail);
  }
  const payload = (await response.json()) as DashboardSnapshot;
  return shapeDashboardSnapshot(payload);
}

export function formatDashboardFetchError(error: unknown) {
  return toDashboardFetchError(error);
}
