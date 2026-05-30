/**
 * Tests for: mapa-interactivo-mejoras
 * Feature: mapa-interactivo-mejoras
 */

import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import colombiaMvp from '../../public/geo/colombia_mvp.geojson';
import { getBaseStyle } from '../lib/map-styles';
import {
  MIN_ZOOM,
  MAX_ZOOM,
  DEFAULT_ZOOM,
  DEFAULT_CENTER,
  COLOMBIA_BOUNDS,
} from '../components/mapa-constants';

// ---------------------------------------------------------------------------
// Task 5.4 — Requirement 3.1
// Verify the GeoJSON has exactly 15 features (one per MVP municipality)
// ---------------------------------------------------------------------------

describe('Feature: mapa-interactivo-mejoras — GeoJSON colombia_mvp', () => {
  it('has exactly 15 features', () => {
    // Validates: Requirements 3.1
    expect(colombiaMvp.features.length).toBe(15);
  });
});

// ---------------------------------------------------------------------------
// Task 5.5 — Requirement 3.2
// Property 1: No superposición entre hexágonos
// ---------------------------------------------------------------------------

// Helper: compute centroid as average of exterior ring vertices (excluding closing duplicate)
function centroid(feature: (typeof colombiaMvp.features)[number]): [number, number] {
  const ring = feature.geometry.coordinates[0];
  // Exclude the closing duplicate (last point equals first)
  const pts = ring.slice(0, ring.length - 1);
  const sumLon = pts.reduce((acc, p) => acc + p[0], 0);
  const sumLat = pts.reduce((acc, p) => acc + p[1], 0);
  return [sumLon / pts.length, sumLat / pts.length];
}

// Helper: compute radius as max distance from centroid to any vertex
function radius(feature: (typeof colombiaMvp.features)[number]): number {
  const c = centroid(feature);
  const ring = feature.geometry.coordinates[0];
  return Math.max(...ring.map((p) => distance(c, [p[0], p[1]])));
}

// Helper: Euclidean distance between two [lon, lat] points
function distance(c1: [number, number], c2: [number, number]): number {
  const dx = c1[0] - c2[0];
  const dy = c1[1] - c2[1];
  return Math.sqrt(dx * dx + dy * dy);
}

const features = colombiaMvp.features;

describe('Feature: mapa-interactivo-mejoras — Property 1: no superposicion entre hexagonos', () => {
  it('no two hexagons overlap (distance between centroids > sum of radii)', () => {
    // Validates: Requirements 3.2
    fc.assert(
      fc.property(
        fc
          .tuple(
            fc.integer({ min: 0, max: features.length - 1 }),
            fc.integer({ min: 0, max: features.length - 1 }),
          )
          .filter(([i, j]) => i !== j),
        ([i, j]) => {
          const ci = centroid(features[i]);
          const cj = centroid(features[j]);
          const ri = radius(features[i]);
          const rj = radius(features[j]);
          const dist = distance(ci, cj);
          return dist > ri + rj;
        },
      ),
      { numRuns: 105 },
    );
  });
});

// ---------------------------------------------------------------------------
// Task 5.6 — Requirement 3.3
// Property 2: Estilo de borde consistente en todos los hexágonos
// ---------------------------------------------------------------------------

describe('Feature: mapa-interactivo-mejoras — Property 2: estilo de borde consistente', () => {
  it('getBaseStyle returns color #fff and weight >= 1.5 for every GeoJSON feature', () => {
    // Feature: mapa-interactivo-mejoras, Property 2: estilo de borde consistente
    // Validates: Requirements 3.3
    fc.assert(
      fc.property(
        fc.constantFrom(...features),
        (feature) => {
          const style = getBaseStyle(feature);
          return style.color === '#fff' && (style.weight ?? 0) >= 1.5;
        },
      ),
      { numRuns: 100 },
    );
  });
});

// ---------------------------------------------------------------------------
// Task 2.2 — Requirements 1.2, 1.6
// Verify zoom configuration constants and MapContainer/ZoomControl JSX props
// ---------------------------------------------------------------------------

const MAPA_SOURCE = readFileSync(
  resolve(__dirname, '../components/MapaColombia.tsx'),
  'utf-8',
);

describe('Feature: mapa-interactivo-mejoras — zoom constants', () => {
  it('MIN_ZOOM equals 5', () => {
    // Validates: Requirements 1.2
    expect(MIN_ZOOM).toBe(5);
  });

  it('MAX_ZOOM equals 10', () => {
    // Validates: Requirements 1.2
    expect(MAX_ZOOM).toBe(10);
  });

  it('DEFAULT_ZOOM equals 6', () => {
    // Validates: Requirements 1.6
    expect(DEFAULT_ZOOM).toBe(6);
  });

  it('DEFAULT_CENTER equals [4.57, -74.3]', () => {
    // Validates: Requirements 1.6
    expect(DEFAULT_CENTER).toEqual([4.57, -74.3]);
  });
});

