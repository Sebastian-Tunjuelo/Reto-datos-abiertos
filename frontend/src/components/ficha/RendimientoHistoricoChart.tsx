"use client";

import dynamic from "next/dynamic";
import type { SeriePunto } from "@/components/FichaMunicipal";
import { InfoTooltip } from "@/components/ui/info-tooltip";

// react-plotly.js must be client-only (no SSR)
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  serie: SeriePunto[];
  cultivo: string;
  municipio: string;
}

export default function RendimientoHistoricoChart({
  serie,
  cultivo,
  municipio,
}: Props) {
  if (serie.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-sm font-semibold mb-3">Rendimiento histórico</h2>
        <p className="text-sm text-muted-foreground">
          Sin histórico disponible.
        </p>
      </div>
    );
  }

  const años = serie.map((p) => p.año);
  const rend = serie.map((p) => p.rendimiento);
  const prom3a = serie.map((p) => p.rendimiento_prom3a);

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center gap-1.5 mb-1">
        <h2 className="text-sm font-semibold">Rendimiento histórico</h2>
        <InfoTooltip
          label="Qué significa rendimiento histórico"
          description="Serie de producción por año para el municipio y cultivo seleccionados."
        />
      </div>
      <p className="inline-flex items-center gap-1 text-xs text-muted-foreground mb-3">
        {municipio} · {cultivo} · t/ha por año
        <InfoTooltip
          label="Qué significa t/ha por año"
          description="t/ha significa toneladas por hectárea, y por año indica el valor registrado o estimado en cada temporada."
        />
      </p>
      <Plot
        data={[
          {
            x: años,
            y: rend,
            type: "scatter",
            mode: "lines+markers",
            name: "Rendimiento",
            line: { color: "#16a34a", width: 2 },
            marker: { color: "#16a34a", size: 6 },
            connectgaps: true,
          },
          {
            x: años,
            y: prom3a,
            type: "scatter",
            mode: "lines",
            name: "Promedio 3 años",
            line: { color: "#f59e0b", width: 2, dash: "dot" },
            connectgaps: true,
          },
        ]}
        layout={{
          autosize: true,
          height: 260,
          margin: { t: 10, r: 20, b: 40, l: 50 },
          xaxis: {
            title: { text: "Año", font: { size: 11 } },
            tickfont: { size: 11 },
            dtick: 1,
          },
          yaxis: {
            title: { text: "t/ha", font: { size: 11 } },
            tickfont: { size: 11 },
          },
          legend: { orientation: "h", y: -0.25, font: { size: 11 } },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { family: "Nunito, sans-serif" },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
