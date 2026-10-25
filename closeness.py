"""Scores how close a listing's zip code is to the favourite zip codes, on a 0-5 scale."""
import json
import math

# (max km from the listing's area centre to the nearest favourite area, score); inside a favourite is 5
THRESHOLDS = [(0.75, 4), (1.5, 3), (2.5, 2), (4.0, 1)]
LAT0 = 52.37  # Amsterdam; good enough for a flat projection at city scale


def _to_km(lon, lat):
    return lon * 111.32 * math.cos(math.radians(LAT0)), lat * 110.57


def _polygons(geometry):
    polys = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
    return [[[_to_km(*point) for point in ring] for ring in poly] for poly in polys]


def _centroid(polygons):
    # area-weighted centroid of the outer rings
    area = cx = cy = 0
    for poly in polygons:
        ring = poly[0]
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            cross = x1 * y2 - x2 * y1
            area += cross
            cx += (x1 + x2) * cross
            cy += (y1 + y2) * cross
    return cx / (3 * area), cy / (3 * area)


def _inside(x, y, polygons):
    def in_ring(ring):
        inside = False
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
        return inside
    return any(in_ring(poly[0]) and not any(in_ring(hole) for hole in poly[1:]) for poly in polygons)


def _distance(x, y, polygons):
    if _inside(x, y, polygons):
        return 0.0
    best = math.inf
    for poly in polygons:
        for ring in poly:
            for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
                dx, dy = x2 - x1, y2 - y1
                t = 0 if dx == dy == 0 else max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
                best = min(best, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
    return best


class Closeness:
    def __init__(self, geojson_path, favourites):
        with open(geojson_path) as f:
            features = json.load(f)['features']
        self.areas = {f['properties']['pc4']: _polygons(f['geometry']) for f in features}
        self.names = {f['properties']['pc4']: ', '.join(f['properties']['names']) for f in features}
        self.centres = {pc: _centroid(polys) for pc, polys in self.areas.items()}
        self.favourites = [pc for pc in favourites if pc in self.areas]

    def score(self, pc4):
        """Returns (score 0-5, km to the nearest favourite, nearest favourite zip), or None if unknown."""
        if not self.favourites or pc4 not in self.centres:
            return None
        if pc4 in self.favourites:
            return 5, 0.0, pc4
        x, y = self.centres[pc4]
        km, nearest = min((_distance(x, y, self.areas[fav]), fav) for fav in self.favourites)
        score = next((s for limit, s in THRESHOLDS if km <= limit), 0)
        return score, km, nearest
