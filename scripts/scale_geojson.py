#!/usr/bin/env python3
"""Escala geometrías de un GeoJSON (centroid -> vértices) por un factor dado.

Uso:
  python scripts/scale_geojson.py <input_geojson> <output_geojson> [factor]

Ejemplo:
  python scripts/scale_geojson.py frontend/public/geo/colombia_mvp.geojson frontend/public/geo/colombia_mvp.geojson 0.6
"""
import json
import sys
from copy import deepcopy


def centroid_ring(ring):
    # ring: list of [lon, lat], last point may equal first
    pts = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
    sumx = sum(p[0] for p in pts)
    sumy = sum(p[1] for p in pts)
    n = len(pts) or 1
    return [sumx / n, sumy / n]


def scale_point(c, p, factor):
    return [c[0] + factor * (p[0] - c[0]), c[1] + factor * (p[1] - c[1])]


def scale_polygon(coords, factor):
    # coords: [ring0, ring1, ...]
    new_coords = []
    for ring in coords:
        c = centroid_ring(ring)
        new_ring = [scale_point(c, p, factor) for p in ring]
        new_coords.append(new_ring)
    return new_coords


def scale_geometry(geom, factor):
    t = geom.get('type')
    coords = geom.get('coordinates')
    if t == 'Polygon':
        return {'type': 'Polygon', 'coordinates': scale_polygon(coords, factor)}
    if t == 'MultiPolygon':
        new = []
        for poly in coords:
            new.append(scale_polygon(poly, factor))
        return {'type': 'MultiPolygon', 'coordinates': new}
    # passthrough other types
    return geom


def main(argv):
    if len(argv) < 3:
        print('Usage: scale_geojson.py <input> <output> [factor]')
        return 2
    infile = argv[1]
    outfile = argv[2]
    factor = float(argv[3]) if len(argv) > 3 else 0.6

    with open(infile, 'r', encoding='utf-8') as f:
        data = json.load(f)

    out = deepcopy(data)
    features = out.get('features', [])
    for feat in features:
        geom = feat.get('geometry')
        if not geom:
            continue
        feat['geometry'] = scale_geometry(geom, factor)

    # Backup original if output path equals input
    if infile == outfile:
        import shutil
        shutil.copyfile(infile, infile + '.bak')

    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f'Scaled {len(features)} features by factor={factor} and wrote {outfile}')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
