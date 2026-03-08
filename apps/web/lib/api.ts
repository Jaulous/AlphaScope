import type { DashboardSnapshot } from "@limitboard/db-types";

const serverUrl = process.env.NEXT_PUBLIC_SERVER_URL ?? "http://localhost:8000";

export type FetchRunResult = {
  status: string;
  as_of: string;
  indicator_count: number;
  theme_count: number;
  stock_kline_count: number;
  persisted: boolean;
  warnings?: string[];
  raw_market_snapshot_count?: number;
  raw_limit_up_pool_count?: number;
  raw_concept_board_count?: number;
  raw_stock_kline_count?: number;
};

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const response = await fetch(`${serverUrl}/api/dashboard/latest`, {
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

export async function fetchBoardDocument(): Promise<{ snapshot: unknown }> {
  const response = await fetch(`${serverUrl}/api/board/default`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch board document");
  }
  return response.json();
}

export async function saveBoardDocument(snapshot: unknown) {
  const response = await fetch(`${serverUrl}/api/board/default`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ snapshot }),
  });
  if (!response.ok) {
    throw new Error("Failed to save board document");
  }
  return response.json();
}

export async function runFetchJob(adminKey?: string): Promise<FetchRunResult> {
  const response = await fetch(`${serverUrl}/api/fetch/run`, {
    method: "POST",
    headers: adminKey ? { "x-admin-key": adminKey } : undefined,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail =
      payload && typeof payload.detail === "string"
        ? payload.detail
        : "Failed to run fetch job";
    throw new Error(detail);
  }
  return response.json();
}
