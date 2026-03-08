"use client";

import { createContext, useContext } from "react";

import type {
  DashboardIndicator,
  ThemeSeries,
  TrackedStockSeries,
} from "@limitboard/db-types";

type IndicatorDataContextValue = {
  indicators: DashboardIndicator[];
  themes: ThemeSeries[];
  stocks: TrackedStockSeries[];
};

const IndicatorDataContext = createContext<IndicatorDataContextValue>({
  indicators: [],
  themes: [],
  stocks: [],
});

export function IndicatorDataProvider({
  value,
  children,
}: {
  value: IndicatorDataContextValue;
  children: React.ReactNode;
}) {
  return (
    <IndicatorDataContext.Provider value={value}>
      {children}
    </IndicatorDataContext.Provider>
  );
}

export function useIndicatorData() {
  return useContext(IndicatorDataContext);
}
