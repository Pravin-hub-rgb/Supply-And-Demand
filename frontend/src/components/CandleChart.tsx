"use client";

import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type IRange,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import type { Candle, CandleClass, ChartZone, Timeframe } from "../lib/types";
import type { DetectedZone } from "../lib/types";
import { ZoneRectanglesPrimitive } from "../lib/zoneRectangles";
import type { ChartMemory } from "../lib/chartMemory";

interface Ohlcv {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

function pad(value: number) {
  return String(value).padStart(2, "0");
}

function timeKey(time: Time): string {
  if (typeof time === "string") return time.slice(0, 10);
  if (typeof time === "number") return new Date(time * 1000).toISOString().slice(0, 10);
  return `${time.year}-${pad(time.month)}-${pad(time.day)}`;
}

function toOhlcv(candle: Candle): Ohlcv {
  return { open: candle.open, high: candle.high, low: candle.low, close: candle.close, volume: candle.volume };
}

function toBusinessDay(time: string) {
  const [year, month, day] = time.slice(0, 10).split("-").map(Number);
  return { year, month, day };
}

function normalizeRange(range: IRange<number>): IRange<number> {
  return { from: range.from, to: range.to };
}

function safeLogicalRange(chart: IChartApi): IRange<number> | null {
  try {
    const range = chart.timeScale().getVisibleLogicalRange();
    return range ? normalizeRange(range) : null;
  } catch (error) {
    console.warn("Could not read chart visible logical range", error);
    return null;
  }
}

function rememberRange(memory: ChartMemory, key: string, range: IRange<number>) {
  const normalized = normalizeRange(range);
  memory.views.set(key, normalized);
  memory.last = normalized;
}

interface Props {
  candles: Candle[];
  timeframe: Timeframe;
  symbol: string;
  memory: ChartMemory;
  zones?: ChartZone[];
  candleClasses?: CandleClass[];
}

export default function CandleChart({ candles, timeframe, symbol, memory, zones, candleClasses }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const previousKeyRef = useRef(`${symbol}:${timeframe}`);
  const hasDataRef = useRef(false);
  const candleByTimeRef = useRef<Map<string, Ohlcv>>(new Map());
  const lastOhlcvRef = useRef<Ohlcv | null>(null);
  const zonePrimitiveRef = useRef<ZoneRectanglesPrimitive | null>(null);
  const markersPluginRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const [ohlcv, setOhlcv] = useState<Ohlcv | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      layout: {
        background: { type: ColorType.Solid, color: "#000000" },
        textColor: "#8b98ab",
      },
      grid: {
        vertLines: { color: "#1f2a3d" },
        horzLines: { color: "#1f2a3d" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#1f2a3d" },
      timeScale: { borderColor: "#1f2a3d" },
    });
    chartRef.current = chart;
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderUpColor: "#26a69a",
      borderDownColor: "#ef5350",
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });
    seriesRef.current = series;

    const primitive = new ZoneRectanglesPrimitive();
    series.attachPrimitive(primitive);
    zonePrimitiveRef.current = primitive;
    primitive.setZones(zones ?? []);

    markersPluginRef.current = createSeriesMarkers(series, []);

    chart.subscribeCrosshairMove((param) => {
      const key = param.time ? timeKey(param.time) : null;
      const hovered = key ? candleByTimeRef.current.get(key) : undefined;
      setOhlcv(hovered ?? lastOhlcvRef.current);
    });

    const resizeObserver = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
    resizeObserver.observe(container);
    return () => {
      if (seriesRef.current && zonePrimitiveRef.current) {
        seriesRef.current.detachPrimitive(zonePrimitiveRef.current);
      }
      zonePrimitiveRef.current = null;
      markersPluginRef.current = null;
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      hasDataRef.current = false;
    };
  }, []);

  useEffect(() => {
    zonePrimitiveRef.current?.setZones(zones ?? []);
  }, [zones]);

  useEffect(() => {
    if (!markersPluginRef.current) return;
    const markers: SeriesMarker<Time>[] = (candleClasses ?? [])
      .filter((item) => item.strong || item.base)
      .map((item) => ({
        time: toBusinessDay(item.time) as Time,
        position: "belowBar",
        color: item.strong ? "#26a69a" : "#facc15",
        shape: item.strong ? "arrowUp" : "circle",
        text: item.strong ? "S" : "B",
      }));
    markersPluginRef.current.setMarkers(markers);
  }, [candleClasses]);

  useEffect(() => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series) return;

    const currentKey = `${symbol}:${timeframe}`;
    if (hasDataRef.current) {
      const previousKey = previousKeyRef.current;
      const range = safeLogicalRange(chart);
      if (range) rememberRange(memory, previousKey, range);
    }
    if (!candles.length) {
      candleByTimeRef.current = new Map();
      lastOhlcvRef.current = null;
      setOhlcv(null);
      series.setData([]);
      return;
    }

    series.setData(candles.map((candle) => ({ ...candle, time: toBusinessDay(candle.time) })));
    candleByTimeRef.current = new Map(candles.map((candle) => [candle.time.slice(0, 10), toOhlcv(candle)]));
    const latest = toOhlcv(candles[candles.length - 1]);
    lastOhlcvRef.current = latest;
    setOhlcv(latest);
    const savedRange = memory.views.get(currentKey) ?? memory.last;
    if (savedRange) {
      try {
        chart.timeScale().setVisibleLogicalRange(savedRange);
        memory.views.set(currentKey, normalizeRange(savedRange));
        memory.last = normalizeRange(savedRange);
      } catch (error) {
        console.warn("Could not restore chart visible logical range", error);
      }
    }
    hasDataRef.current = true;
    previousKeyRef.current = currentKey;
  }, [candles, memory, symbol, timeframe]);

  return (
    <div className="chart-shell">
      {ohlcv ? (
        <div className="ohlcv-overlay" aria-label="Hovered candle OHLCV">
          <span className="ohlcv-o">O: {ohlcv.open.toFixed(2)}</span>
          <span className="ohlcv-h">H: {ohlcv.high.toFixed(2)}</span>
          <span className="ohlcv-l">L: {ohlcv.low.toFixed(2)}</span>
          <span className="ohlcv-c">C: {ohlcv.close.toFixed(2)}</span>
          <span className="ohlcv-v">Vol: {Math.round(ohlcv.volume).toLocaleString()}</span>
        </div>
      ) : null}
      <div ref={containerRef} className="chart-panel" />
    </div>
  );
}
