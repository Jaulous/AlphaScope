"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

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
  MetricTrendChart,
  StockCandlestickChart,
  ThemeTurnoverChart,
} from "./dashboard-charts";
import { fetchDashboardSnapshot } from "../lib/api";

const REFRESH_INTERVAL_MS = 60_000;
const TOP_MONITOR_INDICATOR_ORDER = [
  "up_limit_count",
  "market_turnover",
  "active_capital_ratio",
] as const;
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

function formatCompactSignedNumber(value?: number | null) {
  if (value === null || value === undefined) {
    return "--";
  }
  const formatted = formatCompactNumber(Math.abs(value));
  return `${value >= 0 ? "+" : "-"}${formatted}`;
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

function getIndicatorCategory(indicator: DashboardIndicator) {
  if (indicator.key.includes("turnover")) {
    return "Turnover";
  }
  if (indicator.key.includes("ratio")) {
    return "Ratio";
  }
  if (indicator.key.includes("board")) {
    return "Board";
  }
  if (indicator.key.includes("count")) {
    return "Breadth";
  }
  return "Signal";
}

function getIndicatorTrend(indicator: DashboardIndicator) {
  const values = (indicator.history ?? [])
    .map((item) => item.value)
    .filter((value): value is number => value !== null && value !== undefined);

  if (values.length < 2) {
    return {
      delta: null,
      changePct: null,
      direction: "flat" as const,
      sampleSize: values.length,
    };
  }

  const latest = values[values.length - 1];
  const previous = values[values.length - 2];
  const delta = latest - previous;
  const changePct = previous === 0 ? null : (delta / Math.abs(previous)) * 100;

  return {
    delta,
    changePct,
    direction: delta > 0 ? ("up" as const) : delta < 0 ? ("down" as const) : ("flat" as const),
    sampleSize: values.length,
  };
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

function ServingMetricRow({
  indicator,
}: {
  indicator: DashboardIndicator;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const stocks = useMemo(() => getIndicatorStocks(indicator), [indicator]);
  const trend = useMemo(() => getIndicatorTrend(indicator), [indicator]);
  const isPositive = trend.direction === "up";
  const isNegative = trend.direction === "down";
  const accentClass = isPositive
    ? "text-emerald-300"
    : isNegative
      ? "text-rose-300"
      : "text-zinc-300";
  const panelAccent = isPositive
    ? "border-emerald-400/14 bg-emerald-400/[0.04]"
    : isNegative
      ? "border-rose-400/14 bg-rose-400/[0.04]"
      : "border-white/8 bg-white/[0.02]";

  return (
    <div
      data-serving-metric-row
      className="grid gap-0 xl:grid-cols-[320px_minmax(0,1fr)_170px]"
    >
      <div className="border-b border-white/8 bg-[linear-gradient(180deg,rgba(8,12,22,0.92),rgba(6,10,18,0.88))] p-6 xl:border-b-0 xl:border-r">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-white/8 bg-white/[0.04] px-2.5 py-1 text-[10px] uppercase tracking-[0.22em] text-zinc-400">
                {getIndicatorCategory(indicator)}
              </span>
              <span className="rounded-full border border-white/8 bg-black/20 px-2.5 py-1 text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                {indicator.key}
              </span>
            </div>
            <CardTitle className="mt-4 text-[32px] leading-[1.02] text-white">
              {indicator.title}
            </CardTitle>
            <div className="mt-6 flex items-end gap-3">
              <div className="font-mono text-[52px] font-semibold leading-none text-white">
                {formatIndicatorValue(indicator)}
              </div>
              <div className="pb-1 text-[11px] uppercase tracking-[0.22em] text-zinc-500">
                {indicator.unit ?? "metric"}
              </div>
            </div>

            <div className="mt-6 grid gap-2">
              <div className="flex flex-wrap gap-2 text-xs">
                <span className={`rounded-full border px-3 py-1 ${panelAccent}`}>
                  {isPositive ? (
                    <ArrowUpRight className="mr-1 inline h-3.5 w-3.5" />
                  ) : isNegative ? (
                    <ArrowDownRight className="mr-1 inline h-3.5 w-3.5" />
                  ) : (
                    <Activity className="mr-1 inline h-3.5 w-3.5" />
                  )}
                  <span className={accentClass}>
                    {trend.delta === null
                      ? "History pending"
                      : `${formatCompactSignedNumber(trend.delta)} / ${formatSignedPercent(trend.changePct)}`}
                  </span>
                </span>
                <span className="rounded-full border border-white/8 bg-white/[0.03] px-3 py-1 text-zinc-400">
                  Samples {trend.sampleSize}
                </span>
                <span className="rounded-full border border-white/8 bg-white/[0.03] px-3 py-1 text-zinc-400">
                  Snapshot {indicator.indicator_date}
                </span>
              </div>
            </div>
          </div>
          <div className="rounded-[18px] border border-white/8 bg-white/[0.03] px-3 py-2 text-right">
            <div className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">
              Stored
            </div>
            <div className="mt-1 text-sm text-zinc-300">{indicator.indicator_date}</div>
          </div>
        </div>

        {stocks.length > 0 ? (
          <div className="mt-8">
            <Button
              variant="ghost"
              className="h-10 rounded-[14px] border border-white/8 bg-white/[0.03] px-3 text-zinc-200 hover:border-emerald-400/20 hover:bg-emerald-400/10"
              onClick={() => setIsExpanded((value) => !value)}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              关联股票 {stocks.length}
            </Button>
          </div>
        ) : null}
      </div>

      <div className="border-b border-white/8 bg-[linear-gradient(180deg,rgba(7,11,22,0.94),rgba(4,8,16,0.92))] p-6 xl:border-b-0 xl:border-r">
        <MetricTrendChart
          history={indicator.history ?? []}
          chartClassName="h-[320px] lg:h-[360px]"
        />
      </div>

      <div className="bg-[linear-gradient(180deg,rgba(5,9,16,0.96),rgba(4,8,15,0.92))] p-5">
        <div className="flex h-full flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-zinc-500">
              <BarChart3 className="h-3.5 w-3.5" />
              Market Readout
            </div>
            <div className="mt-4 space-y-3">
              <div className="rounded-[18px] border border-white/8 bg-white/[0.03] p-3">
                <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                  Latest Move
                </div>
                <div className={`mt-2 text-xl font-semibold ${accentClass}`}>
                  {trend.delta === null ? "--" : formatCompactSignedNumber(trend.delta)}
                </div>
              </div>
              <div className="rounded-[18px] border border-white/8 bg-white/[0.03] p-3">
                <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                  Relative Change
                </div>
                <div className={`mt-2 text-xl font-semibold ${accentClass}`}>
                  {formatSignedPercent(trend.changePct)}
                </div>
              </div>
              <div className="rounded-[18px] border border-white/8 bg-white/[0.03] p-3">
                <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                  Tracked Stocks
                </div>
                <div className="mt-2 text-xl font-semibold text-white">
                  {stocks.length}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 rounded-[18px] border border-white/8 bg-black/20 p-3 text-xs leading-5 text-zinc-500">
            {trend.sampleSize > 1
              ? "沿用单指标单行结构。每一行只服务一个指标，图表内部继续支持左右查看历史。"
              : "历史样本不足时，仅保留主读数与基础状态。"}
          </div>
        </div>
      </div>

      {isExpanded ? (
        <div className="border-t border-white/8 bg-[rgba(5,9,16,0.9)] p-6 xl:col-span-3">
          <IndicatorStockTable indicatorKey={indicator.key} stocks={stocks} />
        </div>
      ) : null}
    </div>
  );
}

function MonitorChip({
  indicator,
}: {
  indicator: DashboardIndicator;
}) {
  const trend = getIndicatorTrend(indicator);
  const isPositive = trend.direction === "up";
  const isNegative = trend.direction === "down";

  return (
    <div className="min-w-[160px] rounded-[22px] border border-white/10 bg-[linear-gradient(180deg,rgba(13,19,31,0.95),rgba(9,14,24,0.92))] px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
      <div className="flex items-center justify-between gap-3">
        <div className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">
          {indicator.title}
        </div>
        <div className="rounded-full border border-white/8 bg-white/[0.03] px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-zinc-500">
          {getIndicatorCategory(indicator)}
        </div>
      </div>
      <div className="mt-4 font-mono text-[34px] font-semibold leading-none text-white">
        {formatIndicatorValue(indicator)}
      </div>
      <div className="mt-3 flex items-center justify-between gap-3">
        <div className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">
          {indicator.unit ?? indicator.key}
        </div>
        <div
          className={`text-xs font-medium ${
            isPositive
              ? "text-emerald-300"
              : isNegative
                ? "text-rose-300"
                : "text-zinc-400"
          }`}
        >
          {trend.delta === null ? "--" : formatCompactSignedNumber(trend.delta)}
        </div>
      </div>
    </div>
  );
}

function MetricsList({ indicators }: { indicators: DashboardIndicator[] }) {
  if (indicators.length === 0) {
    return (
      <EmptyState label="No serving-layer indicators are available for the latest snapshot." />
    );
  }

  return (
    <div className="overflow-hidden rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(6,10,18,0.96),rgba(3,6,12,0.96))] shadow-[0_30px_100px_rgba(0,0,0,0.28)]">
      {indicators.map((indicator, index) => (
        <div
          key={indicator.key}
          className={index === 0 ? "" : "border-t border-white/8"}
        >
          <ServingMetricRow indicator={indicator} />
        </div>
      ))}
    </div>
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
          页面正在等待最新持久化快照返回。
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardShell({
  initialSnapshot = null,
  initialError = null,
}: {
  initialSnapshot?: DashboardSnapshot | null;
  initialError?: string | null;
}) {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(initialSnapshot);
  const [isLoading, setIsLoading] = useState(initialSnapshot === null && initialError === null);
  const [error, setError] = useState<string | null>(initialError);
  const isRequestInFlight = useRef(false);

  const loadSnapshot = useCallback(async (mode: "initial" | "refresh") => {
    if (isRequestInFlight.current) {
      return;
    }

    isRequestInFlight.current = true;
    if (mode === "initial") {
      setIsLoading(true);
    }

    try {
      const nextSnapshot = await fetchDashboardSnapshot();
      setSnapshot(nextSnapshot);
      setError(null);
    } catch (loadError) {
      const message =
        loadError instanceof Error
          ? loadError.message
          : "Failed to load indicators";
      setError(message);
    } finally {
      setIsLoading(false);
      isRequestInFlight.current = false;
    }
  }, []);

  useEffect(() => {
    if (!initialSnapshot && !initialError) {
      void loadSnapshot("initial");
    }

    const timer = window.setInterval(() => {
      void loadSnapshot("refresh");
    }, REFRESH_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [initialError, initialSnapshot, loadSnapshot]);

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
  const topMonitorIndicators = useMemo(() => {
    const order = new Map<string, number>(
      TOP_MONITOR_INDICATOR_ORDER.map((key, index) => [key, index]),
    );
    const selected = indicators
      .filter((indicator) => order.has(indicator.key))
      .sort(
        (left, right) =>
          (order.get(left.key) ?? 99) - (order.get(right.key) ?? 99),
      );
    const fallback = indicators.filter(
      (indicator) => !selected.some((picked) => picked.key === indicator.key),
    );
    return [...selected, ...fallback].slice(0, 3);
  }, [indicators]);
  const warnings = snapshot?.warnings ?? [];
  const latestRun = snapshot?.latest_run ?? null;
  const indicatorCount = snapshot?.indicator_count ?? indicators.length;
  const activeThemeCount = snapshot?.active_theme_count ?? snapshot?.active_themes.length ?? 0;
  const trackedStockCount =
    snapshot?.tracked_stock_count ?? snapshot?.tracked_stocks.length ?? 0;
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
          <div className="flex flex-col gap-6 px-6 py-7 lg:flex-row lg:items-start lg:justify-between lg:px-8 lg:py-8">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-emerald-200">
                Daily Quant Surface
              </div>
              <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-[1.02] text-white sm:text-5xl lg:text-6xl">
                AlphaScope
              </h1>
              <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-400 sm:text-base">
                每日从 serving 层输出中直接观察核心监控指标、全量指标明细与题材热度追踪。
                页面顶部只放最关键的监控值，详细指标在下方按单指标单行方式展开，图表内部继续支持左右查看更长历史。
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {showInitialLoading ? (
                <>
                  <div className="min-w-[140px] rounded-[20px] border border-white/10 bg-white/5 px-4 py-4 text-zinc-400">
                    Loading...
                  </div>
                  <div className="min-w-[140px] rounded-[20px] border border-white/10 bg-white/5 px-4 py-4 text-zinc-400">
                    Loading...
                  </div>
                  <div className="min-w-[140px] rounded-[20px] border border-white/10 bg-white/5 px-4 py-4 text-zinc-400">
                    Loading...
                  </div>
                </>
              ) : (
                topMonitorIndicators.map((indicator) => (
                  <MonitorChip key={indicator.key} indicator={indicator} />
                ))
              )}
            </div>
          </div>
        </section>

        <section className="rounded-[28px] border border-sky-400/20 bg-[linear-gradient(135deg,rgba(8,18,30,0.88),rgba(8,18,30,0.7))] px-5 py-5 shadow-[0_24px_80px_rgba(0,0,0,0.24)]">
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
              <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300">
                最近刷新:{" "}
                {showInitialLoading
                  ? "Loading..."
                  : formatTimestamp(snapshot?.generated_at)}
              </div>
              <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300">
                当前快照: {showInitialLoading ? "Loading..." : snapshot?.as_of ?? "--"}
              </div>
              {latestRun ? (
                <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300">
                  最近任务: {latestRun.status} · {latestRun.target_date}
                </div>
              ) : null}
              <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300">
                指标 {showInitialLoading ? "..." : indicatorCount} · 题材{" "}
                {showInitialLoading ? "..." : activeThemeCount} · 个股{" "}
                {showInitialLoading ? "..." : trackedStockCount}
              </div>
            </div>
          </div>
        </section>

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
        <section className="space-y-4 rounded-[30px] border border-emerald-400/14 bg-[linear-gradient(180deg,rgba(7,11,22,0.76),rgba(4,8,15,0.58))] px-5 py-5 shadow-[0_30px_90px_rgba(0,0,0,0.24)]">
          <div className="rounded-[24px] border border-white/10 bg-[linear-gradient(180deg,rgba(9,15,25,0.9),rgba(5,9,16,0.85))] p-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">
                  Serving Metrics
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-white">
                  Serving 层指标明细
                </h2>
                <p className="mt-3 max-w-3xl text-sm text-zinc-400">
                  每个指标保持一行，左侧读数，中部主图，右侧状态面板。
                  真正需要左右拖动的，是图表内部的历史窗口，不是整块指标卡片本身。
                </p>
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                <div className="rounded-full border border-white/8 bg-white/[0.04] px-3 py-1.5 text-zinc-300">
                  Stored Snapshot · {snapshot?.as_of ?? "--"}
                </div>
                <div className="rounded-full border border-white/8 bg-white/[0.04] px-3 py-1.5 text-zinc-300">
                  Indicators · {indicators.length}
                </div>
                <div className="rounded-full border border-white/8 bg-white/[0.04] px-3 py-1.5 text-zinc-300">
                  Layout · One Row Per Indicator
                </div>
              </div>
            </div>
          </div>
          <MetricsList indicators={indicators} />
        </section>
        ) : null}

        {showMetricSections ? (
        <section className="space-y-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-zinc-500">
              Active Themes
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              题材热度追踪模块
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
              跟踪个股模块
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
