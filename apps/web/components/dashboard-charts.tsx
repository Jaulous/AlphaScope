"use client";

import dynamic from "next/dynamic";

import { ChartContainer, cn } from "@limitboard/ui";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

type MetricHistoryPoint = {
  date: string;
  value: number | null;
};

type ThemeHistoryPoint = {
  date: string;
  turnover: number;
};

type StockHistoryPoint = {
  ts: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
};

export function MetricSparkline({
  history,
  className,
}: {
  history: MetricHistoryPoint[];
  className?: string;
}) {
  const points = history.map((item) => item.value ?? 0);
  return (
    <ChartContainer className={cn("mt-4 h-24 p-0", className)}>
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
          tooltip: { trigger: "axis" },
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
        }}
      />
    </ChartContainer>
  );
}

export function ThemeTurnoverChart({
  history,
  className,
}: {
  history: ThemeHistoryPoint[];
  className?: string;
}) {
  return (
    <ChartContainer className={cn("mt-4 h-28 p-0", className)}>
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
          tooltip: { trigger: "axis" },
          series: [
            {
              type: "line",
              data: history.map((item) => item.turnover),
              smooth: true,
              symbol: "none",
              lineStyle: { color: "#38BDF8", width: 2 },
              areaStyle: { color: "rgba(56, 189, 248, 0.10)" },
            },
          ],
        }}
      />
    </ChartContainer>
  );
}

export function StockCandlestickChart({
  history,
  className,
}: {
  history: StockHistoryPoint[];
  className?: string;
}) {
  const points = history
    .filter((item) => {
      return (
        item.open !== null &&
        item.close !== null &&
        item.low !== null &&
        item.high !== null
      );
    })
    .map((item) => ({
      ts: item.ts,
      values: [item.open, item.close, item.low, item.high] as [
        number,
        number,
        number,
        number,
      ],
    }));

  if (points.length === 0) {
    return null;
  }

  return (
    <ChartContainer className={cn("mt-4 h-40 p-0", className)}>
      <ReactECharts
        style={{ height: "100%", width: "100%" }}
        option={{
          animation: false,
          grid: { left: 14, right: 14, top: 12, bottom: 16 },
          xAxis: {
            type: "category",
            show: false,
            data: points.map((item) => item.ts.slice(0, 10)),
          },
          yAxis: { type: "value", show: false, scale: true },
          tooltip: { trigger: "axis" },
          series: [
            {
              type: "candlestick",
              data: points.map((item) => item.values),
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
  );
}
