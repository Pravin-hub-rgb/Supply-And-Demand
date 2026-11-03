"use client";

import { TIMEFRAMES, type Timeframe } from "../lib/types";

const LABELS: Record<Timeframe, string> = {
  Y: "Y",
  HY: "HY",
  Q: "Q",
  M: "M",
  W: "W",
  D: "D",
};

export default function TimeframeSwitch({ value, onChange }: { value: Timeframe; onChange: (timeframe: Timeframe) => void }) {
  return (
    <div className="timeframe-switch" aria-label="Timeframe">
      {TIMEFRAMES.map((timeframe) => (
        <button
          className="timeframe-button"
          key={timeframe}
          type="button"
          aria-pressed={timeframe === value}
          onClick={() => onChange(timeframe)}
        >
          {LABELS[timeframe]}
        </button>
      ))}
    </div>
  );
}
