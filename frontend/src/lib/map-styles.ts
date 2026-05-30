/**
 * Pure style helpers for MapaColombia — no React/Leaflet runtime dependencies.
 * Exported here so they can be imported in Vitest (node environment) without
 * pulling in react-leaflet or next/navigation.
 */

// ─── Types ────────────────────────────────────────────────────────────────────

export type EtiquetaRiesgo = "Bajo" | "Medio" | "Alto" | "Sin datos";

export interface GeoFeature {
  type: string;
  properties: {
    codigo_dane: string;
    municipio: string;
    [key: string]: unknown;
  };
  geometry: unknown;
}

export interface PathOptions {
  color: string;
  weight: number;
  fillColor: string;
  fillOpacity: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

export const ETIQUETA_FILL: Record<EtiquetaRiesgo, string> = {
  Bajo: "#16a34a",
  Medio: "#f59e0b",
  Alto: "#dc2626",
  "Sin datos": "#9ca3af",
};

// ─── Pure exported helper ─────────────────────────────────────────────────────

/**
 * Returns the base Leaflet PathOptions for a GeoFeature using only the
 * ETIQUETA_FILL map and no component state.
 *
 * Validates: Requirements 3.3
 */
export function getBaseStyle(_feature?: GeoFeature): PathOptions {
  // When called without component state, default to "Sin datos"
  const etiqueta: EtiquetaRiesgo = "Sin datos";
  const fill = ETIQUETA_FILL[etiqueta];
  return {
    color: "#fff",
    weight: 1.5,
    fillColor: fill,
    fillOpacity: 0.65,
  };
}
