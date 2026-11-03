"use client";

import { useEffect, useRef } from "react";
import { CandlestickSeries, ColorType, CrosshairMode, createChart } from "lightweight-charts";
import type { Candle } from "../lib/types";

function toBusinessDay(time: string) {
  const [year, month, day] = time.slice(0, 10).split("-").map(Number);
  return { year, month, day };
}

export default function CandleChart({ candles }: { candles: Candle[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      layout: {
        background: { type: ColorType.Solid, color: "#0d1117" },
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
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderUpColor: "#26a69a",
      borderDownColor: "#ef5350",
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });
    series.setData(candles.map((candle) => ({ ...candle, time: toBusinessDay(candle.time) })));

    const resizeObserver = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
    resizeObserver.observe(container);
    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [candles]);

  return <div ref={containerRef} className="chart-panel" />;
}
