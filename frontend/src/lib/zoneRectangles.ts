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
        const x1 = chart.timeScale().timeToCoordinate(toBusinessDay(zone.startTime) as unknown as Time);
        const x2 = chart.timeScale().width();
        const yTop = series.priceToCoordinate(zone.top);
        const yBottom = series.priceToCoordinate(zone.bottom);
        if (x1 === null || yTop === null || yBottom === null) continue;
        const left = Math.max(0, x1);
        const top = Math.min(yTop, yBottom);
        const bottom = Math.max(yTop, yBottom);
        const width = Math.max(1, x2 - left);
        const height = Math.max(1, bottom - top);
        const isDemand = zone.type === "demand";
        context.fillStyle = isDemand ? "rgba(38, 166, 154, 0.14)" : "rgba(239, 83, 80, 0.14)";
        context.fillRect(left, top, width, height);
        context.strokeStyle = isDemand ? "rgba(38, 166, 154, 0.75)" : "rgba(239, 83, 80, 0.75)";
        context.lineWidth = 1;
        context.strokeRect(left, top, width, height);
        context.fillStyle = isDemand ? "#26a69a" : "#ef5350";
        context.font = "12px sans-serif";
        context.fillText(`${zone.sourceTimeframe} ${zone.pattern} ${zone.type}`, left + 6, top + 14);
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
