import type { CandleClass, CandleClassesResponse, CandlesResponse, DetectedZone, Instrument, Timeframe, ZonesResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8011";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function readJson<T>(response: Response): Promise<T> {
  let body: unknown;
  try {
    body = await response.json();
  } catch (error) {
    throw new ApiError("Backend returned invalid JSON", response.status);
  }
  if (!response.ok) {
    const detail = typeof body === "object" && body && "detail" in body ? String((body as { detail: unknown }).detail) : "request failed";
    throw new ApiError(detail, response.status);
  }
  return body as T;
}

export async function getInstruments(): Promise<Instrument[]> {
  const response = await fetch(`${API_BASE}/api/instruments`, { cache: "no-store" });
  return readJson<Instrument[]>(response);
}

export async function getCandles(symbol: string, timeframe: Timeframe): Promise<CandlesResponse> {
  const response = await fetch(`${API_BASE}/api/candles/${encodeURIComponent(symbol)}?timeframe=${timeframe}`, { cache: "no-store" });
  return readJson<CandlesResponse>(response);
}

export async function getZones(symbol: string, timeframe: Timeframe = "Y"): Promise<ZonesResponse> {
  const response = await fetch(`${API_BASE}/api/zones/${encodeURIComponent(symbol)}?timeframe=${timeframe}`, { cache: "no-store" });
  return readJson<ZonesResponse>(response);
}

export async function getCandleClasses(symbol: string, timeframe: Timeframe): Promise<CandleClassesResponse> {
  const response = await fetch(`${API_BASE}/api/candle-classes/${encodeURIComponent(symbol)}?timeframe=${timeframe}`, { cache: "no-store" });
  return readJson<CandleClassesResponse>(response);
}
