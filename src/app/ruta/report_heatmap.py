"""Offline institutional map, using the campaign's existing publication rules."""

from functools import lru_cache
from io import BytesIO

from .campanas import MIN_GROUP_SIZE, metropolitan_locations, metropolitan_ranking

MAP_SOURCE = "Límites comunales: BCN, comunas2017 (referencia). Ubicaciones sintéticas del MVP."
MAP_NOTE = (
    "Pendientes de atención en terreno, sin contacto confirmado. Solo comunas con "
    "al menos 5 casos. La intensidad representa cercanía relativa, no una tasa "
    "poblacional ni un conteo por color."
)


def heatmap_data(state, people, profiles=None):
    # Do not turn arbitrary or real addresses into invented map locations.
    candidates = [
        p for p in people if p.get("stage") == 4 and p.get("contact", {}).get("synthetic")
    ]
    local = {**state, "people": candidates}
    rows = metropolitan_ranking(local, profiles or {}) if state.get("clock") else []
    points = metropolitan_locations(local, rows) if rows else []
    return {
        "points": [{key: p[key] for key in ("latitude", "longitude", "weight")} for p in points],
        "communes": [{key: row[key] for key in ("commune", "people")} for row in rows],
        "mapped": len(points),
        "minimum_group": MIN_GROUP_SIZE,
        "source": MAP_SOURCE,
        "note": MAP_NOTE,
    }


def render_heatmap(data):
    points = tuple((p["longitude"], p["latitude"], p["weight"]) for p in data["points"])
    labels = tuple((row["commune"], row["people"]) for row in data["communes"])
    return _render(points, labels)


@lru_cache(maxsize=16)
def _render(points, labels):
    import numpy as np
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.figure import Figure
    from matplotlib.patches import Polygon

    from .contacto import METROPOLITAN_COMMUNES
    from .geografia import commune_geometries

    if points:
        longitude, latitude, _ = zip(*points, strict=True)
        cx, cy = (min(longitude) + max(longitude)) / 2, (min(latitude) + max(latitude)) / 2
        dx = max(0.20, max(longitude) - min(longitude) + 0.09)
        dy = max(0.15, max(latitude) - min(latitude) + 0.06)
        # Fill the landscape frame while preserving the local geographic aspect.
        target = (10.8 * 0.95) / (6.1 * 0.90) / 0.834
        dx = max(dx, dy * target)
        dy = max(dy, dx / target)
        bounds = (cx - dx / 2, cx + dx / 2, cy - dy / 2, cy + dy / 2)
    else:
        bounds = (-70.85, -70.48, -33.70, -33.28)
    xmin, xmax, ymin, ymax = bounds
    figure = Figure(figsize=(10.8, 6.1), dpi=180, facecolor="#0b243a")
    FigureCanvasAgg(figure)
    axes = figure.add_axes((0.025, 0.06, 0.95, 0.90), facecolor="#0b243a")
    for geometry in commune_geometries().values():
        polygons = (
            [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        )
        for polygon in polygons:
            axes.add_patch(
                Polygon(
                    polygon[0], facecolor="#12344c", edgecolor="#426177", linewidth=0.65, zorder=1
                )
            )
    x, y = np.meshgrid(np.linspace(xmin, xmax, 600), np.linspace(ymin, ymax, 400))
    density = np.zeros_like(x)
    for lon, lat, weight in points:
        density += weight * np.exp(-((x - lon) ** 2 * 0.70 + (y - lat) ** 2) / (2 * 0.009**2))
    if points:
        normalized = density / density.max()
        palette = LinearSegmentedColormap.from_list(
            "campaign_heat",
            [
                (0, (0, 0.65, 0.85, 0)),
                (0.12, (0, 0.65, 0.85, 0.20)),
                (0.30, (0.0, 0.85, 0.82, 0.65)),
                (0.55, (0.97, 0.84, 0.34, 0.86)),
                (0.80, (1, 0.44, 0.29, 0.95)),
                (1, (1, 0.29, 0.48, 1)),
            ],
        )
        axes.imshow(
            normalized,
            extent=bounds,
            origin="lower",
            cmap=palette,
            vmin=0,
            vmax=1,
            interpolation="bilinear",
            zorder=2,
        )
    counts = dict(labels)
    for _, name, lat, lon, _ in METROPOLITAN_COMMUNES:
        if xmin + 0.01 < lon < xmax - 0.01 and ymin + 0.01 < lat < ymax - 0.01:
            label = f"{name}\n{counts[name]} pendientes" if name in counts else name
            axes.text(
                lon,
                lat,
                label,
                color="#edf8ff" if name in counts else "#9eb5c6",
                fontsize=9 if name in counts else 7,
                ha="center",
                va="center",
                fontweight="bold" if name in counts else "normal",
                zorder=3,
                bbox={"facecolor": "#0b243a", "alpha": 0.85, "edgecolor": "none", "pad": 4},
            )
    if not points:
        axes.text(
            0.5,
            0.5,
            "Sin grupos publicables para este filtro",
            transform=axes.transAxes,
            ha="center",
            color="white",
            fontsize=13,
            bbox={"facecolor": "#0b243a", "alpha": 0.9, "edgecolor": "none", "pad": 15},
        )
    axes.set(xlim=(xmin, xmax), ylim=(ymin, ymax))
    axes.set_aspect(1 / np.cos(np.radians(-33.5)))
    axes.axis("off")
    axes.text(
        0.98,
        0.98,
        "N ↑",
        transform=axes.transAxes,
        ha="right",
        va="top",
        color="#c4dbe9",
        fontsize=10,
    )
    figure.text(
        0.05, 0.025, "REGIÓN METROPOLITANA  /  UBICACIONES SIMULADAS", color="#91b0c4", fontsize=7
    )
    legend = figure.add_axes((0.70, 0.035, 0.24, 0.012))
    legend.imshow(
        np.linspace(0, 1, 256)[None, :],
        aspect="auto",
        cmap=LinearSegmentedColormap.from_list(
            "heat_legend", ["#159bb5", "#00d9d1", "#f7d657", "#ff704a", "#ff4a7a"]
        ),
    )
    legend.axis("off")
    figure.text(0.70, 0.012, "BAJA", color="#91b0c4", fontsize=6)
    figure.text(0.94, 0.012, "ALTA", color="#91b0c4", fontsize=6, ha="right")
    output = BytesIO()
    figure.savefig(output, format="png", facecolor=figure.get_facecolor())
    return output.getvalue()
