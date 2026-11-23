"""Graficos de la presentacion (fuentes >= 12 pt al tamano de diapositiva)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as md
import matplotlib.pyplot as plt
import matplotlib.ticker
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
IMG = RAIZ / "presentacion" / "img"
NAVY, AZUL, ORO, GRIS = "#00204E", "#004C97", "#C98F00", "#5B6B76"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
plt.rcParams["font.family"] = "Arial"


def _estilo(a):
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.spines["left"].set_color("#BBBBBB")
    a.spines["bottom"].set_color("#BBBBBB")
    a.tick_params(labelsize=12, colors=GRIS, length=0)
    a.grid(axis="y", color="#E6E6E6", lw=0.6)


def dataset():
    d = pd.read_csv(RAIZ / "data/processed/lima_semanal.csv", parse_dates=["fecha_inicio"])
    fig, ax = plt.subplots(3, 1, figsize=(8.3, 4.95), sharex=True,
                           gridspec_kw=dict(height_ratios=[1.5, 1, 1], hspace=0.12))
    x = d.fecha_inicio
    ax[0].fill_between(x, d.casos, color=AZUL)
    ax[0].set_ylim(0, d.casos.max() * 1.25)
    ax[1].plot(x, d.temp_media, color=ORO, lw=1.3)
    ax[1].set_ylim(14.6, 25)
    ax[2].fill_between(x, d.icen, 0, where=d.icen >= 0, color=NAVY)
    ax[2].fill_between(x, d.icen, 0, where=d.icen < 0, color=GRIS)
    ax[2].set_ylim(-1.9, 5.0)
    tit = [("CASOS · MINSA-CDC", AZUL), ("TEMPERATURA (°C) · NASA POWER", ORO), ("EL NIÑO (ICEN) · IGP / ENFEN", NAVY)]
    for a, (t, c) in zip(ax, tit):
        _estilo(a)
        a.text(0.005, 0.99, t, transform=a.transAxes, va="top", fontsize=13, fontweight="bold", color=c)
    ax[0].annotate("Casi nulo de 2010 a 2022", xy=(pd.Timestamp("2016-06-01"), 30),
                   xytext=(pd.Timestamp("2011-06-01"), 3800), fontsize=13, color=NAVY,
                   arrowprops=dict(arrowstyle="-|>", color=NAVY))
    ax[0].annotate("10,256", xy=(d.loc[d.casos.idxmax(), "fecha_inicio"], d.casos.max()),
                   xytext=(-8, -4), textcoords="offset points", fontsize=13, fontweight="bold",
                   color=AZUL, ha="right", va="center")
    ax[2].xaxis.set_major_locator(md.YearLocator(2))
    ax[2].xaxis.set_major_formatter(md.DateFormatter("%Y"))
    ax[0].set_yticks([0, 5000, 10000])
    ax[0].set_yticklabels(["0", "5,000", "10,000"])
    ax[1].set_yticks([16, 20, 24])
    ax[2].set_yticks([0, 2, 4])
    fig.subplots_adjust(left=0.085, right=0.995, top=0.99, bottom=0.07)
    fig.savefig(IMG / "dataset_lima.png", dpi=200)
    plt.close(fig)


def temperatura():
    d = pd.read_csv(RAIZ / "data/processed/lima_semanal.csv", parse_dates=["fecha_inicio"])
    d = d[d.fecha_inicio >= "2022-12-25"]
    fig, ax = plt.subplots(2, 1, figsize=(12.33, 5.0), sharex=True,
                           gridspec_kw=dict(height_ratios=[1.3, 1], hspace=0.1))
    ax[0].plot(d.fecha_inicio, d.casos, color=AZUL, lw=2.5)
    ax[1].plot(d.fecha_inicio, d.temp_media, color=ORO, lw=2.2)
    ax[0].set_ylim(0, 13800)
    ax[1].set_ylim(14.5, 23.5)
    picos = [("2023-04-02", "2023-05-14", "6 semanas"), ("2024-02-11", "2024-04-14", "9 semanas")]
    for ts, cs, txt in picos:
        ts, cs = pd.Timestamp(ts), pd.Timestamp(cs)
        cmax = d.loc[d.fecha_inicio == cs, "casos"].iloc[0]
        tmax = d.loc[d.fecha_inicio == ts, "temp_media"].iloc[0]
        for a in ax:
            a.axvline(ts, color=NAVY, ls=":", lw=1.3)
            a.axvline(cs, color=NAVY, ls=":", lw=1.3)
        ax[0].plot([cs], [cmax], "o", color=NAVY, ms=8)
        ax[1].plot([ts], [tmax], "o", color=NAVY, ms=8)
        ax[0].annotate("", xy=(cs, 12000), xytext=(ts, 12000),
                       arrowprops=dict(arrowstyle="<->", color=NAVY, lw=1.8))
        ax[0].text(ts + (cs - ts) / 2, 12300, txt, ha="center", va="bottom", fontsize=14, bbox=dict(facecolor="white", edgecolor="none", pad=1.5),
                   fontweight="bold", color=NAVY)
    for a in ax:
        _estilo(a)
    ax[0].set_ylabel("Casos por semana", fontsize=13, color=NAVY)
    ax[1].set_ylabel("Temperatura (°C)", fontsize=13, color=NAVY)
    ax[0].set_yticks([0, 5000, 10000])
    ax[0].set_yticklabels(["0", "5,000", "10,000"])
    ax[1].set_yticks([16, 18, 20, 22])
    ax[1].xaxis.set_major_locator(md.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax[1].xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{MESES[md.num2date(v).month - 1]} {md.num2date(v).year % 100}"))
    fig.subplots_adjust(left=0.075, right=0.995, top=0.97, bottom=0.08)
    fig.savefig(IMG / "temperatura_casos.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    dataset()
    temperatura()


def perfil():
    r = pd.read_csv(RAIZ / "data/raw/datos_abiertos_vigilancia_dengue_2000_2024.csv", sep=";",
                    encoding="utf-8-sig", low_memory=False)
    l = r[(r.departamento == "LIMA") & (r.ano >= 2023)]
    vc = l.distrito.value_counts().head(10)[::-1]
    fig, ax = plt.subplots(2, 1, figsize=(6.5, 4.9), gridspec_kw=dict(height_ratios=[1.45, 1], hspace=0.3))
    nombres = [x.title().replace(" De ", " de ").replace(" Del ", " del ").replace("Maria", "María").replace("Martin", "Martín")
               for x in vc.index]
    ax[0].barh(nombres, vc.values, color=AZUL)
    for k, v in enumerate(vc.values):
        ax[0].text(v + 150, k, f"{v:,}", va="center", fontsize=12, color=NAVY, fontweight="bold")
    ax[0].set_title("10 distritos con más casos (64% del total)", fontsize=14, color=NAVY, fontweight="bold", loc="left")
    ax[0].set_xlim(0, vc.max() * 1.18)
    ax[0].xaxis.set_visible(False)
    a = l[l.tipo_edad == "A"]
    cuts = pd.cut(a.edad, [-1, 11, 17, 29, 59, 200], labels=["0–11", "12–17", "18–29", "30–59", "60+"])
    tab = pd.crosstab(cuts, a.sexo) / len(a) * 100
    y = range(len(tab))
    ax[1].barh(y, -tab["M"], color=NAVY, label="Hombres")
    ax[1].barh(y, tab["F"], color=ORO, label="Mujeres")
    for k, (m, f) in enumerate(zip(tab["M"], tab["F"])):
        ax[1].text(-m - 0.5, k, f"{m:.0f}%", ha="right", va="center", fontsize=12, color=NAVY, fontweight="bold")
        ax[1].text(f + 0.5, k, f"{f:.0f}%", ha="left", va="center", fontsize=12, color=ORO, fontweight="bold")
    ax[1].set_yticks(list(y))
    ax[1].set_yticklabels(tab.index)
    ax[1].set_xlim(-30, 30)
    ax[1].xaxis.set_visible(False)
    ax[1].set_title("Casos por edad y sexo (% del total)", fontsize=14, color=NAVY, fontweight="bold", loc="left")
    ax[1].legend(fontsize=12, loc="lower right", frameon=False)
    for a_ in ax:
        for sp in ("top", "right", "bottom"):
            a_.spines[sp].set_visible(False)
        a_.tick_params(labelsize=12, length=0)
    fig.subplots_adjust(left=0.36, right=0.99, top=0.94, bottom=0.02)
    fig.savefig(IMG / "perfil_lima.png", dpi=170)
    plt.close(fig)

