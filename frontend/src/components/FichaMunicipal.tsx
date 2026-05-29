"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, AlertTriangle, RefreshCw, Info, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import MunicipioHeader from "@/components/ficha/MunicipioHeader";
import RiesgoSemaforo from "@/components/ficha/RiesgoSemaforo";
import RendimientoHistoricoChart from "@/components/ficha/RendimientoHistoricoChart";
import ShapBars from "@/components/ficha/ShapBars";
import RecomendacionCard from "@/components/ficha/RecomendacionCard";

// ─── Types ────────────────────────────────────────────────────────────────────

export type EtiquetaRiesgo = "Bajo" | "Medio" | "Alto" | "Sin datos";

export interface SeriePunto {
  año: number;
  rendimiento: number | null;
  rendimiento_prom3a: number | null;
}

export interface ShapItem {
  label: string;
  value: number | null;
  direction: string | null;
}

export interface FichaMunicipalState {
  codigo_dane: string;
  municipio: string;
  departamento: string;
  cultivo: string;
  anio_objetivo: number;
  prediccion?: {
    rendimiento_esperado: number | null;
    prob_riesgo_alto: number | null;
    etiqueta_riesgo: EtiquetaRiesgo;
  };
  serie?: SeriePunto[];
  shap_items?: ShapItem[];
  recomendacion?: string | null;
  estado: "cargando" | "ok" | "sin_datos" | "error";
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function parseSecciones(texto: string): Record<string, string> {
  const result: Record<string, string> = {};
  const parts = texto.split(/=== (.+?) ===/);
  for (let i = 1; i < parts.length; i += 2) {
    result[parts[i].trim()] = (parts[i + 1] ?? "").trim();
  }
  return result;
}

function parseShapItems(riesgoBloque: string): ShapItem[] {
  const lines = riesgoBloque.split("\n");
  const items: ShapItem[] = [];
  let inShap = false;

  for (const line of lines) {
    if (line.includes("Factores determinantes")) { inShap = true; continue; }
    if (inShap && line.trim().startsWith("-")) {
      const raw = line.replace(/^[\s-]+/, "");
      const colonIdx = raw.indexOf(":");
      const label = colonIdx >= 0 ? raw.slice(0, colonIdx).trim() : raw.trim();
      const rest = colonIdx >= 0 ? raw.slice(colonIdx + 1).trim() : "";
      const numMatch = rest.match(/[-\d.]+/);
      const dirMatch = rest.match(/\(([^)]+)\)/);
      items.push({
        label,
        value: numMatch ? parseFloat(numMatch[0]) : null,
        direction: dirMatch ? dirMatch[1] : null,
      });
    } else if (inShap && line.trim() === "") {
      break;
    }
  }

  // Fallback: parse inline factor mentions from the Análisis paragraph
  // e.g. "Promedio 3 años (valor: N/A)" or "Aptitud media (valor: 0.02)"
  if (items.length === 0) {
    const factorRegex = /([^:,]+?)\s*\(valor:\s*([\d.]+|N\/A)\)/g;
    let m: RegExpExecArray | null;
    while ((m = factorRegex.exec(riesgoBloque)) !== null) {
      const label = m[1].trim().replace(/^(son:|son|son:)\s*/i, "").trim();
      const valStr = m[2];
      items.push({
        label,
        value: valStr === "N/A" ? null : parseFloat(valStr),
        direction: null,
      });
    }
  }

  return items;
}

function parseRecomendacion(recomBloque: string): string {
  return recomBloque
    .split("\n")
    .filter((l) => l.trim() && !l.startsWith("==="))
    .join(" ")
    .trim();
}

// ─── Component ────────────────────────────────────────────────────────────────

interface Props {
  codigo_dane: string;
  cultivo: string;
  anioParam?: number;
}

