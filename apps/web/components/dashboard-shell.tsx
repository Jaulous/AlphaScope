"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp, RefreshCw } from "lucide-react";

import type {
  DashboardIndicator,
  DashboardSnapshot,
  Json,
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

import {
  MetricSparkline,
  StockCandlestickChart,
  ThemeTurnoverChart,
} from "./dashboard-charts";
import { fetchDashboardSnapshot } from "../lib/api";

const REFRESH_INTERVAL_MS = 60_000;
const PRIMARY_INDICATOR_ORDER = [
  "up_limit_count",
  "n_shape_limit_up_count",
] as const;
const PRIMARY_INDICATOR_KEYS = new Set<string>(PRIMARY_INDICATOR_ORDER);
const THEME_PANEL_LIMIT = 8;
const TRACKED_STOCK_PANEL_LIMIT = 12;

type IndicatorStock = {
  symbol: string;
  name?: string | null;
  board_count?: number;
  today_board_count?: number;
  prior_limit_date?: string;
  pullback_low_date?: string;
  pullback_pct?: number;
};

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

function formatIndicatorValue(indicator: DashboardIndicator) {
  if (indicator.value_text) {
    return indicator.value_text;
  }
  return formatCompactNumber(indicator.value_numeric);
}

function formatSignedPercent(value?: number | null) {
  if (value === null || value === undefined) {
    return "--";
  }
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
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

function getIndicatorStocks(indicator: DashboardIndicator): IndicatorStock[] {
  const rawData = indicator.raw_data as { stocks?: Json } | undefined;
  if (!rawData || !Array.isArray(rawData.stocks)) {
    return [];
  }
  return rawData.stocks.filter((item): item is IndicatorStock => {
    return Boolean(item && typeof item === "object" && "symbol" in item);
  });
}

function IndicatorStockTable({
  indicatorKey,
  stocks,
}: {
  indicatorKey: string;
  stocks: IndicatorStock[];
}) {
  const showNShapeColumns = indicatorKey === "n_shape_limit_up_count";

  return (
    <div className="overflow-hidden rounded-[22px] border border-white/10 bg-black/25">
      <div
        className={`grid gap-3 border-b border-white/10 px-4 py-3 text-[11px] uppercase tracking-[0.22em] text-zinc-500 ${
          showNShapeColumns
            ? "grid-cols-[0.9fr_1.1fr_1fr_1fr_0.8fr]"
            : "grid-cols-[1fr_1.2fr_0.8fr]"
        }`}
      >
        <span>代码</span>
        <span>名称</span>
        {showNShapeColumns ? (
          <>
            <span>前次涨停</span>
            <span>回撤低点</span>
            <span>回撤幅度</span>
          </>
        ) : (
          <span>连板</span>
        )}
      </div>
      <div className="divide-y divide-white/8">
        {stocks.map((stock) => (
          <div
            key={`${indicatorKey}-${stock.symbol}`}
            className={`grid gap-3 px-4 py-3 text-sm text-zinc-200 ${
              showNShapeColumns
                ? "grid-cols-[0.9fr_1.1fr_1fr_1fr_0.8fr]"
                : "grid-cols-[1fr_1.2fr_0.8fr]"
            }`}
          >
            <div className="font-mono text-zinc-100">{stock.symbol}</div>
            <div>{stock.name ?? "--"}</div>
            {showNShapeColumns ? (
              <>
                <div>{stock.prior_limit_date ?? "--"}</div>
                <div>{stock.pullback_low_date ?? "--"}</div>
                <div>
                  {stock.pullback_pct !== undefined
                    ? `${stock.pullback_pct.toFixed(2)}%`
                    : "--"}
                </div>
              </>
            ) : (
              <div>{stock.today_board_count ?? stock.board_count ?? "--"}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function IndicatorCard({
  indicator,
  prominent = false,
}: {
  indicator: DashboardIndicator;
  prominent?: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const stocks = useMemo(() => getIndicatorStocks(indicator), [indicator]);
  const hasHistory = Boolean(indicator.history && indicator.history.length > 1);

  return (
    <Card
      className={`border-white/10 bg-[rgba(7,11,22,0.92)] shadow-[0_24px_80px_rgba(0,0,0,0.35)] ${
        prominent ? "min-h-[360px]" : ""
      }`}
    >
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardDescription>{indicator.key}</CardDescription>
            <CardTitle
              className={
                prominent
                  ? "mt-2 text-2xl text-white"
                  : "mt-2 text-lg text-white"
              }
            >
              {indicator.title}
            </CardTitle>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-400">
            {indicator.indicator_date}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="flex items-end justify-between gap-4">
          <div>
            <div
              className={`font-mono font-semibold leading-none text-white ${
                prominent
                  ? "text-[56px] sm:text-[68px]"
                  : "text-[36px] sm:text-[42px]"
              }`}
            >
              {formatIndicatorValue(indicator)}
            </div>
            <div className="mt-3 text-[11px] uppercase tracking-[0.22em] text-zinc-500">
              {indicator.unit ?? "metric"}
            </div>
          </div>
          {stocks.length > 0 ? (
            <Button
              variant="default"
              onClick={() => setIsExpanded((value) => !value)}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              查看当日股票 {stocks.length}
            </Button>
          ) : null}
        </div>

        {hasHistory ? (
          <div>
            <div className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">
              Daily Tracking
            </div>
            <MetricSparkline
              history={indicator.history ?? []}
              className={prominent ? "mt-3 h-28" : "mt-3 h-24"}
            />
          </div>
        ) : null}

        {isExpanded ? (
          <IndicatorStockTable indicatorKey={indicator.key} stocks={stocks} />
        ) : null}
      </CardContent>
    </Card>
  );
}

function ThemeCard({ theme }: { theme: ThemeSeries }) {
  return (
    <Card className="border-white/10 bg-[rgba(7,11,22,0.9)] shadow-[0_24px_80px_rgba(0,0,0,0.3)]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardDescription>Theme Turnover</CardDescription>
            <CardTitle className="mt-2 text-xl text-white">
              {theme.theme_name}
            </CardTitle>
          </div>
          <div className="rounded-full border border-sky-400/20 bg-sky-400/10 px-3 py-1 text-xs text-sky-100">
            Rank #{theme.rank}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div className="font-mono text-[38px] font-semibold leading-none text-white">
            {formatCompactNumber(theme.latest_turnover)}
          </div>
          <div className="text-right text-sm text-zinc-400">
            <div>{formatSignedPercent(theme.metadata?.pct_change)}</div>
            <div className="mt-1 text-xs uppercase tracking-[0.2em] text-zinc-500">
              涨跌幅
            </div>
          </div>
        </div>
        {theme.metadata?.leader ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-zinc-300">
            领涨股: {theme.metadata.leader}
          </div>
        ) : null}
        {theme.history.length > 0 ? (
          <ThemeTurnoverChart history={theme.history} />
        ) : null}
      </CardContent>
    </Card>
  );
}

function StockCard({ stock }: { stock: TrackedStockSeries }) {
  const isPositive = (stock.latest_pct_change ?? 0) >= 0;

  return (
    <Card className="border-white/10 bg-[rgba(7,11,22,0.9)] shadow-[0_24px_80px_rgba(0,0,0,0.3)]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardDescription>Tracked Equity</CardDescription>
            <CardTitle className="mt-2 text-xl text-white">
              {stock.name ? `${stock.name} · ${stock.symbol}` : stock.symbol}
            </CardTitle>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-mono text-zinc-300">
            {stock.symbol}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <div className="font-mono text-[34px] font-semibold leading-none text-white">
              {stock.latest_close?.toFixed(2) ?? "--"}
            </div>
            <div className="mt-2 text-[11px] uppercase tracking-[0.22em] text-zinc-500">
              Last Close
            </div>
          </div>
          <div>
            <div
              className={`font-mono text-[28px] font-semibold leading-none ${
                isPositive ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {formatSignedPercent(stock.latest_pct_change)}
            </div>
            <div className="mt-2 text-[11px] uppercase tracking-[0.22em] text-zinc-500">
              Daily Change
            </div>
          </div>
          <div>
            <div className="font-mono text-[28px] font-semibold leading-none text-zinc-100">
              {formatCompactNumber(stock.latest_turnover)}
            </div>
            <div className="mt-2 text-[11px] uppercase tracking-[0.22em] text-zinc-500">
              Turnover
            </div>
          </div>
        </div>
        {stock.history.length > 0 ? (
          <StockCandlestickChart history={stock.history} />
        ) : null}
      </CardContent>
    </Card>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <Card className="border-white/10 bg-black/20 shadow-none">
      <CardContent className="p-5 text-sm text-zinc-400">{label}</CardContent>
    </Card>
  );
}

function LoadingState() {
  return (
    <Card className="border-white/10 bg-black/20 shadow-none">
      <CardContent className="space-y-3 p-5">
        <div className="text-sm font-medium text-zinc-200">
          正在加载最新指标快照
        </div>
        <div className="text-sm text-zinc-400">
          页面会在拿到最新持久化快照后再渲染指标、题材和个股面板。
        </div>
      </CardContent>
    </Card>
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
          : "Failed to load indicators";
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

  const indicators = useMemo(
    () =>
      (snapshot?.indicators ?? []).filter(
        (indicator) => indicator.key !== "active_themes",
      ),
    [snapshot],
  );
  const themes = useMemo(
    () => (snapshot?.active_themes ?? []).slice(0, THEME_PANEL_LIMIT),
    [snapshot],
  );
  const trackedStocks = useMemo(
    () => (snapshot?.tracked_stocks ?? []).slice(0, TRACKED_STOCK_PANEL_LIMIT),
    [snapshot],
  );
  const primaryIndicators = useMemo(() => {
    const order = new Map<string, number>(
      PRIMARY_INDICATOR_ORDER.map((key, index) => [key, index]),
    );
    return indicators
      .filter((indicator) => PRIMARY_INDICATOR_KEYS.has(indicator.key))
      .sort(
        (left, right) =>
          (order.get(left.key) ?? 99) - (order.get(right.key) ?? 99),
      );
  }, [indicators]);
  const secondaryIndicators = useMemo(
    () =>
      indicators.filter(
        (indicator) => !PRIMARY_INDICATOR_KEYS.has(indicator.key),
      ),
    [indicators],
  );
  const warnings = snapshot?.warnings ?? [];
  const latestRun = snapshot?.latest_run ?? null;
  const hasSnapshot = snapshot !== null;
  const showInitialLoading = isLoading && !hasSnapshot;
  const showNoData =
    !isLoading &&
    !error &&
    hasSnapshot &&
    indicators.length === 0 &&
    themes.length === 0 &&
    trackedStocks.length === 0;
  const showMetricSections = hasSnapshot && !showInitialLoading;
  const showUnavailableState = !hasSnapshot && !showInitialLoading && Boolean(error);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(21,48,74,0.22),transparent_38%),linear-gradient(180deg,#07111b_0%,#04070d_100%)] text-foreground">
      <div className="mx-auto flex w-full max-w-[1340px] flex-col gap-6 px-4 pb-12 pt-6 sm:px-6 lg:px-8">
        <section className="overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(135deg,rgba(8,18,30,0.96),rgba(4,9,16,0.92))] shadow-[0_40px_120px_rgba(0,0,0,0.45)]">
          <div className="flex flex-col gap-6 px-6 py-7 lg:flex-row lg:items-end lg:justify-between lg:px-8 lg:py-8">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-emerald-200">
                Daily Quant Surface
              </div>
              <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-[1.02] text-white sm:text-5xl lg:text-6xl">
                AlphaScope
              </h1>
              <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-400 sm:text-base">
                每日从原始行情计算指标、主题和跟踪股票，并在同一页面上保留历史走势。
                指标卡展示当日值与历史追踪，主题与个股面板展示连续序列，方便观察日内
                热点切换与强势股延续性。
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <Card className="border-white/10 bg-white/5 shadow-none">
                <CardHeader className="pb-3">
                  <CardDescription>Indicators</CardDescription>
                  <CardTitle className="text-3xl text-white">
                    {showInitialLoading ? "..." : indicators.length || "--"}
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card className="border-white/10 bg-white/5 shadow-none">
                <CardHeader className="pb-3">
                  <CardDescription>Themes</CardDescription>
                  <CardTitle className="text-3xl text-white">
                    {showInitialLoading
                      ? "..."
                      : snapshot?.active_themes.length || "--"}
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card className="border-white/10 bg-white/5 shadow-none">
                <CardHeader className="pb-3">
                  <CardDescription>Tracked Stocks</CardDescription>
                  <CardTitle className="text-3xl text-white">
                    {showInitialLoading
                      ? "..."
                      : snapshot?.tracked_stocks.length || "--"}
                  </CardTitle>
                </CardHeader>
              </Card>
              <Card className="border-white/10 bg-white/5 shadow-none">
                <CardHeader className="pb-3">
                  <CardDescription>As Of</CardDescription>
                  <CardTitle className="text-xl text-zinc-100">
                    {showInitialLoading ? "Loading..." : snapshot?.as_of ?? "--"}
                  </CardTitle>
                </CardHeader>
              </Card>
            </div>
          </div>
        </section>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">
              Runtime
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              最新计算快照
            </h2>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Card className="border-white/10 bg-white/5 shadow-none">
                <CardContent className="px-4 py-3 text-sm text-zinc-300">
                  最近刷新:{" "}
                  {showInitialLoading
                    ? "Loading..."
                    : formatTimestamp(snapshot?.generated_at)}
                </CardContent>
              </Card>
            {latestRun ? (
              <Card className="border-white/10 bg-white/5 shadow-none">
                <CardContent className="px-4 py-3 text-sm text-zinc-300">
                  最近任务: {latestRun.status} · {latestRun.target_date}
                </CardContent>
              </Card>
            ) : null}
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
        </div>

        {error ? (
          <Card className="border-rose-500/20 bg-rose-500/10 shadow-none">
            <CardContent className="flex items-start gap-3 p-5">
              <AlertTriangle className="mt-0.5 h-5 w-5 text-rose-300" />
              <div>
                <div className="text-sm font-medium text-rose-100">
                  Indicator load failed
                </div>
                <div className="mt-1 text-sm text-rose-200/80">{error}</div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {warnings.length > 0 ? (
          <Card className="border-amber-400/20 bg-amber-400/10 shadow-none">
            <CardContent className="space-y-2 p-5 text-sm text-amber-100">
              {warnings.map((warning) => (
                <div key={warning} className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-200" />
                  <span>{warning}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        ) : null}

        {showInitialLoading ? <LoadingState /> : null}

        {showNoData ? (
          <Card className="border-amber-400/20 bg-amber-400/10 shadow-none">
            <CardContent className="space-y-2 p-5">
              <div className="text-sm font-medium text-amber-100">
                当前没有可展示的最新快照
              </div>
              <div className="text-sm text-amber-100/80">
                后端已返回响应，但最新持久化快照里没有指标、题材或跟踪股票。先检查抓数任务和
                Supabase 中最近一个交易日的数据完整性。
              </div>
            </CardContent>
          </Card>
        ) : null}

        {showUnavailableState ? (
          <Card className="border-white/10 bg-white/5 shadow-none">
            <CardContent className="space-y-2 p-5">
              <div className="text-sm font-medium text-zinc-100">
                当前无法取得最新快照
              </div>
              <div className="text-sm text-zinc-400">
                页面没有收到任何可回退的持久化数据，因此不会继续渲染空指标面板。
                先检查后端 `/api/dashboard/latest`、最近一次抓数任务，以及 Supabase
                中最新交易日是否已有 serving snapshot。
              </div>
            </CardContent>
          </Card>
        ) : null}

        {showMetricSections ? (
        <section className="space-y-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">
              Core Metrics
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              核心日度指标与历史追踪
            </h2>
          </div>
          {showInitialLoading ? null : primaryIndicators.length > 0 ? (
            <div className="grid gap-5 lg:grid-cols-2">
              {primaryIndicators.map((indicator) => (
                <IndicatorCard
                  key={indicator.key}
                  indicator={indicator}
                  prominent
                />
              ))}
            </div>
          ) : (
            <EmptyState label="No primary indicators available for the latest snapshot." />
          )}
        </section>
        ) : null}

        {showMetricSections ? (
        <section className="space-y-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">
              Additional Metrics
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">扩展指标</h2>
          </div>
          {showInitialLoading ? null : secondaryIndicators.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {secondaryIndicators.map((indicator) => (
                <IndicatorCard key={indicator.key} indicator={indicator} />
              ))}
            </div>
          ) : (
            <EmptyState label="No additional indicators available for the latest snapshot." />
          )}
        </section>
        ) : null}

        {showMetricSections ? (
        <section className="space-y-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">
              Active Themes
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              题材热度连续跟踪
            </h2>
          </div>
          {showInitialLoading ? null : themes.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {themes.map((theme) => (
                <ThemeCard key={theme.theme_name} theme={theme} />
              ))}
            </div>
          ) : (
            <EmptyState label="No active theme history is available for the latest snapshot." />
          )}
        </section>
        ) : null}

        {showMetricSections ? (
        <section className="space-y-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">
              Tracked Equities
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              跟踪股票 K 线与强弱变化
            </h2>
          </div>
          {showInitialLoading ? null : trackedStocks.length > 0 ? (
            <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {trackedStocks.map((stock) => (
                <StockCard key={stock.symbol} stock={stock} />
              ))}
            </div>
          ) : (
            <EmptyState label="No tracked stock history is available for the latest snapshot." />
          )}
        </section>
        ) : null}
      </div>
    </main>
  );
}
