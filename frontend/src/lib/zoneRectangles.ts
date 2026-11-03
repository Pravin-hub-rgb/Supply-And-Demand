import type {
  IChartApi,
  IPrimitivePaneRenderer,
  IPrimitivePaneView,
  ISeriesApi,
  ISeriesPrimitive,
  Time,
} from "lightweight-charts";
import type { ChartZone } from "./types";

function toBusinessDay(time: string) {
  const [year, month, day] = time.slice(0, 10).split("-").map(Number);
  return { year, month, day };
}

function zoneColors(zone: ChartZone): { fill: string; stroke: string } {
  const demand = zone.type === "demand";
  switch (zone.sourceTimeframe) {
    case "Y":
      return { fill: "rgba(0, 188, 212, 0.8)", stroke: "#e53935" };
    case "HY":
      return { fill: "rgba(74, 20, 140, 0.8)", stroke: "#e53935" };
    case "Q":
      return demand
        ? { fill: "rgba(27, 94, 32, 0.8)", stroke: "#e53935" }
        : { fill: "rgba(13, 71, 161, 0.8)", stroke: "#e53935" };
    case "M":
      return demand
        ? { fill: "rgba(251, 192, 45, 0.8)", stroke: "#e53935" }
        : { fill: "rgba(239, 108, 0, 0.8)", stroke: "#e53935" };
    case "W":
      return demand
        ? { fill: "rgba(0, 230, 118, 0.8)", stroke: "#e53935" }
        : { fill: "rgba(229, 57, 53, 0.8)", stroke: "#e53935" };
    case "D":
      return demand
        ? { fill: "rgba(255, 182, 193, 0.8)", stroke: "#e53935" }
        : { fill: "rgba(117, 117, 117, 0.8)", stroke: "#e53935" };
    default:
      return demand
        ? { fill: "rgba(38, 166, 154, 0.8)", stroke: "#e53935" }
        : { fill: "rgba(239, 83, 80, 0.8)", stroke: "#e53935" };
  }
}

class ZoneRenderer implements IPrimitivePaneRenderer {
  private zones: ChartZone[] = [];
  private chart?: IChartApi;
  private series?: ISeriesApi<"Candlestick">;

  setContext(chart?: IChartApi, series?: ISeriesApi<"Candlestick">) {
    this.chart = chart;
    this.series = series;
  }

  setZones(zones: ChartZone[]) {
    this.zones = zones;
  }

  draw(target: { useMediaCoordinateSpace: (fn: (scope: { context: CanvasRenderingContext2D }) => void) => void }) {
    const chart = this.chart;
    const series = this.series;
    if (!chart || !series || this.zones.length === 0) return;
    target.useMediaCoordinateSpace(({ context }) => {
      for (const zone of this.zones) {
        const x1Raw = chart.timeScale().timeToCoordinate(toBusinessDay(zone.startTime) as unknown as Time);
        if (x1Raw === null) continue;
        const x1 = x1Raw;
        const x2 = chart.timeScale().width();
        const yTop = series.priceToCoordinate(zone.top);
        const yBottom = series.priceToCoordinate(zone.bottom);
        if (x1 === null || yTop === null || yBottom === null) continue;
        const left = Math.max(0, x1);
        const top = Math.min(yTop, yBottom);
        const bottom = Math.max(yTop, yBottom);
        const width = Math.max(1, x2 - left);
        const height = Math.max(1, bottom - top);
        const colors = zoneColors(zone);
        context.save();
        context.globalAlpha = 1;
        context.fillStyle = colors.fill;
        context.fillRect(left, top, width, height);
        context.strokeStyle = colors.stroke;
        context.lineWidth = 1;
        context.strokeRect(left, top, width, height);
        context.restore();
      }
    });
  }
}

class ZonePaneView implements IPrimitivePaneView {
  private rendererInstance = new ZoneRenderer();
  private zones: ChartZone[] = [];

  setContext(chart?: IChartApi, series?: ISeriesApi<"Candlestick">) {
    this.rendererInstance.setContext(chart, series);
  }

  setZones(zones: ChartZone[]) {
    this.zones = zones;
    this.rendererInstance.setZones(zones);
  }

  hasZones() {
    return this.zones.length > 0;
  }

  zOrder() {
    return "bottom" as const;
  }

  renderer(): IPrimitivePaneRenderer | null {
    return this.rendererInstance;
  }
}

export class ZoneRectanglesPrimitive implements ISeriesPrimitive<Time> {
  private chart?: IChartApi;
  private series?: ISeriesApi<"Candlestick">;
  private requestUpdate?: () => void;
  private zones: ChartZone[] = [];
  private view = new ZonePaneView();

  setZones(zones: ChartZone[]) {
    this.zones = zones;
    this.view.setZones(zones);
    this.requestUpdate?.();
  }

  attached(param: any) {
    this.chart = param.chart;
    this.series = param.series;
    this.requestUpdate = param.requestUpdate;
    this.view.setContext(this.chart, this.series);
    this.view.setZones(this.zones);
  }

  detached() {
    this.chart = undefined;
    this.series = undefined;
    this.requestUpdate = undefined;
    this.view.setContext(undefined, undefined);
  }

  updateAllViews() {
    this.view.setZones(this.zones);
  }

  paneViews() {
    return this.view.hasZones() ? [this.view] : [];
  }
}