export default function FichaMunicipal({ codigo_dane, cultivo, anioParam }: Props) {
  const [state, setState] = useState<FichaMunicipalState>({
    codigo_dane,
    municipio: codigo_dane,
    departamento: "",
    cultivo,
    anio_objetivo: anioParam ?? 2025,
    estado: "cargando",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

  // Validate codigo_dane
  if (!/^\d{5}$/.test(codigo_dane)) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <AlertTriangle className="size-10 text-destructive mx-auto mb-3" />
        <p className="font-semibold text-destructive">Código DANE inválido: {codigo_dane}</p>
        <Link href="/" className="mt-4 inline-block text-sm text-primary underline">
          ← Volver al mapa
        </Link>
      </div>
    );
  }

  async function load() {
    setState((s) => ({ ...s, estado: "cargando" }));
    setErrors({});
    const newErrors: Record<string, string> = {};

    // 1. Rendimiento histórico
    let serie: SeriePunto[] = [];
    let anioMax = 2024;
    let municipioNombre = codigo_dane;
    let departamento = "";
    let cultivoNorm = cultivo;

    try {
      const r = await fetch(`${base}/rendimiento/${codigo_dane}/${encodeURIComponent(cultivo)}`);
      if (r.ok) {
        const d = await r.json();
        municipioNombre = d.municipio ?? codigo_dane;
        departamento = d.departamento ?? "";
        cultivoNorm = d.cultivo ?? cultivo;
        anioMax = d.año_max ?? 2024;
        serie = (d.serie ?? []).map((p: any) => ({
          año: p.año,
          rendimiento: p.rendimiento ?? null,
          rendimiento_prom3a: p.rendimiento_prom3a ?? null,
        }));
      } else {
        newErrors.rendimiento = "Sin histórico disponible";
      }
    } catch {
      newErrors.rendimiento = "Error cargando histórico";
    }

    // 2. Resolve anio_objetivo
    const anioObjetivo = anioParam && anioParam > anioMax ? anioParam : anioMax + 1;

    // 3. Predicción
    let prediccion: FichaMunicipalState["prediccion"] | undefined;
    try {
      const r = await fetch(`${base}/predecir`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ municipio: codigo_dane, cultivo: cultivoNorm, año: anioObjetivo }),
      });
      if (r.ok) {
        const d = await r.json();
        municipioNombre = d.municipio ?? municipioNombre;
        departamento = d.departamento ?? departamento;
        prediccion = {
          rendimiento_esperado: d.rendimiento_esperado ?? null,
          prob_riesgo_alto: d.prob_riesgo_alto ?? null,
          etiqueta_riesgo: (d.etiqueta_riesgo as EtiquetaRiesgo) ?? "Sin datos",
        };
      } else if (r.status === 422) {
        const body = await r.json().catch(() => ({}));
        newErrors.prediccion = body?.detail ?? "Año no válido para predicción";
      } else if (r.status === 404) {
        newErrors.prediccion = "Sin datos de predicción para este municipio/cultivo";
      } else {
        newErrors.prediccion = "Error al obtener predicción";
      }
    } catch {
      newErrors.prediccion = "Error de conexión al obtener predicción";
    }

    // 4. Reporte (SHAP + recomendación)
    let shapItems: ShapItem[] = [];
    let recomendacion: string | null = null;
    try {
      const r = await fetch(
        `${base}/reporte/${codigo_dane}/${encodeURIComponent(cultivoNorm)}?formato=texto`
      );
      if (r.ok) {
        const d = await r.json();
        const secciones = parseSecciones(d.contenido_texto ?? "");
        shapItems = parseShapItems(secciones["Riesgo"] ?? "");
        recomendacion = parseRecomendacion(secciones["Recomendación"] ?? "");
      } else {
        newErrors.reporte = "Sin narrativa SHAP disponible";
      }
    } catch {
      newErrors.reporte = "Error cargando reporte";
    }

    setErrors(newErrors);
    setState({
      codigo_dane,
      municipio: municipioNombre,
      departamento,
      cultivo: cultivoNorm,
      anio_objetivo: anioObjetivo,
      prediccion,
      serie: serie.length > 0 ? serie : undefined,
      shap_items: shapItems.length > 0 ? shapItems : undefined,
      recomendacion,
      estado: prediccion || serie.length > 0 ? "ok" : "sin_datos",
    });
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [codigo_dane, cultivo, anioParam]);

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="px-6 py-4 border-b border-border/60 bg-card/70 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-1.5">
              <ArrowLeft className="size-4" />
              Mapa
            </Button>
          </Link>
          <div className="h-5 w-px bg-border" />
          {state.estado === "cargando" ? (
            <div className="flex items-center gap-2 text-muted-foreground text-sm">
              <Spinner className="size-4" />
              Cargando ficha…
            </div>
          ) : (
            <MunicipioHeader
              municipio={state.municipio}
              departamento={state.departamento}
              cultivo={state.cultivo}
              anio={state.anio_objetivo}
            />
          )}
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Loading skeleton */}
        {state.estado === "cargando" && (
          <div className="space-y-4 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 rounded-xl bg-muted" />
            ))}
          </div>
        )}

        {/* Error parcial banners */}
        {state.estado !== "cargando" &&
          Object.entries(errors).map(([key, msg]) => (
            <div
              key={key}
              className="flex items-center gap-2 rounded-lg border border-amber-400/40 bg-amber-50 dark:bg-amber-950/30 px-4 py-3 text-sm text-amber-700 dark:text-amber-400"
            >
              <Info className="size-4 shrink-0" />
              <span>{msg}</span>
            </div>
          ))}

        {/* Sin datos total */}
        {state.estado === "sin_datos" && (
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <AlertTriangle className="size-10 text-muted-foreground" />
            <p className="font-semibold">Sin datos para {state.municipio} / {state.cultivo}</p>
            <Button variant="outline" size="sm" onClick={load}>
              <RefreshCw className="size-4 mr-2" />
              Reintentar
            </Button>
          </div>
        )}

        {/* Content */}
        {state.estado === "ok" && (
          <>
            {/* Predicción semáforo */}
            {state.prediccion && (
              <RiesgoSemaforo
                etiqueta={state.prediccion.etiqueta_riesgo}
                rendimiento={state.prediccion.rendimiento_esperado}
                probRiesgoAlto={state.prediccion.prob_riesgo_alto}
                anio={state.anio_objetivo}
                cultivo={state.cultivo}
              />
            )}

            {/* Gráfica histórica */}
            <RendimientoHistoricoChart
              serie={state.serie ?? []}
              cultivo={state.cultivo}
              municipio={state.municipio}
            />

            {/* SHAP */}
            {state.shap_items && state.shap_items.length > 0 && (
              <ShapBars items={state.shap_items} />
            )}

            {/* Recomendación */}
            {state.recomendacion && (
              <RecomendacionCard
                texto={state.recomendacion}
                etiqueta={state.prediccion?.etiqueta_riesgo ?? "Sin datos"}
              />
            )}

            {/* Retry button */}
            <div className="flex justify-end gap-2 pt-2">
              <Link href={`/asistente?municipio=${state.codigo_dane}&cultivo=${encodeURIComponent(state.cultivo)}`}>
                <Button variant="outline" size="sm" className="gap-1.5 text-muted-foreground">
                  <MessageSquare className="size-3.5" />
                  Consultar asistente
                </Button>
              </Link>
              <Button variant="ghost" size="sm" onClick={load} className="text-muted-foreground">
                <RefreshCw className="size-3.5 mr-1.5" />
                Actualizar
              </Button>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
