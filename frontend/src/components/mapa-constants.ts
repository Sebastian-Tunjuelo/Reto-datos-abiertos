/**
 * Zoom and bounds constants for MapaColombia.
 * Extracted to a separate file so they can be imported in Node-environment tests
 * without pulling in react-leaflet or next/navigation.
 */

export const MIN_ZOOM = 5;
export const MAX_ZOOM = 10;
export const DEFAULT_ZOOM = 6;
export const DEFAULT_CENTER: [number, number] = [4.57, -74.3];

export const COLOMBIA_BOUNDS: [[number, number], [number, number]] = [
  [-4.23, -79.0],   // suroeste
  [12.53, -66.87],  // noreste
];
