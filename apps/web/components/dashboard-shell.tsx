"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CandlestickChart,
  Clock3,
  Database,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import type {
  DashboardIndicator,
  DashboardSnapshot,
  FetchRunSourceStatus,
  FetchRunSummary,
  ThemeSeries,
  TrackedStockSeries,
} from "@limitboard/db-types";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@limitboard/ui";

import { fetchDashboardSnapshot } from "../lib/api";

const REFRESH_INTERVAL_MS = 60_000;

function formatCompactNumber(value?: number | null) {
  if (value === null || value === undefined) {
    return "--";
  }
  if (Math.abs(value) >= 100000000) {
    return `${(value / 100000000).toFixed(2)}B`;
  }
  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(2)}W`;
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(
    value,
  );
}

function formatPercent(value?: number | null) {
  if (value === null || value === undefined) {
    return "--";
  }
  return `${value.toFixed(2)}%`;
}

function formatIndicatorValue(indicator: DashboardIndicator) {
  if (indicator.value_text) {
    return indicator.value_text;
  }
  return formatCompactNumber(indicator.value_numeric);
}

function formatTimestamp(value?: string | null) {
  if (!value) {
    return "--";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatSourceStatusLabel(status?: string) {
  switch (status) {
    case "fetched":
      return "Fetched";
    case "reused_existing_raw":
      return "Reused Raw";
    case "failed_no_raw":
      return "Failed";
    default:
      return status ?? "--";
  }
}

function statusTone(status?: string) {
  switch (status) {
    case "success":
    case "fetched":
      return "text-emerald-300 border-emerald-400/20 bg-emerald-400/10";
    case "success_with_warnings":
    case "preserved_existing_snapshot":
    case "reused_existing_raw":
    case "skipped_non_trading_day":
      return "text-amber-200 border-amber-400/20 bg-amber-400/10";
    case "failed":
    case "failed_no_raw":
      return "text-rose-200 border-rose-400/20 bg-rose-400/10";
    default:
      return "text-zinc-300 border-white/10 bg-white/5";
  }
}

function SourceStatusRow({
  source,
  details,
}: {
  source: string;
  details: FetchRunSourceStatus;
}) {
  return (
    <div className="rounded-[18px] border border-white/8 bg-black/20 px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-zinc-100">{source}</div>
          <div className="mt-1 text-xs text-zinc-500">
            Attempts {details.attempts ?? "--"} · Rows{" "}
            {details.row_count ?? "--"}
          </div>
        </div>
        <div
          className={`rounded-full border px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] ${statusTone(details.status)}`}
        >
          {formatSourceStatusLabel(details.status)}
        </div>
      </div>
      {details.errors && details.errors.length > 0 ? (
        <div className="mt-3 space-y-1 text-xs text-zinc-500">
          {details.errors.slice(0, 2).map((error) => (
            <div key={error}>{error}</div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function IngestionStatusCard({
  latestRun,
}: {
  latestRun?: FetchRunSummary | null;
}) {
  const sourceEntries = Object.entries(latestRun?.source_statuses ?? {});

  return (
    <Card className="border-white/10 bg-[rgba(9,13,24,0.9)] shadow-[0_24px_80px_rgba(0,0,0,0.35)]">
      <CardHeader>
        <CardDescription>Ingestion State</CardDescription>
        <CardTitle className="flex items-center gap-3 text-2xl text-white">
          Latest Fetch Run
          <span
            className={`rounded-full border px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] ${statusTone(
              latestRun?.status,
            )}`}
          >
            {latestRun?.status ?? "--"}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!latestRun ? (
          <div className="rounded-[20px] border border-dashed border-white/10 px-4 py-6 text-sm text-zinc-500">
            No ingestion run has been recorded yet.
          </div>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-[18px] border border-white/8 bg-black/20 px-4 py-3">
                <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">
                  Trigger
                </div>
                <div className="mt-2 text-sm text-zinc-100">
                  {latestRun.trigger}
                </div>
              </div>
              <div className="rounded-[18px] border border-white/8 bg-black/20 px-4 py-3">
                <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">
                  Target Trading Day
                </div>
                <div className="mt-2 text-sm text-zinc-100">
                  {latestRun.target_date}
                </div>
              </div>
              <div className="rounded-[18px] border border-white/8 bg-black/20 px-4 py-3">
                <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">
                  Created At
                </div>
                <div className="mt-2 text-sm text-zinc-100">
                  {formatTimestamp(latestRun.created_at)}
                </div>
              </div>
              <div className="rounded-[18px] border border-white/8 bg-black/20 px-4 py-3">
                <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">
                  Counts
                </div>
                <div className="mt-2 text-sm text-zinc-100">
                  I {latestRun.counts?.indicator_count ?? "--"} · T{" "}
                  {latestRun.counts?.theme_count ?? "--"} · K{" "}
                  {latestRun.counts?.stock_kline_count ?? "--"}
                </div>
              </div>
            </div>

            {latestRun.skipped_reason ? (
              <div className="rounded-[18px] border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
                Skipped reason: {latestRun.skipped_reason}
              </div>
            ) : null}

            <div className="space-y-3">
              <div className="text-[11px] uppercase tracking-[0.2em] text-zinc-500">
                Source Status
              </div>
              {sourceEntries.length === 0 ? (
                <div className="rounded-[18px] border border-dashed border-white/10 px-4 py-5 text-sm text-zinc-500">
                  No source detail available for this run.
                </div>
              ) : (
                sourceEntries.map(([source, details]) => (
                  <SourceStatusRow
                    key={source}
                    source={source}
                    details={details}
                  />
                ))
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function MetricCard({ indicator }: { indicator: DashboardIndicator }) {
  const leaders = Array.isArray(
    (indicator.raw_data as { leaders?: string[] } | undefined)?.leaders,
  )
    ? ((indicator.raw_data as { leaders?: string[] }).leaders ?? []).slice(0, 3)
    : [];

  return (
    <Card className="border-white/10 bg-[rgba(7,11,22,0.88)] shadow-[0_24px_80px_rgba(0,0,0,0.35)]">
      <CardHeader className="pb-3">
        <CardDescription>{indicator.key}</CardDescription>
        <CardTitle className="text-[15px] text-zinc-100">
          {indicator.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between gap-4">
          <div>
            <div className="font-mono text-[36px] font-semibold leading-none text-white sm:text-[44px]">
              {formatIndicatorValue(indicator)}
            </div>
            <div className="mt-3 text-[11px] uppercase tracking-[0.24em] text-zinc-500">
              {indicator.unit ?? "metric"}
            </div>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-400">
            {indicator.indicator_date}
          </div>
        </div>
        {leaders.length > 0 ? (
          <div className="mt-5 flex flex-wrap gap-2">
            {leaders.map((leader) => (
              <span
                key={leader}
                className="rounded-full border border-amber-400/20 bg-amber-400/10 px-2.5 py-1 text-xs text-amber-200"
              >
                {leader}
              </span>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function ThemeRow({ theme }: { theme: ThemeSeries }) {
  const pctChange = theme.metadata?.pct_change ?? null;
  return (
    <div className="grid grid-cols-[56px_1fr_auto] items-center gap-4 rounded-[20px] border border-white/8 bg-black/20 px-4 py-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 font-mono text-sm text-zinc-200">
        #{theme.rank}
      </div>
      <div>
        <div className="text-sm font-medium text-zinc-100">
          {theme.theme_name}
        </div>
        <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
          <span>Leader {theme.metadata?.leader ?? "--"}</span>
          <span>
            Breadth {theme.metadata?.advancers ?? "--"} /{" "}
            {theme.metadata?.decliners ?? "--"}
          </span>
        </div>
      </div>
      <div className="text-right">
        <div className="font-mono text-lg text-white">
          {formatCompactNumber(theme.latest_turnover)}
        </div>
        <div
          className={`mt-1 text-xs ${pctChange !== null && pctChange >= 0 ? "text-emerald-300" : "text-rose-300"}`}
        >
          {formatPercent(pctChange)}
        </div>
      </div>
    </div>
  );
}

function StockRow({ stock }: { stock: TrackedStockSeries }) {
  const positive = (stock.latest_pct_change ?? 0) >= 0;
  return (
    <div className="grid grid-cols-[1.2fr_0.8fr_0.8fr_0.9fr] items-center gap-3 rounded-[18px] border border-white/8 bg-black/20 px-4 py-3 text-sm">
      <div>
        <div className="font-medium text-zinc-100">
          {stock.name ?? stock.symbol}
        </div>
        <div className="mt-1 font-mono text-xs text-zinc-500">
          {stock.symbol}
        </div>
      </div>
      <div className="font-mono text-zinc-100">
        {stock.latest_close?.toFixed(2) ?? "--"}
      </div>
      <div
        className={`font-mono ${positive ? "text-emerald-300" : "text-rose-300"}`}
      >
        {formatPercent(stock.latest_pct_change)}
      </div>
      <div className="text-right font-mono text-zinc-400">
        {formatCompactNumber(stock.latest_turnover)}
      </div>
    </div>
  );
}

export function DashboardShell() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSnapshot = useCallback(async (mode: "initial" | "refresh") => {
    if (mode === "initial") {
      setIsLoading(true);
    } else {
      setIsRefreshing(true);
    }
    setError(null);
    try {
      const nextSnapshot = await fetchDashboardSnapshot();
      setSnapshot(nextSnapshot);
    } catch (loadError) {
      const message =
        loadError instanceof Error
          ? loadError.message
          : "Failed to load dashboard";
      setError(message);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadSnapshot("initial");
    const timer = window.setInterval(() => {
      void loadSnapshot("refresh");
    }, REFRESH_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [loadSnapshot]);

  const metrics = useMemo(
    () =>
      (snapshot?.indicators ?? []).filter(
        (indicator) => indicator.key !== "active_themes",
      ),
    [snapshot],
  );
  const themes = snapshot?.active_themes ?? [];
  const stocks = snapshot?.tracked_stocks ?? [];
  const warnings = snapshot?.warnings ?? [];
  const latestRun = snapshot?.latest_run ?? null;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-6 px-4 pb-10 pt-6 sm:px-6 lg:px-10">
        <section className="overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(135deg,rgba(10,16,30,0.96),rgba(6,10,18,0.92))] shadow-[0_40px_120px_rgba(0,0,0,0.45)]">
          <div className="grid gap-6 px-6 py-7 lg:grid-cols-[1.5fr_1fr] lg:px-8 lg:py-8">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-cyan-200">
                <Activity className="h-3.5 w-3.5" />
                Market Monitor
              </div>
              <h1 className="mt-4 max-w-3xl font-sans text-4xl font-semibold leading-[1.05] text-white sm:text-5xl lg:text-6xl">
                AlphaScope
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-zinc-400 sm:text-base">
                A read-only short-term market dashboard. Every card on this page
                is derived from backend calculations, not drawn by hand and not
                editable in the browser.
              </p>
              <div className="mt-6 flex flex-wrap gap-3 text-xs uppercase tracking-[0.22em] text-zinc-500">
                <span className="rounded-full border border-white/10 px-3 py-2">
                  Source {snapshot?.source ?? "--"}
                </span>
                <span className="rounded-full border border-white/10 px-3 py-2">
                  Storage {snapshot?.storage_mode ?? "--"}
                </span>
                <span className="rounded-full border border-white/10 px-3 py-2">
                  As of {snapshot?.as_of ?? "--"}
                </span>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <Card className="border-white/10 bg-white/5 shadow-none">
                <CardHeader className="pb-3">
                  <CardDescription>Advancers</CardDescription>
                  <CardTitle className="text-3xl text-emerald-300">
                    {snapshot?.market_breadth?.advancers ?? "--"}
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card className="border-white/10 bg-white/5 shadow-none">
                <CardHeader className="pb-3">
                  <CardDescription>Decliners</CardDescription>
                  <CardTitle className="text-3xl text-rose-300">
                    {snapshot?.market_breadth?.decliners ?? "--"}
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card className="border-white/10 bg-white/5 shadow-none">
                <CardHeader className="pb-3">
                  <CardDescription>Last Refresh</CardDescription>
                  <CardTitle className="text-xl text-zinc-100">
                    {formatTimestamp(snapshot?.generated_at)}
                  </CardTitle>
                </CardHeader>
              </Card>
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="space-y-6">
            {error ? (
              <Card className="border-rose-500/20 bg-rose-500/10 shadow-none">
                <CardContent className="flex items-start gap-3 p-5">
                  <AlertTriangle className="mt-0.5 h-5 w-5 text-rose-300" />
                  <div>
                    <div className="text-sm font-medium text-rose-100">
                      Dashboard load failed
                    </div>
                    <div className="mt-1 text-sm text-rose-200/80">{error}</div>
                  </div>
                </CardContent>
              </Card>
            ) : null}

            {warnings.length > 0 ? (
              <Card className="border-amber-400/20 bg-amber-400/10 shadow-none">
                <CardContent className="p-5">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-200" />
                    <div className="space-y-1 text-sm text-amber-100">
                      {warnings.map((warning) => (
                        <div key={warning}>{warning}</div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : null}

            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">
                  Backend Metrics
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-white">
                  Computed Market Indicators
                </h2>
              </div>
              <Button
                variant="accent"
                onClick={() => void loadSnapshot("refresh")}
                disabled={isRefreshing}
              >
                <RefreshCw
                  className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
                />
                {isRefreshing ? "Refreshing" : "Refresh"}
              </Button>
            </div>

            {isLoading ? (
              <Card className="border-white/10 bg-black/20 shadow-none">
                <CardContent className="p-5 text-sm text-zinc-400">
                  Loading market dashboard...
                </CardContent>
              </Card>
            ) : null}

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {metrics.map((indicator) => (
                <MetricCard key={indicator.key} indicator={indicator} />
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <Card className="border-white/10 bg-[rgba(9,13,24,0.9)] shadow-[0_24px_80px_rgba(0,0,0,0.35)]">
              <CardHeader>
                <CardDescription>Theme Rotation</CardDescription>
                <CardTitle className="text-2xl text-white">
                  Active Themes
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {themes.length === 0 ? (
                  <div className="rounded-[20px] border border-dashed border-white/10 px-4 py-6 text-sm text-zinc-500">
                    No theme data available yet.
                  </div>
                ) : (
                  themes
                    .slice(0, 8)
                    .map((theme) => (
                      <ThemeRow key={theme.theme_name} theme={theme} />
                    ))
                )}
              </CardContent>
            </Card>

            <IngestionStatusCard latestRun={latestRun} />

            <Card className="border-white/10 bg-[rgba(9,13,24,0.9)] shadow-[0_24px_80px_rgba(0,0,0,0.35)]">
              <CardHeader>
                <CardDescription>Tracked Universe</CardDescription>
                <CardTitle className="text-2xl text-white">
                  Equity Watchlist
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-[1.2fr_0.8fr_0.8fr_0.9fr] gap-3 px-1 text-[11px] uppercase tracking-[0.24em] text-zinc-500">
                  <span>Name</span>
                  <span>Close</span>
                  <span>Move</span>
                  <span className="text-right">Turnover</span>
                </div>
                {stocks.length === 0 ? (
                  <div className="rounded-[20px] border border-dashed border-white/10 px-4 py-6 text-sm text-zinc-500">
                    No tracked stock data available yet.
                  </div>
                ) : (
                  stocks
                    .slice(0, 12)
                    .map((stock) => (
                      <StockRow key={stock.symbol} stock={stock} />
                    ))
                )}
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <Card className="border-white/10 bg-black/20 shadow-none">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
                <TrendingUp className="h-5 w-5" />
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.24em] text-zinc-500">
                  Read Mode
                </div>
                <div className="mt-1 text-sm text-zinc-200">
                  No editable canvas. Everything is backend-driven.
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-black/20 shadow-none">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-400/10 text-cyan-200">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.24em] text-zinc-500">
                  Source Chain
                </div>
                <div className="mt-1 text-sm text-zinc-200">
                  AkShare ingestion, quant-core computation, dashboard delivery.
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-black/20 shadow-none">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-amber-400/20 bg-amber-400/10 text-amber-200">
                <Clock3 className="h-5 w-5" />
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.24em] text-zinc-500">
                  Display Goal
                </div>
                <div className="mt-1 text-sm text-zinc-200">
                  A presentation surface for market state, not a whiteboard
                  tool.
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
