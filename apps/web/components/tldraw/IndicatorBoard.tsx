"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BarChart3, Play, Plus, RefreshCcw, Save } from "lucide-react";
import {
  Tldraw,
  createTLStore,
  defaultShapeUtils,
  getSnapshot,
  loadSnapshot,
  type Editor,
  type TLStoreSnapshot,
} from "tldraw";
import "tldraw/tldraw.css";

import type {
  DashboardIndicator,
  DashboardSnapshot,
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
  fetchBoardDocument,
  fetchDashboardSnapshot,
  runFetchJob,
  saveBoardDocument,
  type FetchRunResult,
} from "../../lib/api";
import { getSupabaseBrowserClient } from "../../lib/supabase/client";
import { IndicatorDataProvider } from "./IndicatorDataContext";
import { IndicatorShapeUtil } from "./IndicatorShapeUtil";

const store = createTLStore({
  shapeUtils: [...defaultShapeUtils, IndicatorShapeUtil],
});

export function IndicatorBoard() {
  const [editor, setEditor] = useState<Editor | null>(null);
  const [indicators, setIndicators] = useState<DashboardIndicator[]>([]);
  const [themes, setThemes] = useState<ThemeSeries[]>([]);
  const [stocks, setStocks] = useState<TrackedStockSeries[]>([]);
  const [asOf, setAsOf] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [adminKey, setAdminKey] = useState("");
  const [isTriggeringFetch, setIsTriggeringFetch] = useState(false);
  const [fetchFeedback, setFetchFeedback] = useState<string | null>(null);
  const boardLoaded = useRef(false);
  const boardNeedsSeed = useRef(false);
  const lastLoadedSnapshot = useRef<string>("");
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const persistBoardSnapshot = useCallback(async (snapshot: unknown) => {
    const serialized = JSON.stringify(snapshot);
    if (serialized === lastLoadedSnapshot.current) {
      return false;
    }

    setIsSaving(true);
    try {
      await saveBoardDocument(snapshot);
      lastLoadedSnapshot.current = serialized;
      return true;
    } finally {
      setIsSaving(false);
    }
  }, []);

  const reloadDashboard = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const snapshot: DashboardSnapshot = await fetchDashboardSnapshot();
      setIndicators(snapshot.indicators);
      setThemes(snapshot.active_themes);
      setStocks(snapshot.tracked_stocks);
      setAsOf(snapshot.as_of);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load dashboard";
      setLoadError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadBoard = useCallback(async () => {
    const board = await fetchBoardDocument();
    const snapshot = (board.snapshot ?? {}) as unknown as TLStoreSnapshot;
    if (editor && Object.keys(snapshot).length > 0) {
      loadSnapshot(editor.store, snapshot);
      lastLoadedSnapshot.current = JSON.stringify(snapshot);
      boardLoaded.current = true;
      boardNeedsSeed.current = false;
      return;
    }
    boardLoaded.current = true;
    boardNeedsSeed.current = true;
  }, [editor]);

  const seedDefaultBoard = useCallback(async () => {
    if (!editor || indicators.length === 0 || !boardNeedsSeed.current) {
      return;
    }

    const metricCards = indicators
      .filter((item) => item.key !== "active_themes")
      .slice(0, 6);
    const themeCards = themes.slice(0, 4);
    const stockCards = stocks.slice(0, 4);

    const shapes = [
      ...metricCards.map((indicator, index) => ({
        type: "indicator" as const,
        x: index < 3 ? index * 390 : (index - 3) * 390,
        y: index < 3 ? 0 : 300,
        props: {
          indicatorKey: indicator.key,
          variant: "metric" as const,
          w: 360,
          h: 280,
        },
      })),
      ...themeCards.map((theme, index) => ({
        type: "indicator" as const,
        x: index * 450,
        y: 630,
        props: {
          indicatorKey: "active_themes",
          variant: "theme" as const,
          seriesKey: theme.theme_name,
          w: 420,
          h: 320,
        },
      })),
      ...stockCards.map((stock, index) => ({
        type: "indicator" as const,
        x: index * 450,
        y: 980,
        props: {
          indicatorKey: "stock_kline_daily",
          variant: "stock" as const,
          seriesKey: stock.symbol,
          w: 420,
          h: 320,
        },
      })),
    ];

    if (shapes.length === 0) {
      return;
    }

    editor.createShapes(shapes);
    editor.zoomToFit({ animation: { duration: 0 } });
    boardNeedsSeed.current = false;
    await persistBoardSnapshot(getSnapshot(editor.store));
  }, [editor, indicators, persistBoardSnapshot, themes, stocks]);

  useEffect(() => {
    void reloadDashboard();
  }, [reloadDashboard]);

  useEffect(() => {
    if (!editor || boardLoaded.current) {
      return;
    }
    void loadBoard();
  }, [editor, loadBoard]);

  useEffect(() => {
    if (!editor || !boardNeedsSeed.current) {
      return;
    }
    void seedDefaultBoard();
  }, [editor, indicators, themes, seedDefaultBoard]);

  useEffect(() => {
    let supabase;
    try {
      supabase = getSupabaseBrowserClient();
    } catch {
      return;
    }
    const channel = supabase
      .channel("limitboard-stream")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "daily_indicators" },
        () => {
          void reloadDashboard();
        },
      )
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "daily_themes_volume" },
        () => {
          void reloadDashboard();
        },
      )
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "stock_kline_daily" },
        () => {
          void reloadDashboard();
        },
      )
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "board_documents" },
        () => {
          if (editor) {
            void loadBoard();
          }
        },
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [editor, loadBoard, reloadDashboard]);

  useEffect(() => {
    if (!editor) {
      return;
    }
    const unsubscribe = editor.store.listen(
      () => {
        if (saveTimer.current) {
          clearTimeout(saveTimer.current);
        }
        saveTimer.current = setTimeout(async () => {
          const snapshot = getSnapshot(editor.store);
          await persistBoardSnapshot(snapshot);
        }, 1200);
      },
      { source: "user", scope: "document" },
    );
    return () => {
      unsubscribe();
      if (saveTimer.current) {
        clearTimeout(saveTimer.current);
      }
    };
  }, [editor, persistBoardSnapshot]);

  const addMetricCard = useCallback(
    (indicatorKey: string) => {
      if (!editor) {
        return;
      }
      const bounds = editor.getViewportPageBounds();
      editor.createShapes([
        {
          type: "indicator",
          x: bounds.center.x - 180 + Math.random() * 30,
          y: bounds.center.y - 140 + Math.random() * 30,
          props: {
            indicatorKey,
            variant: "metric",
            w: 360,
            h: 280,
          },
        },
      ]);
    },
    [editor],
  );

  const addThemeCard = useCallback(
    (themeName: string) => {
      if (!editor) {
        return;
      }
      const bounds = editor.getViewportPageBounds();
      editor.createShapes([
        {
          type: "indicator",
          x: bounds.center.x - 210 + Math.random() * 30,
          y: bounds.center.y - 160 + Math.random() * 30,
          props: {
            indicatorKey: "active_themes",
            variant: "theme",
            seriesKey: themeName,
            w: 420,
            h: 320,
          },
        },
      ]);
    },
    [editor],
  );

  const addStockCard = useCallback(
    (symbol: string) => {
      if (!editor) {
        return;
      }
      const bounds = editor.getViewportPageBounds();
      editor.createShapes([
        {
          type: "indicator",
          x: bounds.center.x - 210 + Math.random() * 30,
          y: bounds.center.y - 160 + Math.random() * 30,
          props: {
            indicatorKey: "stock_kline_daily",
            variant: "stock",
            seriesKey: symbol,
            w: 420,
            h: 320,
          },
        },
      ]);
    },
    [editor],
  );

  const dataValue = useMemo(
    () => ({ indicators, themes, stocks }),
    [indicators, themes, stocks],
  );
  const totalAssets = indicators.length + themes.length + stocks.length;
  const metricIndicators = useMemo(
    () => indicators.filter((item) => item.key !== "active_themes"),
    [indicators],
  );

  const triggerFetch = useCallback(async () => {
    setIsTriggeringFetch(true);
    setFetchFeedback(null);
    try {
      const result: FetchRunResult = await runFetchJob(
        adminKey.trim() || undefined,
      );
      setFetchFeedback(
        `Fetched ${result.indicator_count} indicators, ${result.theme_count} themes, and ${result.stock_kline_count} stock rows for ${result.as_of}.`,
      );
      await reloadDashboard();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to run fetch job";
      setFetchFeedback(message);
    } finally {
      setIsTriggeringFetch(false);
    }
  }, [adminKey, reloadDashboard]);

  return (
    <IndicatorDataProvider value={dataValue}>
      <div className="relative h-full w-full">
        <div className="absolute bottom-6 left-6 top-28 z-20 w-[360px] overflow-hidden rounded-[24px] border border-[color:var(--border)] bg-[color:var(--card)]/85 backdrop-blur-xl shadow-glass">
          <div className="flex h-full flex-col">
            <CardHeader className="border-b border-white/5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <CardDescription>Workspace</CardDescription>
                  <CardTitle className="mt-2 text-zinc-100">
                    Live Indicator Library
                  </CardTitle>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => void reloadDashboard()}
                >
                  <RefreshCcw className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                As of {asOf ?? "--"}
              </p>
            </CardHeader>
            <CardContent className="flex-1 space-y-6 overflow-y-auto pb-5 pt-5">
              {loadError ? (
                <div className="rounded-[18px] border border-red-500/20 bg-red-500/8 px-4 py-3 text-sm text-red-100">
                  {loadError}
                </div>
              ) : null}
              {isLoading ? (
                <div className="rounded-[18px] border border-white/5 bg-black/20 px-4 py-3 text-sm text-zinc-400">
                  Loading dashboard snapshot...
                </div>
              ) : null}
              {!isLoading && !loadError && totalAssets === 0 ? (
                <div className="rounded-[18px] border border-white/5 bg-black/20 px-4 py-3 text-sm text-zinc-400">
                  No indicator data yet. Run a fetch job to seed the first
                  trading-day snapshot.
                </div>
              ) : null}
              <section>
                <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-zinc-500">
                  <Play className="h-4 w-4 text-amber-400" />
                  Data Ops
                </div>
                <div className="space-y-3 rounded-[18px] border border-white/5 bg-black/20 p-4">
                  <p className="text-sm text-zinc-200">
                    Trigger the daily fetch pipeline without leaving the board.
                  </p>
                  <input
                    type="password"
                    value={adminKey}
                    onChange={(event) => setAdminKey(event.target.value)}
                    placeholder="Admin API key (optional)"
                    className="h-11 w-full rounded-[14px] border border-white/8 bg-black/30 px-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-white/20"
                  />
                  <Button
                    variant="accent"
                    className="w-full"
                    onClick={() => void triggerFetch()}
                    disabled={isTriggeringFetch}
                  >
                    <Play className="h-4 w-4" />
                    {isTriggeringFetch ? "Running Fetch..." : "Run Fetch Now"}
                  </Button>
                  {fetchFeedback ? (
                    <div className="rounded-[14px] border border-white/5 bg-black/30 px-3 py-2 text-sm text-zinc-300">
                      {fetchFeedback}
                    </div>
                  ) : null}
                </div>
              </section>
              <section>
                <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-zinc-500">
                  <BarChart3 className="h-4 w-4" />
                  Core Metrics
                </div>
                <div className="space-y-2">
                  {metricIndicators.map((indicator) => (
                    <button
                      key={indicator.key}
                      type="button"
                      onClick={() => addMetricCard(indicator.key)}
                      className="flex w-full items-center justify-between rounded-[18px] border border-white/5 bg-black/20 px-4 py-3 text-left transition hover:border-white/10 hover:bg-white/[0.03]"
                    >
                      <div>
                        <p className="text-sm text-zinc-100">
                          {indicator.title}
                        </p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-zinc-500">
                          {indicator.key}
                        </p>
                      </div>
                      <Plus className="h-4 w-4 text-zinc-400" />
                    </button>
                  ))}
                  {!isLoading && metricIndicators.length === 0 ? (
                    <div className="rounded-[18px] border border-dashed border-white/8 px-4 py-3 text-sm text-zinc-500">
                      No metric indicators available.
                    </div>
                  ) : null}
                </div>
              </section>
              <section>
                <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-zinc-500">
                  <BarChart3 className="h-4 w-4 text-emerald-400" />
                  Active Themes
                </div>
                <div className="space-y-2">
                  {themes.map((theme) => (
                    <button
                      key={theme.theme_name}
                      type="button"
                      onClick={() => addThemeCard(theme.theme_name)}
                      className="flex w-full items-center justify-between rounded-[18px] border border-white/5 bg-black/20 px-4 py-3 text-left transition hover:border-white/10 hover:bg-white/[0.03]"
                    >
                      <div>
                        <p className="text-sm text-zinc-100">
                          {theme.theme_name}
                        </p>
                        <p className="mt-1 font-mono text-xs text-zinc-500">
                          #{theme.rank} /{" "}
                          {(theme.latest_turnover / 100000000).toFixed(2)}B
                        </p>
                      </div>
                      <Plus className="h-4 w-4 text-zinc-400" />
                    </button>
                  ))}
                  {!isLoading && themes.length === 0 ? (
                    <div className="rounded-[18px] border border-dashed border-white/8 px-4 py-3 text-sm text-zinc-500">
                      No active themes available.
                    </div>
                  ) : null}
                </div>
              </section>
              <section>
                <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.22em] text-zinc-500">
                  <BarChart3 className="h-4 w-4 text-sky-400" />
                  Tracked Equities
                </div>
                <div className="space-y-2">
                  {stocks.map((stock) => (
                    <button
                      key={stock.symbol}
                      type="button"
                      onClick={() => addStockCard(stock.symbol)}
                      className="flex w-full items-center justify-between rounded-[18px] border border-white/5 bg-black/20 px-4 py-3 text-left transition hover:border-white/10 hover:bg-white/[0.03]"
                    >
                      <div>
                        <p className="text-sm text-zinc-100">
                          {stock.name
                            ? `${stock.name} · ${stock.symbol}`
                            : stock.symbol}
                        </p>
                        <p className="mt-1 font-mono text-xs text-zinc-500">
                          {stock.latest_close?.toFixed(2) ?? "--"} /{" "}
                          {stock.latest_pct_change !== null &&
                          stock.latest_pct_change !== undefined
                            ? `${stock.latest_pct_change.toFixed(2)}%`
                            : "--"}
                        </p>
                      </div>
                      <Plus className="h-4 w-4 text-zinc-400" />
                    </button>
                  ))}
                  {!isLoading && stocks.length === 0 ? (
                    <div className="rounded-[18px] border border-dashed border-white/8 px-4 py-3 text-sm text-zinc-500">
                      No tracked equities available.
                    </div>
                  ) : null}
                </div>
              </section>
            </CardContent>
            <div className="flex items-center justify-between border-t border-white/5 px-5 py-4 text-xs uppercase tracking-[0.2em] text-zinc-500">
              <div className="flex items-center gap-2">
                <Save className="h-4 w-4" />
                {isSaving ? "Saving" : "Synced"}
              </div>
              <span>{totalAssets} assets</span>
            </div>
          </div>
        </div>
        <div className="h-full w-full">
          <Tldraw
            store={store}
            shapeUtils={[...defaultShapeUtils, IndicatorShapeUtil]}
            onMount={(mountedEditor) => {
              setEditor(mountedEditor);
            }}
            inferDarkMode
            autoFocus
          />
        </div>
      </div>
    </IndicatorDataProvider>
  );
}
