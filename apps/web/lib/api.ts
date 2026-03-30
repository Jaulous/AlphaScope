import type { DashboardSnapshot } from "@limitboard/db-types";

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const response = await fetch("/api/dashboard/latest", {
    cache: "no-store",
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
