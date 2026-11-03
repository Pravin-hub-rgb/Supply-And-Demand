"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import CandleChart from "../../components/CandleChart";
import StockSidebar from "../../components/StockSidebar";
import TimeframeSwitch from "../../components/TimeframeSwitch";
import { createChartMemory } from "../../lib/chartMemory";
import { getCandles, getInstruments, getZones, getCandleClasses } from "../../lib/api";
import type { CandleClass, CandlesResponse, ChartZone, DetectedZone, Instrument, Timeframe } from "../../lib/types";

export default function ChartsPage() {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [instrumentsError, setInstrumentsError] = useState<string | null>(null);
  const [instrumentsLoading, setInstrumentsLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<Timeframe>("M");
  const [candlesResponse, setCandlesResponse] = useState<CandlesResponse | null>(null);
  const [candlesError, setCandlesError] = useState<string | null>(null);
  const [candlesLoading, setCandlesLoading] = useState(false);
  const [zonesByTimeframe, setZonesByTimeframe] = useState<Partial<Record<Timeframe, ChartZone[]>>>({});
  const [zonesError, setZonesError] = useState<string | null>(null);
  const [candleClasses, setCandleClasses] = useState<CandleClass[]>([]);
  const [reloadTick, setReloadTick] = useState(0);
  const chartMemoryRef = useRef(createChartMemory());

  const selected = useMemo(
    () => instruments.find((instrument) => instrument.symbol === selectedSymbol) ?? null,
    [instruments, selectedSymbol],
  );

  const TIMEFRAME_RANK: Record<Timeframe, number> = { D: 0, W: 1, M: 2, Q: 3, HY: 4, Y: 5 };
  const displayedZones = useMemo(
    () =>
      (Object.entries(zonesByTimeframe) as [Timeframe, ChartZone[] | undefined][]).flatMap(([tf, zones]) =>
        TIMEFRAME_RANK[tf] >= TIMEFRAME_RANK[timeframe] ? zones ?? [] : [],
      ),
    [zonesByTimeframe, timeframe],
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedSymbol = localStorage.getItem("charts.selectedSymbol");
    const storedTimeframe = localStorage.getItem("charts.timeframe");
    if (storedSymbol) setSelectedSymbol(storedSymbol);
    if (
      storedTimeframe === "Y" ||
      storedTimeframe === "HY" ||
      storedTimeframe === "Q" ||
      storedTimeframe === "M" ||
      storedTimeframe === "W" ||
      storedTimeframe === "D"
    ) {
      setTimeframe(storedTimeframe);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    setInstrumentsLoading(true);
    setInstrumentsError(null);
    getInstruments()
      .then((data) => {
        if (cancelled) return;
        setInstruments(data);
        setSelectedSymbol((current) => {
          if (current && data.some((instrument) => instrument.symbol === current)) return current;
          return data[0]?.symbol ?? null;
        });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setInstrumentsError(error instanceof Error ? error.message : String(error));
      })
      .finally(() => {
        if (!cancelled) setInstrumentsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadTick]);

  useEffect(() => {
    if (!selectedSymbol) {
      setCandlesResponse(null);
      return;
    }
    let cancelled = false;
    setCandlesLoading(true);
    setCandlesError(null);
    getCandles(selectedSymbol, timeframe)
      .then((data) => {
        if (!cancelled) setCandlesResponse(data);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setCandlesResponse(null);
        setCandlesError(error instanceof Error ? error.message : String(error));
      })
      .finally(() => {
        if (!cancelled) setCandlesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSymbol, timeframe, reloadTick]);

  useEffect(() => {
    if (!selectedSymbol) {
      setZonesByTimeframe({});
      setZonesError(null);
      return;
    }
    let cancelled = false;
    const timeframes: Timeframe[] = ["Y", "HY", "Q", "M", "W", "D"];
    Promise.all(
      timeframes.map(async (tf) => {
        const data = await getZones(selectedSymbol, tf);
        return [tf, data.zones.map((zone) => ({ ...zone, sourceTimeframe: tf }))] as const;
      }),
    )
      .then((results) => {
        if (cancelled) return;
        const next: Partial<Record<Timeframe, ChartZone[]>> = {};
        for (const [tf, zones] of results) next[tf] = zones;
        setZonesByTimeframe(next);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setZonesByTimeframe({});
        setZonesError(error instanceof Error ? error.message : String(error));
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSymbol, reloadTick]);

  useEffect(() => {
    if (!selectedSymbol) {
      setCandleClasses([]);
      return;
    }
    let cancelled = false;
    getCandleClasses(selectedSymbol, timeframe)
      .then((data) => {
        if (!cancelled) setCandleClasses(data.classes);
      })
      .catch(() => {
        if (!cancelled) setCandleClasses([]);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedSymbol, timeframe, reloadTick]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (selectedSymbol) localStorage.setItem("charts.selectedSymbol", selectedSymbol);
  }, [selectedSymbol]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem("charts.timeframe", timeframe);
  }, [timeframe]);

  if (!instruments.length && instrumentsError) {
    return (
      <main className="state-box error-box">
        <div>
          <p>Could not load the Nifty 50 list from the backend.</p>
          <p>{instrumentsError}</p>
          <button className="retry" type="button" onClick={() => setReloadTick((tick) => tick + 1)}>
            Retry
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="charts-shell">
      <StockSidebar instruments={instruments} selectedSymbol={selectedSymbol} onSelect={setSelectedSymbol} />
      <section className="workspace" aria-label="Chart workspace">
        <header className="topbar">
          <div className="title-block">
            <h2>{selected?.symbol ?? "Select a stock"}</h2>
            <p>{selected?.name ?? (instrumentsLoading ? "Loading Nifty 50…" : "")}</p>
          </div>
          <TimeframeSwitch value={timeframe} onChange={setTimeframe} />
        </header>
        <section className="chart-area" aria-label="Candlestick chart">
          {candlesLoading && !candlesResponse ? <div className="state-box">Loading {timeframe} candles…</div> : null}
          {candlesError ? (
            <div className="state-box error-box">
              <div>
                <p>Could not load candles for {selectedSymbol}.</p>
                <p>{candlesError}</p>
                <button className="retry" type="button" onClick={() => setReloadTick((tick) => tick + 1)}>
                  Retry
                </button>
              </div>
            </div>
          ) : null}
          {!candlesLoading && !candlesError && candlesResponse?.empty ? <div className="state-box">No candles for {selectedSymbol} on {timeframe}.</div> : null}
           {!candlesError && candlesResponse && !candlesResponse.empty && selectedSymbol ? (
             <CandleChart candles={candlesResponse.candles} timeframe={timeframe} symbol={selectedSymbol} memory={chartMemoryRef.current} zones={displayedZones} candleClasses={candleClasses} />
           ) : null}
        </section>
      </section>
    </main>
  );
}
