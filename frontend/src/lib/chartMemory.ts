import type { IRange } from "lightweight-charts";

export interface ChartMemory {
  views: Map<string, IRange<number>>;
  last: IRange<number> | null;
}

export function createChartMemory(): ChartMemory {
  return { views: new Map(), last: null };
}
