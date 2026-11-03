export type Timeframe = "Y" | "HY" | "Q" | "M" | "W" | "D";

export const TIMEFRAMES: Timeframe[] = ["Y", "HY", "Q", "M", "W", "D"];

export interface Instrument {
  symbol: string;
  name: string;
  industry: string | null;
  isin: string;
  instrument_key: string;
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CandlesResponse {
  symbol: string;
  timeframe: Timeframe;
  empty: boolean;
  candles: Candle[];
}

export interface DetectedZone {
  pattern: string;
  type: "demand" | "supply";
  top: number;
  bottom: number;
  startIndex: number;
  startTime: string;
  completedIndex: number;
}

export interface ChartZone extends DetectedZone {
  sourceTimeframe: Timeframe;
}

export interface ZonesResponse {
  symbol: string;
  timeframe: Timeframe;
  empty: boolean;
  zones: DetectedZone[];
}
export interface CandleClass {
  time: string;
  strong: boolean;
  base: boolean;
  direction: number;
}

export interface CandleClassesResponse {
  symbol: string;
  timeframe: Timeframe;
  classes: CandleClass[];
}
