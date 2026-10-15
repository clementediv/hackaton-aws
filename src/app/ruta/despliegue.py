"""Campaign coverage from the same synthetic spatial inputs as the heatmap."""

from collections import Counter
from math import ceil, cos, hypot, isfinite, pi, radians, sin, sqrt

from .campanas import MIN_GROUP_SIZE

# Local equirectangular approximation, meters, adequate for an illustrative RM area.
EARTH_RADIUS = 6371008.8
LATITUDE_SCALE = EARTH_RADIUS * pi / 180
LONGITUDE_SCALE = LATITUDE_SCALE * cos(radians(-33.5))


def automatic_campaign_area(locations, *, staff=2):
    """Smallest demo radius covering one team-day; otherwise best available coverage."""
    if type(staff) is not int or not 1 <= staff <= 20:
        raise ValueError("El personal debe ser un entero entre 1 y 20.")
    target = min(len(locations), staff * 8)
    best = None
    for radius in (750, 1000, 1500, 2000, 2500, 3000):
        area = propose_campaign_area(locations, radius_m=radius, staff=staff, daily_capacity=8)
        if not area:
            continue
        if best is None or area["properties"]["people"] > best["properties"]["people"]:
            best = area
        if area["properties"]["people"] >= target:
            best = area
            break
    if best:
        best["properties"].update(
            automatic=True, target_people=target, planning_policy="smallest-radius-for-team-day"
        )
    return best


def _project(latitude, longitude):
    return (longitude + 70.7) * LONGITUDE_SCALE, (latitude + 33.5) * LATITUDE_SCALE


def _unproject(x, y):
    return x / LONGITUDE_SCALE - 70.7, y / LATITUDE_SCALE - 33.5


def propose_campaign_area(locations, *, radius_m=1500, staff=2, daily_capacity=8):
    """Maximize covered people for a fixed radius in the local planar projection.

    Candidate centers: each point and both circle centers for each pair <= 2r.
    Ties prefer lower mean squared distance, then coordinates. No LLM or map pixels.
    Returns a GeoJSON feature without identifiers or individual addresses.
    """
    if type(radius_m) not in (int, float) or not isfinite(radius_m) or not 250 <= radius_m <= 5000:
        raise ValueError("El radio debe estar entre 250 y 5000 metros.")
    if any(type(v) is not int or v < 1 for v in (staff, daily_capacity)):
        raise ValueError("Personal y capacidad deben ser enteros positivos.")
    points = []
    for location in locations:
        if (
            location.get("synthetic") is not True
            or location.get("weight") != 1
            or not all(
                type(location.get(k)) in (int, float) and isfinite(location[k])
                for k in ("latitude", "longitude")
            )
        ):
            raise ValueError("El área solo admite ubicaciones sintéticas válidas con peso 1.")
        x, y = _project(location["latitude"], location["longitude"])
        points.append((x, y, location["commune"]))
    points.sort()
    if len(points) < MIN_GROUP_SIZE:
        return None
    candidates = {(x, y) for x, y, _ in points}
    for i, (x1, y1, _) in enumerate(points):
        for x2, y2, _ in points[i + 1 :]:
            dx, dy = x2 - x1, y2 - y1
            distance = hypot(dx, dy)
            if distance == 0 or distance > 2 * radius_m:
                continue
            height = sqrt(max(0, radius_m**2 - (distance / 2) ** 2))
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            for sign in (-1, 1):
                candidates.add(
                    (mid_x - sign * dy * height / distance, mid_y + sign * dx * height / distance)
                )
    best = None
    for x, y in sorted(candidates):
        covered = [p for p in points if hypot(p[0] - x, p[1] - y) <= radius_m + 1e-6]
        compactness = sum((px - x) ** 2 + (py - y) ** 2 for px, py, _ in covered) / len(covered)
        key = (-len(covered), compactness, x, y)
        if best is None or key < best[0]:
            best = key, x, y, covered
    _, x, y, covered = best
    if len(covered) < MIN_GROUP_SIZE:
        return None
    # Center a tightly packed optimum more naturally when the mean preserves coverage.
    mean_x = sum(p[0] for p in covered) / len(covered)
    mean_y = sum(p[1] for p in covered) / len(covered)
    if all(hypot(px - mean_x, py - mean_y) <= radius_m + 1e-6 for px, py, _ in covered):
        x, y = mean_x, mean_y
        covered = [p for p in points if hypot(p[0] - x, p[1] - y) <= radius_m + 1e-6]
    ring = [
        list(_unproject(x + radius_m * cos(2 * pi * i / 96), y + radius_m * sin(2 * pi * i / 96)))
        for i in range(96)
    ]
    ring.append(ring[0])
    longitude, latitude = _unproject(x, y)
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {
            "title": "Área propuesta de campaña",
            "center_latitude": latitude,
            "center_longitude": longitude,
            "radius_m": radius_m,
            "area_km2": round(pi * (radius_m / 1000) ** 2, 2),
            "people": len(covered),
            "total_mapped": len(points),
            "coverage_percent": round(100 * len(covered) / len(points), 1),
            "communes": dict(sorted(Counter(p[2] for p in covered).items())),
            "staff": staff,
            "people_per_staff_day": daily_capacity,
            "team_daily_capacity": staff * daily_capacity,
            "estimated_days": ceil(len(covered) / (staff * daily_capacity)),
            "method": "maximum-fixed-radius-coverage-local-rm",
            "source": "Ubicaciones sintéticas del heatmap; radio y capacidad de demo",
            "status": "Propuesta simulada, sin agenda ni despacho",
            "synthetic": True,
        },
    }
