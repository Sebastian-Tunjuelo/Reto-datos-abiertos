/**
 * Geographic and zoom constants for the Colombia interactive map.
 * Extracted to a plain .ts file so they can be imported in tests
 * without triggering JSX parsing (vitest uses environment: 'node').
 */

export const COLOMBIA_BOUNDS: [[number, number], [number, number]] = [
  [-4.23, -79.0], // suroeste
  [12.53, -66.87], // noreste
];

export const MIN_ZOOM = 5;
export const MAX_ZOOM = 10;
export const DEFAULT_ZOOM = 6;
export const DEFAULT_CENTER: [number, number] = [4.57, -74.3];
