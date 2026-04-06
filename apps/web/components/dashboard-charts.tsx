"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";

import { Button, ChartContainer, cn } from "@limitboard/ui";

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

export function MetricTrendChart({
  history,
  className,
}: {
  history: MetricHistoryPoint[];
  className?: string;
}) {
  const points = useMemo(
    () =>
      history.map((item) => ({
        date: item.date,
        value: item.value,
      })),
    [history],
  );
  const defaultVisiblePoints = Math.min(
    Math.max(12, Math.ceil(points.length * 0.55)),
    Math.max(points.length, 1),
  );
  const [visiblePoints, setVisiblePoints] = useState(defaultVisiblePoints);

  useEffect(() => {
    setVisiblePoints(defaultVisiblePoints);
  }, [defaultVisiblePoints]);

  const zoom = useMemo(() => {
    if (points.length <= visiblePoints) {
      return { start: 0, end: 100 };
    }
    const ratio = (visiblePoints / points.length) * 100;
    return { start: Math.max(0, 100 - ratio), end: 100 };
  }, [points.length, visiblePoints]);

  if (points.length === 0) {
    return (
      <div className="flex h-[210px] items-center justify-center rounded-[22px] border border-white/8 bg-black/20 text-sm text-zinc-500">
        暂无可展示的历史序列
      </div>
    );
  }

  const canZoomIn = visiblePoints > Math.max(6, Math.ceil(points.length * 0.2));
  const canZoomOut = visiblePoints < points.length;

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">
          Daily Tracking
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              setVisiblePoints((current) =>
                Math.max(6, Math.floor(current * 0.72)),
              )
            }
            disabled={!canZoomIn}
          >
            放大
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              setVisiblePoints((current) =>
                Math.min(points.length, Math.ceil(current * 1.35)),
              )
            }
            disabled={!canZoomOut}
          >
            缩小
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setVisiblePoints(defaultVisiblePoints)}
            disabled={visiblePoints === defaultVisiblePoints}
          >
            重置
          </Button>
        </div>
      </div>
      <ChartContainer className="h-[210px] rounded-[22px] border border-white/8 bg-black/20 p-0">
        <ReactECharts
          style={{ height: "100%", width: "100%" }}
          option={{
            animation: false,
            grid: { left: 18, right: 18, top: 18, bottom: 46 },
            tooltip: { trigger: "axis" },
            xAxis: {
              type: "category",
              boundaryGap: false,
              axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
              axisLabel: { color: "#71717a", fontSize: 11 },
              data: points.map((item) => item.date),
            },
            yAxis: {
              type: "value",
              scale: true,
              axisLine: { show: false },
              axisTick: { show: false },
              splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
              axisLabel: { color: "#71717a", fontSize: 11 },
            },
            dataZoom: [
              {
                type: "inside",
                start: zoom.start,
                end: zoom.end,
                zoomOnMouseWheel: true,
                moveOnMouseMove: true,
              },
              {
                type: "slider",
                start: zoom.start,
                end: zoom.end,
                height: 18,
                bottom: 10,
                borderColor: "rgba(255,255,255,0.08)",
                fillerColor: "rgba(34,197,94,0.14)",
                backgroundColor: "rgba(255,255,255,0.04)",
                dataBackground: {
                  lineStyle: { color: "rgba(255,255,255,0.12)" },
                  areaStyle: { color: "rgba(255,255,255,0.04)" },
                },
                textStyle: { color: "#71717a" },
              },
            ],
            series: [
              {
                type: "line",
                data: points.map((item) => item.value),
                smooth: true,
                symbol: "none",
                connectNulls: false,
                lineStyle: { color: "#59d471", width: 2.5 },
                areaStyle: { color: "rgba(89, 212, 113, 0.08)" },
              },
            ],
          }}
        />
      </ChartContainer>
    </div>
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
