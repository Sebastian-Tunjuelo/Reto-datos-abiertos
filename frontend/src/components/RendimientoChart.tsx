"use client";

import React from "react";
import Plot from "react-plotly.js";

interface SeriePunto {
  año: number;
  rendimiento: number | null;
  rendimiento_prom3a: number | null;
}

interface Props {
  serie: SeriePunto[];
  cultivo: string;
}

export default function RendimientoChart({ serie, cultivo }: Props) {
  const años = serie.map((p) => p.año);
  const rend = serie.map((p) => p.rendimiento);
  const prom3a = serie.map((p) => p.rendimiento_prom3a);

  const traces: Plotly.Data[] = [
    {
      x: años,
      y: rend,
      type: "scatter",
      mode: "lines+markers",
      name: "Rendimiento (t/ha)",
      line: { color: "#16a34a", width: 2 },
      marker: { size: 6, color: "#16a34a" },
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
  ];

  const layout: Partial<Plotly.Layout> = {
    height: 220,
    margin: { t: 10, r: 10, b: 40, l: 45 },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { family: "Nunito, sans-serif", size: 12 },
    xaxis: {
      tickformat: "d",
      gridcolor: "#e5e7eb",
      linecolor: "#e5e7eb",
    },
    yaxis: {
      gridcolor: "#e5e7eb",
      linecolor: "#e5e7eb",
      rangemode: "tozero",
    },
    legend: {
      orientation: "h",
      y: -0.25,
      x: 0,
      font: { size: 11 },
    },
    hovermode: "x unified",
  };

  return (
    <Plot
      data={traces}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