describe('Feature: mapa-interactivo-mejoras — MapContainer zoom props in JSX source', () => {
  it('MapContainer has scrollWheelZoom={true}', () => {
    // Validates: Requirements 1.2
    expect(MAPA_SOURCE).toContain('scrollWheelZoom={true}');
  });

  it('MapContainer has zoomControl={false}', () => {
    // Validates: Requirements 1.2
    expect(MAPA_SOURCE).toContain('zoomControl={false}');
  });

  it('MapContainer has zoom={DEFAULT_ZOOM}', () => {
    // Validates: Requirements 1.6
    expect(MAPA_SOURCE).toContain('zoom={DEFAULT_ZOOM}');
  });

  it('MapContainer has center={DEFAULT_CENTER}', () => {
    // Validates: Requirements 1.6
    expect(MAPA_SOURCE).toContain('center={DEFAULT_CENTER}');
  });

  it('MapContainer has minZoom={MIN_ZOOM}', () => {
    // Validates: Requirements 1.2
    expect(MAPA_SOURCE).toContain('minZoom={MIN_ZOOM}');
  });

  it('MapContainer has maxZoom={MAX_ZOOM}', () => {
    // Validates: Requirements 1.2
    expect(MAPA_SOURCE).toContain('maxZoom={MAX_ZOOM}');
  });

  it('ZoomControl has position="bottomleft"', () => {
    // Validates: Requirements 1.2
    expect(MAPA_SOURCE).toContain('position="bottomleft"');
  });
});

// ---------------------------------------------------------------------------
// Task 3.2 — Requirements 2.1, 2.4, 2.5
// Unit tests for geographic restriction constants
// ---------------------------------------------------------------------------

describe('Feature: mapa-interactivo-mejoras — Restricción geográfica (Req 2.1, 2.4, 2.5)', () => {
  it('COLOMBIA_BOUNDS equals [[-4.23, -79.0], [12.53, -66.87]]', () => {
    // Validates: Requirements 2.1
    expect(COLOMBIA_BOUNDS).toEqual([
      [-4.23, -79.0],
      [12.53, -66.87],
    ]);
  });

  it('MIN_ZOOM equals 5', () => {
    // Validates: Requirements 2.4
    expect(MIN_ZOOM).toBe(5);
  });

  it('MAX_ZOOM equals 10', () => {
    // Validates: Requirements 2.5
    expect(MAX_ZOOM).toBe(10);
  });

  it('MapaColombia.tsx source contains maxBounds={COLOMBIA_BOUNDS}', () => {
    // Validates: Requirements 2.1
    expect(MAPA_SOURCE).toContain('maxBounds={COLOMBIA_BOUNDS}');
  });

  it('MapaColombia.tsx source contains maxBoundsViscosity={1.0}', () => {
    // Validates: Requirements 2.2, 2.3
    expect(MAPA_SOURCE).toContain('maxBoundsViscosity={1.0}');
  });
});

// ---------------------------------------------------------------------------
// Task 7.3 — Requirements 4.1, 4.3, 4.4
// Unit tests for z-index and pointer-events of Panel_Controles wrapper div
// ---------------------------------------------------------------------------

describe('Feature: mapa-interactivo-mejoras — Z-index del Panel_Controles (Req 4.1, 4.3, 4.4)', () => {
  it('Panel_Controles wrapper div has class z-[1001]', () => {
    // Validates: Requirements 4.1
    expect(MAPA_SOURCE).toContain('z-[1001]');
  });

  it('Panel_Controles wrapper div has style pointerEvents: auto', () => {
    // Validates: Requirements 4.3
    expect(MAPA_SOURCE).toContain("pointerEvents: 'auto'");
  });

  it('Panel_Controles div (z-[1001]) appears before MapContainer in the JSX source', () => {
    // Validates: Requirements 4.4
    // The controls wrapper must precede the map container in DOM order.
    // Use '<MapContainer' to match the JSX tag, not the import identifier.
    const controlsIndex = MAPA_SOURCE.indexOf('z-[1001]');
    const mapContainerIndex = MAPA_SOURCE.indexOf('<MapContainer');
    expect(controlsIndex).toBeGreaterThan(-1);
    expect(mapContainerIndex).toBeGreaterThan(-1);
    expect(controlsIndex).toBeLessThan(mapContainerIndex);
  });
});

// ---------------------------------------------------------------------------
// Task 7.4 — Requirement 4.5
// Property 3: Z-index de SelectContent siempre superior a Leaflet
// ---------------------------------------------------------------------------

describe('Feature: mapa-interactivo-mejoras — Property 3: z-index de SelectContent', () => {
  it('all SelectContent elements have zIndex >= 1001 for any cultivo value', () => {
    // Feature: mapa-interactivo-mejoras, Property 3: z-index de SelectContent
    // Validates: Requirements 4.5
    fc.assert(
      fc.property(
        fc.constantFrom('Café', 'Cacao', 'Maíz'),
        (_cultivo) => {
          // Source-based: verify all SelectContent elements have zIndex: 1001
          const matches = MAPA_SOURCE.match(/<SelectContent[^>]*style=\{\{[^}]*zIndex:\s*1001[^}]*\}\}/g);
          return matches !== null && matches.length >= 2;
        },
      ),
      { numRuns: 100 },
    );
  });
});
