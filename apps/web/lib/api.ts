import type { DashboardSnapshot } from "@limitboard/db-types";

const upstreamBaseUrl =
  process.env.ALPHASCOPE_API_URL ??
  process.env.NEXT_PUBLIC_SERVER_URL ??
  "http://localhost:8000";

function buildDashboardUpstreamUrl() {
  const upstreamUrl = new URL(`${upstreamBaseUrl}/api/dashboard/latest`);
  const bypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;

  if (bypassSecret) {
    upstreamUrl.searchParams.set("x-vercel-protection-bypass", bypassSecret);
  }

  return upstreamUrl;
}

function buildDashboardUpstreamHeaders() {
  const headers = new Headers();
  const bypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;

  if (bypassSecret) {
    headers.set("x-vercel-protection-bypass", bypassSecret);
  }

  return headers;
}

function toDashboardFetchError(detail: unknown) {
  return detail instanceof Error ? detail.message : "Failed to fetch dashboard snapshot";
}

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const response = await fetch("/api/dashboard/latest", {
    cache: "no-store",
    signal: AbortSignal.timeout(12_000),
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
    signal: AbortSignal.timeout(15_000),
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

export function formatDashboardFetchError(error: unknown) {
  return toDashboardFetchError(error);
}
