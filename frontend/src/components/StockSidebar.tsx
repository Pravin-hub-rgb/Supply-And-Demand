"use client";

import { useMemo, useState } from "react";
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
