"use client";

import { useEffect, useMemo, useState } from "react";
import type { Instrument } from "../lib/types";

interface Props {
  instruments: Instrument[];
  selectedSymbol: string | null;
  onSelect: (symbol: string) => void;
}

export default function StockSidebar({ instruments, selectedSymbol, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return instruments;
    return instruments.filter((instrument) =>
      [instrument.symbol, instrument.name, instrument.industry ?? "", instrument.isin]
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }, [instruments, query]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) return;
      if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
      if (filtered.length === 0) return;
      event.preventDefault();
      const currentIndex = filtered.findIndex((instrument) => instrument.symbol === selectedSymbol);
      const nextIndex =
        event.key === "ArrowDown"
          ? currentIndex < 0
            ? 0
            : Math.min(currentIndex + 1, filtered.length - 1)
          : currentIndex < 0
            ? filtered.length - 1
            : Math.max(currentIndex - 1, 0);
      onSelect(filtered[nextIndex].symbol);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [filtered, selectedSymbol, onSelect]);

  return (
    <aside className="sidebar" aria-label="Nifty 50 stocks">
      <div className="sidebar-header">
        <h1>SupplynDemand</h1>
        <p>Nifty 50 higher-timeframe chart study</p>
        <input
          className="search"
          type="search"
          placeholder="Search symbol, name, industry..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="Search Nifty 50 stocks"
        />
      </div>
      <div className="instrument-list">
        {filtered.map((instrument) => (
          <button
            className="instrument-row"
            key={instrument.symbol}
            type="button"
            aria-current={instrument.symbol === selectedSymbol}
            onClick={() => onSelect(instrument.symbol)}
          >
            <span>
              <strong>{instrument.symbol}</strong>
              <br />
              <span>{instrument.name}</span>
              <br />
              <span>{instrument.industry ?? "Nifty 50"}</span>
            </span>
          </button>
        ))}
        {filtered.length === 0 ? <div className="state-box">No matches for {query}</div> : null}
      </div>
    </aside>
  );
}
