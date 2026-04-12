import type { DashboardSnapshot } from "@limitboard/db-types";

function toDashboardFetchError(detail: unknown) {
  return detail instanceof Error ? detail.message : "Failed to fetch dashboard snapshot";
}

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const response = await fetch("/api/dashboard/latest", {
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
