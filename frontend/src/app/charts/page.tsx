"use client";

import { useEffect, useMemo, useState } from "react";
import CandleChart from "../../components/CandleChart";
import StockSidebar from "../../components/StockSidebar";
import TimeframeSwitch from "../../components/TimeframeSwitch";
import { ApiError, getCandles, getInstruments } from "../../lib/api";
import type { CandlesResponse, Instrument, Timeframe } from "../../lib/types";

export default function ChartsPage() {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [instrumentsError, setInstrumentsError] = useState<string | null>(null);
  const [instrumentsLoading, setInstrumentsLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<Timeframe>("M");
  const [candlesResponse, setCandlesResponse] = useState<CandlesResponse | null>(null);
  const [candlesError, setCandlesError] = useState<string | null>(null);
  const [candlesLoading, setCandlesLoading] = useState(false);
  const [reloadTick, setReloadTick] = useState(0);

  const selected = useMemo(
    () => instruments.find((instrument) => instrument.symbol === selectedSymbol) ?? null,
    [instruments, selectedSymbol],
  );

  useEffect(() => {
    let cancelled = false;
    setInstrumentsLoading(true);
    setInstrumentsError(null);
    getInstruments()
      .then((data) => {
        if (cancelled) return;
        setInstruments(data);
        setSelectedSymbol((current) => current ?? data[0]?.symbol ?? null);
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
          {!candlesError && candlesResponse && !candlesResponse.empty ? <CandleChart candles={candlesResponse.candles} /> : null}
        </section>
      </section>
    </main>
  );
}
