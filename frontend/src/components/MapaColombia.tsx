"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import type { Layer, PathOptions } from "leaflet";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ─── Types ────────────────────────────────────────────────────────────────────

type EtiquetaRiesgo = "Bajo" | "Medio" | "Alto" | "Sin datos";
type EstadoMunicipio = "ok" | "sin_datos" | "error" | "cargando";

interface MapaMunicipio {
  codigo_dane: string;
  municipio: string;
  departamento: string;
  cultivo: string;
  anio: number;
  rendimiento_esperado: number | null;
  prob_riesgo_alto: number | null;
  etiqueta_riesgo: EtiquetaRiesgo;
  estado: EstadoMunicipio;
}

interface MunicipioInfo {
  codigo_dane: string;
  municipio: string;
  departamento: string;
}

interface GeoFeature {
  type: string;
  properties: {
    codigo_dane: string;
    municipio: string;
    [key: string]: unknown;
  };
  geometry: unknown;
}

interface GeoData {
  type: string;
  features: GeoFeature[];
}

// ─── Constants ────────────────────────────────────────────────────────────────

const ETIQUETA_COLOR: Record<EtiquetaRiesgo, string> = {
  Bajo: "var(--riesgo-bajo)",
  Medio: "var(--riesgo-medio)",
  Alto: "var(--riesgo-alto)",
  "Sin datos": "var(--riesgo-sin-datos)",
};

const ETIQUETA_FILL: Record<EtiquetaRiesgo, string> = {
  Bajo: "#16a34a",
  Medio: "#f59e0b",
  Alto: "#dc2626",
  "Sin datos": "#9ca3af",
};

const ANIOS_DISPONIBLES = [2025, 2026, 2027];
const BATCH_SIZE = 4;
const CACHE_KEY = "siembrasegura_map_cache_v2";

// ─── Cache helpers ────────────────────────────────────────────────────────────

function loadCache(): Record<string, MapaMunicipio> {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveCache(cache: Record<string, MapaMunicipio>) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
  } catch {
    // storage full or unavailable — ignore
  }
}

