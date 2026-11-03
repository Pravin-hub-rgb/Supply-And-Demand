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
