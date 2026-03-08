"use client";

import dynamic from "next/dynamic";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  ChartContainer,
} from "@limitboard/ui";

import { useIndicatorData } from "./IndicatorDataContext";
import type { IndicatorShape } from "./IndicatorShapeUtil";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function formatPrimaryValue(value?: number | null, fallback?: string | null) {
  if (fallback) {
    return fallback;
  }
  if (value === null || value === undefined) {
    return "--";
  }
  if (Math.abs(value) >= 100000000) {
    return `${(value / 100000000).toFixed(2)}B`;
  }
  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(2)}W`;
  }
  return value.toFixed(2);
}

function MetricSparkline({
  history,
}: {
  history: Array<{ date: string; value: number | null }>;
}) {
  const points = history.map((item) => item.value ?? 0);
  return (
    <ChartContainer className="mt-4 h-24 p-0">
      <ReactECharts
        style={{ height: "100%", width: "100%" }}
        option={{
          animation: false,
          grid: { left: 10, right: 10, top: 10, bottom: 10 },
          xAxis: {
            type: "category",
            show: false,
            data: history.map((item) => item.date),
          },
          yAxis: { type: "value", show: false, scale: true },
          series: [
            {
              type: "line",
              data: points,
              smooth: true,
              symbol: "none",
              lineStyle: { color: "#22C55E", width: 2 },
              areaStyle: { color: "rgba(34, 197, 94, 0.08)" },
            },
          ],
          tooltip: { trigger: "axis" },
        }}
      />
    </ChartContainer>
  );
}

function ThemeChart({
  history,
}: {
  history: Array<{ date: string; turnover: number }>;
}) {
  return (
    <ChartContainer className="mt-4 h-28 p-0">
      <ReactECharts
        style={{ height: "100%", width: "100%" }}
        option={{
          animation: false,
          grid: { left: 12, right: 12, top: 12, bottom: 12 },
          xAxis: {
            type: "category",
            show: false,
            data: history.map((item) => item.date),
          },
          yAxis: { type: "value", show: false, scale: true },
          series: [
            {
              type: "line",
              data: history.map((item) => item.turnover),
              smooth: true,
              symbol: "none",
              lineStyle: { color: "#22C55E", width: 2 },
              areaStyle: { color: "rgba(34, 197, 94, 0.08)" },
            },
          ],
          tooltip: { trigger: "axis" },
        }}
      />
    </ChartContainer>
  );
}

export function IndicatorShapeCard({ shape }: { shape: IndicatorShape }) {
  const { indicators, themes, stocks } = useIndicatorData();

  if (shape.props.variant === "stock" && shape.props.seriesKey) {
    const stock = stocks.find((item) => item.symbol === shape.props.seriesKey);
    return (
      <Card className="h-full w-full overflow-hidden bg-[color:var(--card)]/95">
        <CardHeader className="pb-0">
          <CardDescription>Tracked Equity</CardDescription>
          <CardTitle className="text-base text-zinc-100">
            {stock?.name
              ? `${stock.name} · ${stock.symbol}`
              : shape.props.seriesKey}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex h-[calc(100%-84px)] flex-col justify-between">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="font-mono text-[40px] font-semibold leading-none text-zinc-50">
                {stock?.latest_close?.toFixed(2) ?? "--"}
              </div>
              <p className="mt-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
                Last Close
              </p>
            </div>
            <div className="text-right">
              <div
                className={`font-mono text-[28px] font-semibold leading-none ${
                  (stock?.latest_pct_change ?? 0) >= 0
                    ? "text-emerald-400"
                    : "text-red-400"
                }`}
              >
                {stock?.latest_pct_change !== null &&
                stock?.latest_pct_change !== undefined
                  ? `${stock.latest_pct_change.toFixed(2)}%`
                  : "--"}
              </div>
              <p className="mt-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
                Daily Change
              </p>
            </div>
          </div>
          {stock && stock.history.length > 0 ? (
            <ChartContainer className="mt-4 h-40 p-0">
              <ReactECharts
                style={{ height: "100%", width: "100%" }}
                option={{
                  animation: false,
                  grid: { left: 14, right: 14, top: 12, bottom: 16 },
                  xAxis: {
                    type: "category",
                    show: false,
                    data: stock.history.map((item) => item.ts.slice(0, 10)),
                  },
                  yAxis: { type: "value", show: false, scale: true },
                  tooltip: { trigger: "axis" },
                  series: [
                    {
                      type: "candlestick",
                      data: stock.history.map((item) => [
                        item.open,
                        item.close,
                        item.low,
                        item.high,
                      ]),
                      itemStyle: {
                        color: "#22C55E",
                        color0: "#EF4444",
                        borderColor: "#22C55E",
                        borderColor0: "#EF4444",
                      },
                    },
                  ],
                }}
              />
            </ChartContainer>
          ) : null}
        </CardContent>
      </Card>
    );
  }

  if (shape.props.variant === "theme" && shape.props.seriesKey) {
    const theme = themes.find(
      (item) => item.theme_name === shape.props.seriesKey,
    );
    return (
      <Card className="h-full w-full overflow-hidden bg-[color:var(--card)]/95">
        <CardHeader className="pb-0">
          <CardDescription>Active Theme</CardDescription>
          <CardTitle className="text-base text-zinc-100">
            {theme?.theme_name ?? shape.props.seriesKey}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex h-[calc(100%-84px)] flex-col justify-between">
          <div>
            <div className="font-mono text-[40px] font-semibold leading-none text-zinc-50">
              {theme
                ? `${(theme.latest_turnover / 100000000).toFixed(2)}B`
                : "--"}
            </div>
            <p className="mt-2 text-xs uppercase tracking-[0.2em] text-zinc-500">
              Rank #{theme?.rank ?? "--"}
            </p>
          </div>
          {theme && theme.history.length > 0 ? (
            <ThemeChart history={theme.history} />
          ) : null}
        </CardContent>
      </Card>
    );
  }

  const indicator = indicators.find(
    (item) => item.key === shape.props.indicatorKey,
  );
  return (
    <Card className="h-full w-full overflow-hidden bg-[color:var(--card)]/95">
      <CardHeader className="pb-0">
        <CardDescription>Daily Indicator</CardDescription>
        <CardTitle className="text-base text-zinc-100">
          {indicator?.title ?? shape.props.indicatorKey}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex h-[calc(100%-84px)] flex-col justify-between">
        <div>
          <div className="font-mono text-[48px] font-semibold leading-none text-zinc-50">
            {formatPrimaryValue(
              indicator?.value_numeric,
              indicator?.value_text,
            )}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs uppercase tracking-[0.18em] text-zinc-500">
            <span>{indicator?.unit ?? "metric"}</span>
            <span>{indicator?.indicator_date ?? "--"}</span>
          </div>
        </div>
        {indicator?.history && indicator.history.length > 1 ? (
          <MetricSparkline history={indicator.history} />
        ) : null}
      </CardContent>
    </Card>
  );
}
