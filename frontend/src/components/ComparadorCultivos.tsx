"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, RefreshCw, AlertTriangle, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import RankingCard from "@/components/comparador/RankingCard";
import ComparisonTable from "@/components/comparador/ComparisonTable";
import MunicipioSelector from "@/components/comparador/MunicipioSelector";

// ─── Types ────────────────────────────────────────────────────────────────────

export type EtiquetaRiesgo = "Bajo" | "Medio" | "Alto" | "Sin datos";

export interface CultivoComparacion {
  cultivo: string;
  rendimiento_esperado: number | null;
  prob_riesgo_alto: number | null;
  etiqueta_riesgo: EtiquetaRiesgo;
  score: number; // 0–100, higher = better
  estado: "ok" | "sin_datos" | "error";
  error_msg?: string;
}

const CULTIVOS_MVP = ["Café", "Cacao", "Maíz"];
const ANIOS_DISPONIBLES = [2025, 2026, 2027];

// Score: penaliza prob_riesgo_alto y premia rendimiento relativo
function calcScore(
  prob: number | null,
  rend: number | null,
  maxRend: number
): number {
  if (prob === null) return 0;
  const riskPenalty = prob * 60; // 0–60 pts de penalización
  const rendBonus = rend != null && maxRend > 0 ? (rend / maxRend) * 40 : 0;
  return Math.max(0, Math.round(100 - riskPenalty + rendBonus - 40));
}

// ─── Component ────────────────────────────────────────────────────────────────

interface Props {
  municipioParam: string;
  anioParam: number;
}

export default function ComparadorCultivos({ municipioParam, anioParam }: Props) {
  const [municipios, setMunicipios] = useState<
    { codigo_dane: string; municipio: string; departamento: string }[]
  >([]);
  const [municipio, setMunicipio] = useState(municipioParam);
  const [anio, setAnio] = useState(anioParam);
  const [data, setData] = useState<CultivoComparacion[]>([]);
  const [loading, setLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [municipioNombre, setMunicipioNombre] = useState("");
  const [municipioDept, setMunicipioDept] = useState("");

  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

  // Load municipios catalog
  useEffect(() => {
    if (!base) return;
    fetch(`${base}/municipios`)
      .then((r) => r.json())
      .then((list) => {
        setMunicipios(list);
        if (!municipio && list.length > 0) setMunicipio(list[0].codigo_dane);
      })
      .catch(() => {});
  }, [base]);

  // Sync municipio name
  useEffect(() => {
    const found = municipios.find((m) => m.codigo_dane === municipio);
    if (found) {
      setMunicipioNombre(found.municipio);
      setMunicipioDept(found.departamento);
    }
  }, [municipio, municipios]);

  // Fetch comparisons
  async function fetchComparacion(cod: string, yr: number) {
    if (!cod) return;
    setLoading(true);
    setGlobalError(null);
    setData([]);

    try {
      const results = await Promise.all(
        CULTIVOS_MVP.map(async (cultivo) => {
          try {
            const r = await fetch(`${base}/predecir`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ municipio: cod, cultivo, año: yr }),
            });

            if (r.status === 404) {
              return {
                cultivo,
                rendimiento_esperado: null,
                prob_riesgo_alto: null,
                etiqueta_riesgo: "Sin datos" as EtiquetaRiesgo,
                score: 0,
                estado: "sin_datos" as const,
                error_msg: "Sin suficiente histórico para proyectar",
              };
            }
            if (!r.ok) {
              const body = await r.json().catch(() => ({}));
              return {
                cultivo,
                rendimiento_esperado: null,
                prob_riesgo_alto: null,
                etiqueta_riesgo: "Sin datos" as EtiquetaRiesgo,
                score: 0,
                estado: "error" as const,
                error_msg: body?.detail ?? "Error al obtener predicción",
              };
            }

            const d = await r.json();
            return {
              cultivo,
              rendimiento_esperado: d.rendimiento_esperado ?? null,
              prob_riesgo_alto: d.prob_riesgo_alto ?? null,
              etiqueta_riesgo: (d.etiqueta_riesgo as EtiquetaRiesgo) ?? "Sin datos",
              score: 0, // calculated below
              estado: "ok" as const,
            };
          } catch {
            return {
              cultivo,
              rendimiento_esperado: null,
              prob_riesgo_alto: null,
              etiqueta_riesgo: "Sin datos" as EtiquetaRiesgo,
              score: 0,
              estado: "error" as const,
              error_msg: "Error conectando con el orquestador. Intenta más tarde.",
            };
          }
        })
      );

      // Calculate scores with relative rendimiento
      const maxRend = Math.max(
        ...results.map((r) => r.rendimiento_esperado ?? 0)
      );
      const withScores = results.map((r) => ({
        ...r,
        score: calcScore(r.prob_riesgo_alto, r.rendimiento_esperado, maxRend),
      }));

      // Sort by score desc
      withScores.sort((a, b) => b.score - a.score);
      setData(withScores);
    } catch {
      setGlobalError("Error conectando con el orquestador. Intenta más tarde.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (municipio) fetchComparacion(municipio, anio);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [municipio, anio]);

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="px-6 py-4 border-b border-border/60 bg-card/70 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-1.5">
              <ArrowLeft className="size-4" />
              Mapa
            </Button>
          </Link>
          <div className="h-5 w-px bg-border" />
          <BarChart3 className="size-5 text-primary shrink-0" />
          <div>
            <h1 className="text-base font-bold leading-tight">Comparador de cultivos</h1>
            {municipioNombre && (
              <p className="text-xs text-muted-foreground leading-none">
                {municipioNombre}
                {municipioDept && ` · ${municipioDept}`} · {anio}
              </p>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        {/* Controls */}
        <MunicipioSelector
          municipios={municipios}
          municipio={municipio}
          anio={anio}
          aniosDisponibles={ANIOS_DISPONIBLES}
          onMunicipioChange={setMunicipio}
          onAnioChange={setAnio}
        />

        {/* Global error */}
        {globalError && (
          <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            <AlertTriangle className="size-4 shrink-0" />
            <span>{globalError}</span>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground animate-pulse">
              <Spinner className="size-4" />
              Consultando predicciones para los 3 cultivos…
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-40 rounded-xl bg-muted animate-pulse" />
              ))}
            </div>
            <div className="h-48 rounded-xl bg-muted animate-pulse" />
          </div>
        )}

        {/* Results */}
        {!loading && data.length > 0 && (
          <>
            {/* Ranking cards */}
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                Ranking de recomendación
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {data.map((item, idx) => (
                  <RankingCard
                    key={item.cultivo}
                    rank={idx + 1}
                    item={item}
                    municipio={municipio}
                    anio={anio}
                  />
                ))}
              </div>
            </div>

            {/* Comparison table */}
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                Detalle comparativo
              </h2>
              <ComparisonTable data={data} />
            </div>

            {/* Retry */}
            <div className="flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground"
                onClick={() => fetchComparacion(municipio, anio)}
              >
                <RefreshCw className="size-3.5 mr-1.5" />
                Actualizar
              </Button>
            </div>
          </>
        )}

        {/* Empty state */}
        {!loading && !globalError && data.length === 0 && municipio && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
            <AlertTriangle className="size-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Selecciona un municipio para ver la comparación.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