function cacheKey(codigo: string, cultivo: string, anio: number) {
  return `${codigo}__${cultivo}__${anio}`;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function MapaColombia() {
  const [geo, setGeo] = useState<GeoData | null>(null);
  const [geoError, setGeoError] = useState(false);

  const [cultivos, setCultivos] = useState<string[]>([]);
  const [cultivo, setCultivo] = useState<string>("");
  const [anio, setAnio] = useState<number>(2025);

  const [results, setResults] = useState<Record<string, MapaMunicipio>>({});
  const [loading, setLoading] = useState(false);
  const [partialError, setPartialError] = useState(false);
  const [anioError, setAnioError] = useState<string | null>(null);

  // Track the "generation" of the current fetch so stale responses are ignored
  const fetchGenRef = useRef(0);

  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
  const router = useRouter();

  // ── Load GeoJSON ────────────────────────────────────────────────────────────
  useEffect(() => {
    fetch("/geo/colombia_mvp.geojson")
      .then((r) => {
        if (!r.ok) throw new Error("GeoJSON fetch failed");
        return r.json();
      })
      .then((j: GeoData) => setGeo(j))
      .catch(() => setGeoError(true));
  }, []);

  // ── Load cultivos from API (no hardcode) ────────────────────────────────────
  useEffect(() => {
    if (!geo || !base) {
      // Fallback when no backend configured
      setCultivos(["Café", "Cacao", "Maíz"]);
      setCultivo("Café");
      return;
    }
    const firstCode = geo.features[0]?.properties?.codigo_dane;
    if (!firstCode) return;

    fetch(`${base}/cultivos/${firstCode}`)
      .then((r) => r.json())
      .then((data: { cultivos?: string[] }) => {
        const list = data.cultivos ?? ["Café", "Cacao", "Maíz"];
        setCultivos(list);
        setCultivo(list[0]);
      })
      .catch(() => {
        setCultivos(["Café", "Cacao", "Maíz"]);
        setCultivo("Café");
      });
  }, [geo, base]);

  // ── Fetch predictions ───────────────────────────────────────────────────────
  const fetchPredictions = useCallback(
    async (targetCultivo: string, targetAnio: number) => {
      if (!geo || !targetCultivo) return;

      const codes = geo.features
        .map((f) => f.properties?.codigo_dane)
        .filter(Boolean);
      if (codes.length === 0) return;

      const gen = ++fetchGenRef.current;

      const cache = loadCache();
      const toFetch = codes.filter(
        (c) => !cache[cacheKey(c, targetCultivo, targetAnio)],
      );

      if (toFetch.length === 0) {
        setResults({ ...cache });
        return;
      }

      if (!base) {
        // No backend — mark all as sin_datos
        const copy = { ...cache };
        for (const c of toFetch) {
          copy[cacheKey(c, targetCultivo, targetAnio)] = {
            codigo_dane: c,
            municipio: c,
            departamento: "",
            cultivo: targetCultivo,
            anio: targetAnio,
            rendimiento_esperado: null,
            prob_riesgo_alto: null,
            etiqueta_riesgo: "Sin datos",
            estado: "sin_datos",
          };
        }
        saveCache(copy);
        setResults(copy);
        return;
      }

      setLoading(true);
      setPartialError(false);
      setAnioError(null);

      const copy = { ...cache };
      let hasPartialError = false;

      for (let i = 0; i < toFetch.length; i += BATCH_SIZE) {
        if (fetchGenRef.current !== gen) break; // stale — abort

        const chunk = toFetch.slice(i, i + BATCH_SIZE);
        const rows = await Promise.all(
          chunk.map(async (codigo) => {
            try {
              const r = await fetch(`${base}/predecir`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  municipio: codigo,
                  cultivo: targetCultivo,
                  año: targetAnio,
                }),
              });

              if (r.status === 404) {
                return {
                  codigo_dane: codigo,
                  municipio: codigo,
                  departamento: "",
                  cultivo: targetCultivo,
                  anio: targetAnio,
                  rendimiento_esperado: null,
                  prob_riesgo_alto: null,
                  etiqueta_riesgo: "Sin datos" as EtiquetaRiesgo,
                  estado: "sin_datos" as EstadoMunicipio,
                };
              }

              if (r.status === 422) {
                const body = await r.json().catch(() => ({}));
                setAnioError(
                  body?.detail ?? `Año ${targetAnio} no válido para ${codigo}`,
                );
                return {
                  codigo_dane: codigo,
                  municipio: codigo,
                  departamento: "",
                  cultivo: targetCultivo,
                  anio: targetAnio,
                  rendimiento_esperado: null,
                  prob_riesgo_alto: null,
                  etiqueta_riesgo: "Sin datos" as EtiquetaRiesgo,
                  estado: "error" as EstadoMunicipio,
                };
              }

              if (!r.ok) {
                hasPartialError = true;
                return {
                  codigo_dane: codigo,
                  municipio: codigo,
                  departamento: "",
                  cultivo: targetCultivo,
                  anio: targetAnio,
                  rendimiento_esperado: null,
                  prob_riesgo_alto: null,
                  etiqueta_riesgo: "Sin datos" as EtiquetaRiesgo,
                  estado: "error" as EstadoMunicipio,
                };
              }

              const j = await r.json();
              return {
                codigo_dane: j.codigo_dane ?? codigo,
                municipio: j.municipio ?? codigo,
                departamento: j.departamento ?? "",
                cultivo: targetCultivo,
                anio: targetAnio,
                rendimiento_esperado: j.rendimiento_esperado ?? null,
                prob_riesgo_alto: j.prob_riesgo_alto ?? null,
                etiqueta_riesgo: (j.etiqueta_riesgo as EtiquetaRiesgo) ?? "Sin datos",
                estado: "ok" as EstadoMunicipio,
              };
            } catch {
              hasPartialError = true;
              return {
                codigo_dane: codigo,
                municipio: codigo,
                departamento: "",
                cultivo: targetCultivo,
                anio: targetAnio,
                rendimiento_esperado: null,
                prob_riesgo_alto: null,
                etiqueta_riesgo: "Sin datos" as EtiquetaRiesgo,
                estado: "error" as EstadoMunicipio,
              };
            }
          }),
        );

        if (fetchGenRef.current !== gen) break;

        for (const row of rows) {
          copy[cacheKey(row.codigo_dane, targetCultivo, targetAnio)] = row;
        }
        setResults({ ...copy });
        saveCache(copy);
      }

      if (fetchGenRef.current === gen) {
        setPartialError(hasPartialError);
        setLoading(false);
      }
    },
    [geo, base],
  );

  // Trigger fetch when cultivo or anio changes
  useEffect(() => {
    if (cultivo) fetchPredictions(cultivo, anio);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cultivo, anio, geo]);

  // ── Helpers ─────────────────────────────────────────────────────────────────

  const getResult = (codigo: string) =>
    results[cacheKey(codigo, cultivo, anio)];

  const styleFeature = (feature?: GeoFeature): PathOptions => {
    const codigo = feature?.properties?.codigo_dane ?? "";
    const res = getResult(codigo);
    const etiqueta: EtiquetaRiesgo = res?.etiqueta_riesgo ?? "Sin datos";
    const fill = ETIQUETA_FILL[etiqueta];
    return {
      color: "#fff",
      weight: 1.5,
      fillColor: fill,
      fillOpacity: res?.estado === "cargando" ? 0.2 : 0.65,
    };
  };

  const onEachFeature = (feature: GeoFeature, layer: Layer) => {
    const props = feature.properties;
    const codigo = props.codigo_dane;
    const nombre = props.municipio ?? codigo;

    const bindTooltip = () => {
      const res = getResult(codigo);
      const etiqueta = res?.etiqueta_riesgo ?? "Sin datos";
      const rend =
        res?.rendimiento_esperado != null
          ? `${res.rendimiento_esperado.toFixed(2)} t/ha`
          : "—";
      const prob =
        res?.prob_riesgo_alto != null
          ? `${(res.prob_riesgo_alto * 100).toFixed(0)}%`
          : "—";

      const colorDot = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${ETIQUETA_FILL[etiqueta]};margin-right:5px;vertical-align:middle;"></span>`;

      (layer as any).bindTooltip(
        `<div style="font-family:Nunito,sans-serif;min-width:160px;">
          <strong style="font-size:13px;">${nombre}</strong>
          <div style="font-size:11px;color:#666;margin-bottom:4px;">${res?.departamento ?? ""}</div>
          <div style="font-size:12px;">${colorDot}<strong>${etiqueta}</strong></div>
          <div style="font-size:11px;margin-top:4px;">Rendimiento: <strong>${rend}</strong></div>
          <div style="font-size:11px;">Prob. riesgo alto: <strong>${prob}</strong></div>
          <div style="font-size:10px;color:#9ca3af;margin-top:4px;">Clic para ver ficha →</div>
        </div>`,
        { sticky: true, opacity: 0.97 },
      );
    };

    bindTooltip();

    (layer as any).on("mouseover", function (this: any) {
      this.setStyle({ weight: 2.5, fillOpacity: 0.85 });
    });
    (layer as any).on("mouseout", function (this: any) {
      this.setStyle({ weight: 1.5, fillOpacity: 0.65 });
    });
    (layer as any).on("click", () => {
      router.push(`/municipio/${codigo}/${encodeURIComponent(cultivo)}?anio=${anio}`);
    });
    (layer as any).on("click", function () {
      router.push(`/municipio/${codigo}/${encodeURIComponent(cultivo)}`);
    });
  };

  // ── Render ──────────────────────────────────────────────────────────────────

  if (geoError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4 text-center">
        <AlertTriangle className="size-10 text-destructive" />
        <div>
          <p className="font-semibold text-destructive">GeoJSON no disponible</p>
          <p className="text-sm text-muted-foreground mt-1">
            Verifica que{" "}
            <code className="text-xs bg-muted px-1 rounded">
              public/geo/colombia_mvp.geojson
            </code>{" "}
            exista y sea accesible.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
          <RefreshCw className="size-4 mr-2" />
          Reintentar
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-4">
      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Cultivo
          </label>
          <Select
            value={cultivo}
            onValueChange={(v) => {
              setAnioError(null);
              setCultivo(v);
            }}
            disabled={cultivos.length === 0}
          >
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Seleccionar…" />
            </SelectTrigger>
            <SelectContent>
              {cultivos.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Año objetivo
          </label>
          <Select
            value={String(anio)}
            onValueChange={(v) => {
              setAnioError(null);
              setAnio(Number(v));
            }}
          >
            <SelectTrigger className="w-28">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ANIOS_DISPONIBLES.map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground mt-5 animate-pulse">
            <RefreshCw className="size-4 animate-spin" />
            Cargando predicciones…
          </div>
        )}
      </div>

      {/* Error banners */}
      {anioError && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="size-4 mt-0.5 shrink-0" />
          <span>{anioError}</span>
        </div>
      )}

      {partialError && !anioError && (
        <div className="flex items-center justify-between gap-2 rounded-lg border border-amber-400/40 bg-amber-50 dark:bg-amber-950/30 px-4 py-3 text-sm text-amber-700 dark:text-amber-400">
          <div className="flex items-center gap-2">
            <AlertTriangle className="size-4 shrink-0" />
            <span>Algunos municipios no pudieron cargarse.</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="shrink-0 h-7 text-xs"
            onClick={() => {
              // Clear error entries from cache and retry
              const cache = loadCache();
              const cleaned: Record<string, MapaMunicipio> = {};
              for (const [k, v] of Object.entries(cache)) {
                if (v.estado !== "error") cleaned[k] = v;
              }
              saveCache(cleaned);
              setResults(cleaned);
              fetchPredictions(cultivo, anio);
            }}
          >
            <RefreshCw className="size-3 mr-1" />
            Reintentar
          </Button>
        </div>
      )}

      {/* Map */}
      <div className="relative rounded-xl overflow-hidden ring-1 ring-border shadow-sm h-[72vh] min-h-[400px]">
        {/* Legend */}
        <div className="absolute right-3 top-3 z-[400] bg-card/95 dark:bg-card/90 backdrop-blur-sm rounded-lg shadow-md px-3 py-2.5 ring-1 ring-border/60">
          <p className="text-xs font-semibold mb-2 text-foreground/80 uppercase tracking-wide">
            Riesgo
          </p>
          <div className="flex flex-col gap-1.5">
            {(Object.entries(ETIQUETA_COLOR) as [EtiquetaRiesgo, string][]).map(
              ([label, cssVar]) => (
                <div key={label} className="flex items-center gap-2 text-xs">
                  <span
                    className="w-3.5 h-3.5 rounded-sm shrink-0"
                    style={{ background: ETIQUETA_FILL[label] }}
                  />
                  <span className="text-foreground/90">{label}</span>
                </div>
              ),
            )}
          </div>
        </div>

        {geo && (
          <MapContainer
            style={{ height: "100%", width: "100%" }}
            center={[4.57, -74.3]}
            zoom={6}
            scrollWheelZoom={false}
            zoomControl={true}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />
            <GeoJSON
              key={`${cultivo}-${anio}-${Object.keys(results).length}`}
              data={geo as any}
              style={(feature: any) => styleFeature(feature as GeoFeature)}
              onEachFeature={(feature: any, layer: Layer) =>
                onEachFeature(feature as GeoFeature, layer)
              }
            />
          </MapContainer>
        )}

        {!geo && !geoError && (
          <div className="flex h-full items-center justify-center text-muted-foreground text-sm animate-pulse">
            Cargando mapa…
          </div>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        Haz clic en un municipio para ver su ficha detallada.
      </p>

      <p className="text-xs text-muted-foreground text-right">
        {cultivo && anio
          ? `Mostrando riesgo para ${cultivo} · ${anio} · ${geo?.features?.length ?? 0} municipios`
          : ""}
      </p>
    </div>
  );
}
