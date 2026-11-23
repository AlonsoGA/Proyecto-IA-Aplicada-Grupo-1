"""Mapa de calor de casos por distrito (provincia de Lima, 2023-24). Limites: IGN via joseluisq/peru-geojson-datasets."""
import json, os, unicodedata, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from pathlib import Path as P

RAIZ = P(__file__).resolve().parents[1]
GEO = P(os.environ["TEMP"]) / "lc.geojson"


def n(x):
    return "".join(c for c in unicodedata.normalize("NFD", str(x).upper().strip()) if unicodedata.category(c) != "Mn")


def parches(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        v, c = [], []
        for ring in poly:
            v += ring
            c += [Path.MOVETO] + [Path.LINETO] * (len(ring) - 2) + [Path.CLOSEPOLY]
        yield Path(v, c)


def mapa(salida):
    r = pd.read_csv(RAIZ / "data/raw/datos_abiertos_vigilancia_dengue_2000_2024.csv", sep=";",
                    encoding="utf-8-sig", low_memory=False)
    l = r[(r.departamento == "LIMA") & (r.provincia == "LIMA") & (r.ano >= 2023)]
    c = l.groupby(l.distrito.map(n)).size()
    d = json.load(open(GEO, encoding="utf8"))
    cmap = LinearSegmentedColormap.from_list("m", ["#EEF1F6", "#8FB3DB", "#004C97", "#001F4D"])
    norm = Normalize(0, c.max())
    fig, ax = plt.subplots(figsize=(6.0, 4.9))
    for f in d["features"]:
        p = f["properties"]
        if p["provincia"] != "LIMA":
            continue
        v = c.get(n(p["distrito"]), 0)
        for path in parches(f["geometry"]):
            ax.add_patch(PathPatch(path, fc=cmap(norm(v)), ec="white", lw=0.6))
    ax.autoscale_view(); ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-77.2, -76.6); ax.set_ylim(-12.42, -11.7)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.01)
    cb.ax.tick_params(labelsize=12)
    cb.set_ticks([0, 5000, 10000]); cb.set_ticklabels(["0", "5,000", "10,000"])
    cb.set_label("Casos 2023–24", fontsize=12)
    fig.subplots_adjust(left=0, right=0.9, top=1, bottom=0)
    fig.savefig(salida, dpi=170)
    print(c.sort_values().tail(3))


if __name__ == "__main__":
    mapa(RAIZ / "presentacion/img/mapa_calor_lima.png")
