"""Construye presentacion_final.pptx a partir de avance_semana11.pptx.

Agrega portada, motivacion, datos, comparacion de modelos, hiperparametros y
grafico de XGBoost; reescribe titulos como oraciones y cita el paper del LSTM.
Uso (desde la raiz del repo): python presentacion/construir_presentacion.py
"""
import copy
import os
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "presentacion" / "avance_semana11.pptx"
DESTINO = Path(os.environ.get("PPTX_SALIDA", RAIZ / "presentacion" / "presentacion_final.pptx"))

NAVY, AZUL, GRIS = RGBColor(0x00, 0x1F, 0x4E), RGBColor(0x00, 0x4C, 0x97), RGBColor(0x5B, 0x6B, 0x73)
ORO, CLARO = RGBColor(0xC9, 0x8F, 0x00), RGBColor(0xEE, 0xF2, 0xF7)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
X0, ANCHO = 457200, 11274552

prs = Presentation(ORIGEN)
LAYOUT = prs.slide_layouts.get_by_name("CONTENIDO")
S = list(prs.slides)  # 0 problema, 1 temperatura, 2 cuadricula, 3 LSTM, 4 literatura


def forma(slide, nombre):
    return next(s for s in slide.shapes if s.name == nombre)


def poner_texto(sh, *parrafos):
    """Cambia el texto conservando el formato del primer run de cada parrafo."""
    tf = sh.text_frame
    for p, texto in zip(tf.paragraphs, parrafos):
        runs = p.runs
        runs[0].text = texto
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
    for p in tf.paragraphs[len(parrafos):]:
        p._p.getparent().remove(p._p)


def titulo(slide, texto):
    poner_texto(forma(slide, "Text 2"), texto)


def nueva(copiando=None):
    """Diapositiva nueva con titulo, fuentes y numero copiados de una existente."""
    base = copiando or S[0]
    s = prs.slides.add_slide(LAYOUT)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    for sh in base.shapes:
        if copiando is not None or sh.name in ("Text 2", "Fuentes", "Slide Number Placeholder 0"):
            s.shapes._spTree.append(copy.deepcopy(sh._element))
    return s


def caja(slide, x, y, w, h, texto, size, color=NAVY, bold=False, align=None,
         font=None, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, t in enumerate(texto if isinstance(texto, list) else [texto]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align:
            p.alignment = align
        r = p.add_run()
        r.text = t
        r.font.size, r.font.bold = Pt(size), bold
        r.font.color.rgb = color
        if font:
            r.font.name = font
    return tb


def tabla(slide, x, y, anchos, filas, alto_fila, size=16, cabeceras=1,
          mejores=(), alinear_izq=(0,)):
    """filas: lista de listas de texto. mejores: (fila, col) resaltadas."""
    gf = slide.shapes.add_table(len(filas), len(anchos), Emu(x), Emu(y),
                                Emu(sum(anchos)), Emu(alto_fila * len(filas)))
    t = gf.table
    t.first_row = False
    t.horz_banding = False
    for j, w in enumerate(anchos):
        t.columns[j].width = Emu(w)
    for i, fila in enumerate(filas):
        t.rows[i].height = Emu(alto_fila)
        for j, texto in enumerate(fila):
            c = t.cell(i, j)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = c.margin_right = Emu(91440)
            c.fill.solid()
            cab = i < cabeceras
            c.fill.fore_color.rgb = NAVY if cab else (CLARO if i % 2 == 0 else BLANCO)
            p = c.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j in alinear_izq else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = texto
            r.font.size = Pt(size)
            r.font.bold = cab or (i, j) in mejores or j == 0
            r.font.color.rgb = BLANCO if cab else (AZUL if (i, j) in mejores else NAVY)
    return t


IMG = RAIZ / "presentacion" / "img"
AMARILLO = RGBColor(0xFD, 0xD2, 0x1F)


def rect(slide, x, y, w, h, color, redondo=False, atras=False):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if redondo else MSO_SHAPE.RECTANGLE,
                                Emu(x), Emu(y), Emu(w), Emu(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.shadow.inherit = False
    if redondo:
        sh.adjustments[0] = 0.08
    if atras:
        tree = slide.shapes._spTree
        tree.remove(sh._element)
        tree.insert(2, sh._element)
    return sh


def flecha(slide, x, y, w, h, color, texto, size=16):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.PENTAGON, Emu(x), Emu(y), Emu(w), Emu(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.word_wrap = True
    tf.margin_left, tf.margin_right = Emu(150000), Emu(250000)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = texto
    r.font.size, r.font.bold, r.font.color.rgb = Pt(size), True, BLANCO
    return sh


def foto(slide, nombre, x, y, w, h):
    return slide.shapes.add_picture(str(IMG / nombre), Emu(x), Emu(y), Emu(w), Emu(h))


def limpiar(slide, conservar=("Text 2", "Fuentes", "Slide Number Placeholder 0")):
    for t in slide._element.findall("{http://schemas.openxmlformats.org/presentationml/2006/main}timing"):
        slide._element.remove(t)
    for sh in list(slide.shapes):
        if sh.name not in conservar:
            sh._element.getparent().remove(sh._element)


def tarjeta(slide, x, y, w, h, etiqueta, texto, color):
    rect(slide, x, y, w, h, CLARO, redondo=True)
    rect(slide, x, y + 120000, 70000, h - 240000, color)
    caja(slide, x + 220000, y + 150000, w - 340000, 260000, etiqueta, 12, color=color, bold=True)
    caja(slide, x + 220000, y + 520000, w - 340000, h - 600000, texto, 20, color=NAVY)


# ---------------------------------------------------------------- 1 motivacion
titulo(S[0], "Lima sufre la peor epidemia de dengue sin ser zona endémica")
limpiar(S[0])
ROJO = RGBColor(0xC6, 0x28, 0x28)
# Casos por anio en Lima (barras lineales): 2023-24 aplastan a los 13 anios anteriores.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
plt.rcParams["font.family"] = "Arial"
_d = pd.read_csv(RAIZ / "data/processed/lima_semanal.csv", parse_dates=["fecha_inicio"])
_y = _d.groupby(_d.fecha_inicio.dt.year).casos.sum()
assert _y.loc[:2022].sum() == 3474 and _y.loc[2023:].sum() == 118599
_fig, _ax = plt.subplots(figsize=(7.4, 4.6))
_cols = ["#5B6B73" if a_ < 2023 else "#C62828" for a_ in _y.index]
_ax.bar(_y.index, _y.values, color=_cols, width=0.72)
_ax.text(2023.4, _y[2023] + 1800, f"{_y[2023]:,}", ha="right", fontsize=15, fontweight="bold", color="#C62828")
_ax.text(2024, _y[2024] + 1800, f"{_y[2024]:,}", ha="center", fontsize=15, fontweight="bold", color="#C62828")
_ax.annotate("2010–2022: 3,474 casos\nen 13 años", xy=(2016, 1500), xytext=(2010.2, 42000),
             fontsize=14, color="#5B6B73", fontweight="bold",
             arrowprops=dict(arrowstyle="->", color="#5B6B73", lw=1.6))
_ax.set_ylim(0, 97000)
_ax.set_yticks([0, 25000, 50000, 75000]); _ax.set_yticklabels(["0", "25,000", "50,000", "75,000"])
_ax.set_xticks(range(2010, 2025, 2)); _ax.tick_params(labelsize=12)
_ax.set_ylabel("Casos por año en Lima", fontsize=13)
_ax.grid(axis="y", alpha=0.3)
for _sp in ("top", "right"):
    _ax.spines[_sp].set_visible(False)
_fig.tight_layout()
_fig.savefig(IMG / "casos_por_anio.png", dpi=170)
plt.close(_fig)
_w = 6900000
S[0].shapes.add_picture(str(IMG / "casos_por_anio.png"), Emu(X0), Emu(1750000), Emu(_w), Emu(int(_w * 4.6 / 7.4)))
caja(S[0], X0, 1371600, 6900000, 300000, "Casos de dengue por año en Lima", 14, color=GRIS, bold=True)
_xd = X0 + _w + 400000
_wd = X0 + ANCHO - _xd
caja(S[0], _xd, 1750000, _wd, 950000, "34 veces", 54, color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
caja(S[0], _xd, 2700000, _wd, 1000000, "más casos en 2 años (118,599) que en los 13 años anteriores", 18, color=NAVY)
caja(S[0], _xd, 4000000, _wd, 950000, "10,256", 54, color=ROJO, bold=True, anchor=MSO_ANCHOR.MIDDLE)
caja(S[0], _xd, 4950000, _wd, 800000, ["casos en una sola semana", "(abril 2024)"], 18, color=NAVY)
poner_texto(forma(S[0], "Fuentes"),
            "Fuentes: MINSA-CDC Perú (RENACE) 2010–2024; Alcantara-Zapata et al. (2025), Perspect. Public Health; "
            "Ramírez-Soto et al. (2023), PLoS ONE.")

# ------------------------------------------------------ 1b para que sirve
util = nueva()
titulo(util, "Con 4 semanas de aviso se puede fumigar y preparar hospitales antes del brote")
foto(util, "fumigacion_peru.jpg", X0, 1371600, 5500000, 2900000)
foto(util, "paciente_dengue.jpg", 6231752, 1371600, 5500000, 2900000)
caja(util, X0, 4380000, 5500000, 300000, "FUMIGAR Y ELIMINAR CRIADEROS", 14, color=AZUL, bold=True)
caja(util, 6231752, 4380000, 5500000, 300000, "ATENDER A LOS PACIENTES: PREPARAR CAMAS Y PERSONAL", 14, color=AZUL, bold=True)
for i, (col, tx) in enumerate(((NAVY, "Hoy: predecir los casos de 4 semanas después"),
                               (AZUL, "Antes del brote: fumigación y control de criaderos"),
                               (ORO, "Semana +4: hospitales listos para la ola"))):
    flecha(util, X0 + i * 3737000, 4950000, 3800552, 1150000, col, tx, 17)
poner_texto(forma(util, "Fuentes"),
            "Fotos (Flickr): EU Civil Protection and Humanitarian Aid / CESVI (CC BY-NC-ND); Ministerio de Defensa del Perú (CC BY).")

# -------------------------------------------------------------------- 2 datos
dato = nueva()
titulo(dato, "Usamos casos, clima y el índice El Niño (ICEN) de 81 distritos de Lima")
_GAP = 250000
_W3 = (ANCHO - 2 * _GAP) // 3
for i, (num, tx, col) in enumerate((("937,119", "registros de dengue en Perú, 2010–2024", AZUL),
                                    ("782", "semanas de 81 distritos de Lima", NAVY),
                                    ("45", "variables para cada semana", AZUL))):
    x = X0 + i * (_W3 + _GAP)
    rect(dato, x, 1371600, _W3, 2150000, col, redondo=True)
    caja(dato, x + 250000, 1500000, _W3 - 500000, 1000000, num, 60, color=AMARILLO, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    caja(dato, x + 250000, 2550000, _W3 - 500000, 800000, tx, 20, color=BLANCO)
for i, (et, tx, col) in enumerate((
        ("CASOS · MINSA-CDC", "Un registro por caso, con distrito y semana", AZUL),
        ("CLIMA · NASA POWER", "Temperatura, lluvia y humedad", ORO),
        ("EL NIÑO · ICEN, IGP", "Qué tan cálido está el mar frente a lo normal", NAVY))):
    x = X0 + i * (_W3 + _GAP)
    rect(dato, x, 3900000, _W3, 2150000, CLARO, redondo=True)
    rect(dato, x, 4050000, 70000, 1850000, col)
    caja(dato, x + 250000, 4150000, _W3 - 450000, 300000, et, 14, color=col, bold=True)
    caja(dato, x + 250000, 4600000, _W3 - 450000, 1300000, tx, 22, color=NAVY)
poner_texto(forma(dato, "Fuentes"), "Fuentes: MINSA-CDC Perú (RENACE); NASA POWER; IGP/ENFEN.")

# ---- anatomia de una semana (ejemplo real)
anat = nueva()
titulo(anat, "Cada semana, el modelo recibe 45 variables y predice los casos 4 semanas después")
caja(anat, X0, 1371600, 7000000, 300000, "EJEMPLO REAL: SEMANA DEL 17 DE MARZO DE 2024", 14, color=AZUL, bold=True)
for i, (et, tx, col) in enumerate((
        ("CASOS DE LIMA · 10 VARIABLES", "5,291 casos; las 3 semanas previas: 4,687, 3,380, 2,333", AZUL),
        ("CLIMA · 27 VARIABLES", "20.6 °C y hasta 12 semanas atrás; lluvia y humedad", ORO),
        ("OTRAS REGIONES · 5 VARIABLES", "Casos en Callao, Ica, La Libertad y Áncash", NAVY),
        ("EL NIÑO · 1 VARIABLE", "ICEN +0.38: mar casi normal", AZUL),
        ("ESTACIONALIDAD · 2 VARIABLES", "Semana 12 del año", ORO))):
    y = 1750000 + i * 880000
    rect(anat, X0, y, 7000000, 800000, CLARO, redondo=True)
    rect(anat, X0, y + 80000, 70000, 640000, col)
    caja(anat, X0 + 200000, y + 60000, 6700000, 250000, et, 12, color=col, bold=True)
    caja(anat, X0 + 200000, y + 330000, 6700000, 450000, tx, 16, color=NAVY)
caja(anat, 7650000, 3300000, 450000, 450000, ">", 32, color=ORO, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
rect(anat, 8200000, 1750000, 3531752, 4320000, NAVY, redondo=True)
caja(anat, 8400000, 1900000, 3150000, 300000, "PREDECIR", 14, color=AMARILLO, bold=True)
caja(anat, 8400000, 2300000, 3150000, 900000, "Los casos de 4 semanas después", 20, color=BLANCO, bold=True)
caja(anat, 8400000, 3500000, 3150000, 300000, "Semana del 14 de abril de 2024", 14, color=BLANCO)
caja(anat, 8400000, 3900000, 3150000, 800000, "10,256", 54, color=AMARILLO, bold=True, anchor=MSO_ANCHOR.MIDDLE)
caja(anat, 8400000, 4750000, 3150000, 500000, "casos reales: el pico de 2024", 16, color=BLANCO)
poner_texto(forma(anat, "Fuentes"), "Fuentes: MINSA-CDC Perú (RENACE); NASA POWER; IGP/ENFEN.")

# ---- perfil (oculta)
import graficos
graficos.perfil()
perf = nueva()
titulo(perf, "Cinco distritos reúnen 40% de los casos de Lima 2023–24; la mayoría de los casos son adultos")
_wmap = 5000000
perf.shapes.add_picture(str(IMG / "mapa_calor_lima.png"), Emu(X0), Emu(1750000), Emu(_wmap), Emu(int(_wmap * 4.9 / 6.0)))
caja(perf, X0, 1371600, _wmap, 330000, "Casos por distrito, Lima 2023–24", 14, color=GRIS, bold=True)
caja(perf, X0, 5900000, _wmap, 420000, "Comas y San Juan de Lurigancho concentran los casos: unos 13,000 cada uno.", 14, color=NAVY, bold=True)
_wper = 6500000
perf.shapes.add_picture(str(IMG / "perfil_lima.png"), Emu(X0 + ANCHO - _wper), Emu(1371600), Emu(_wper), Emu(int(_wper * 4.9 / 6.5)))
poner_texto(forma(perf, "Fuentes"), "Fuentes: MINSA-CDC Perú (RENACE), 118,599 casos de Lima en 2023–2024. Mapa: límites del IGN, provincia de Lima.")
poner_texto(forma(dato, "Fuentes"),
            "Fuentes: MINSA-CDC Perú (RENACE); NASA POWER; IGP/ENFEN.")

titulo(S[1], "La temperatura alcanzó su máximo 6 y 9 semanas antes que los casos")
caja(S[1], X0, 6040000, ANCHO, 280000,
     "Solo hay dos olas: es una observación que respalda usar clima rezagado, no una prueba de causalidad.",
     13, color=GRIS)

# ---------------------------------------------------- ablacion y error por fase
titulo(S[3], "El efecto de quitar variables depende del grupo")
limpiar(S[3])
caja(S[3], X0, 1371600, 6700000, 380000,
     "MAE en Lima (casos por semana) al quitar un grupo de variables", 14, color=GRIS, bold=True)
filas = (("Modelo completo", 70.5, NAVY), ("Sin ICEN (índice El Niño)", 68.6, AZUL), ("Sin tendencias recientes", 68.8, AZUL),
         ("Sin clima", 73.1, ORO), ("Sin estacionalidad", 75.8, ORO), ("Sin casos de otras regiones", 77.1, ORO),
         ("Persistencia (referencia)", 132.8, GRIS))
maxw = 3000000
for i, (nom, val, col) in enumerate(filas):
    y = 1780000 + i * 620000
    caja(S[3], X0, y, 2900000, 500000, nom, 15, color=NAVY, bold=(i == 0), anchor=MSO_ANCHOR.MIDDLE)
    w = int(maxw * val / 132.8)
    rect(S[3], X0 + 3000000, y + 50000, w, 400000, col)
    caja(S[3], X0 + 3000000 + w + 80000, y, 1000000, 500000, str(val), 16, color=col, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
rect(S[3], 7500000, 1371600, 4231752, 4700000, NAVY, redondo=True)
caja(S[3], 7750000, 1500000, 3750000, 1000000, "96.8%", 54, color=AMARILLO, bold=True)
caja(S[3], 7750000, 2550000, 3750000, 1100000,
     "del error se concentra en las 77 semanas de brote de 759.", 20, color=BLANCO, bold=True)
caja(S[3], 7750000, 3750000, 3750000, 2200000,
     ["La fase de subida concentra cerca del 68.6% del error."], 18, color=BLANCO)
caja(S[3], X0, 6120000, 6900000, 300000,
     "El ICEN usado es el definitivo, que se conoce después.",
     12, color=GRIS)
sh = forma(S[3], "Fuentes")
sh._element.getparent().remove(sh._element)

# ------------------------------------------------- comparacion de 3 modelos
cmp_ = nueva()
titulo(cmp_, "Con el mismo protocolo, XGBoost completo tiene el menor error, pero su ventaja sobre las redes no es significativa")
caja(cmp_, X0, 1371600, 6600000, 330000, "Mismas 759 semanas de Lima, mismo walk-forward, 3 semillas", 14, color=AZUL, bold=True)
tabla(cmp_, X0, 1750000, [2700000, 1100000, 1100000, 1700000],
      [["Modelo", "MAE", "WAPE", "MAE 2023–24"],
       ["Persistencia", "132.8", "82.6%", "1,014"],
       ["XGBoost base", "79.1", "49.2%", "596"],
       ["XGBoost completo*", "67.0", "41.7%", "503"],
       ["LSTM base", "73.3", "45.6%", "550"],
       ["LSTM completo*", "76.5", "47.6%", "575"],
       ["GRU base", "91.0", "56.6%", "691"],
       ["GRU completo*", "91.4", "56.8%", "694"]],
      400000, size=14, mejores={(3, 1), (3, 2), (3, 3)})
rect(cmp_, 7600000, 1371600, 4131752, 3580000, CLARO, redondo=True)
caja(cmp_, 7800000, 1450000, 3750000, 600000,
     "Diferencia de MAE: XGBoost completo menos la red (IC 95%)", 14, color=AZUL, bold=True)
caja(cmp_, 7800000, 2150000, 3750000, 400000, "LSTM", 16, color=NAVY, bold=True)
caja(cmp_, 7800000, 2500000, 3750000, 500000, "−4.4  [−18, +7]", 24, color=NAVY, bold=True)
caja(cmp_, 7800000, 3150000, 3750000, 400000, "GRU", 16, color=NAVY, bold=True)
caja(cmp_, 7800000, 3500000, 3750000, 500000, "−24.5  [−67, +3]", 24, color=NAVY, bold=True)
caja(cmp_, 7800000, 4150000, 3750000, 700000,
     "Los intervalos incluyen 0: no hay diferencia significativa.", 14, color=GRIS)
caja(cmp_, X0, 5150000, ANCHO, 560000,
     "Igual para todos: universo de 5 departamentos, variables, objetivo (delta del log), reentreno cada 13 semanas y búsqueda de hiperparámetros con validación temporal.",
     14, color=NAVY)
caja(cmp_, X0, 5750000, ANCHO, 300000,
     "* Completo = base + Callao, Ica, La Libertad, Áncash + tendencias recientes. WAPE = error total / casos reales. MAE en casos por semana.",
     12, color=GRIS)
caja(cmp_, X0, 6050000, ANCHO, 420000,
     "En la literatura: ARIMA supera a LSTM y BiLSTM por 5–8% en la selva peruana; XGBoost fue el mejor en Singapur (MAE 89.12).",
     12, color=NAVY)
poner_texto(forma(cmp_, "Fuentes"),
            "Referencias: Zhou et al. (2024); Mayta-Quispe y Alemán (2025); Tian et al. (2024); Carvajal et al. (2018).")

# ------------------------------------------------------- literatura (antes de la EDA)
lit = nueva()
titulo(lit, "Cuatro hallazgos de la literatura guiaron nuestro diseño")
caja(lit, X0, 1371600, 5400000, 300000, "QUÉ ENCONTRAMOS", 14, color=AZUL, bold=True)
caja(lit, X0 + 5900000, 1371600, 5374552, 300000, "QUÉ HICIMOS", 14, color=ORO, bold=True)
for i, (hall, cita, hec, col) in enumerate((
        ("El clima actúa con rezago de 2 a 8 semanas", "Leung et al. (2023); Carvajal et al. (2018)",
         "Clima con rezagos de 2 a 12 semanas", AZUL),
        ("Los modelos simples compiten con los profundos",
         "Mayta-Quispe y Alemán (2025); Tian et al. (2024)", "XGBoost frente a LSTM, GRU y persistencia", ORO),
        ("Hay que evaluar el pico, no solo el promedio", "Hii et al. (2012); Benedum et al. (2020)",
         "Medimos retraso y subestimación del pico", NAVY),
        ("Casi no hay ML para Lima con El Niño", "Leung et al. (2023)",
         "Incluimos el ICEN y medimos su aporte", AZUL))):
    y = 1720000 + i * 1110000
    rect(lit, X0, y, 5400000, 1010000, CLARO, redondo=True)
    rect(lit, X0, y + 100000, 70000, 810000, col)
    caja(lit, X0 + 200000, y + 80000, 5100000, 600000, hall, 16, color=NAVY, bold=True)
    caja(lit, X0 + 200000, y + 700000, 5100000, 280000, cita, 12, color=GRIS)
    flecha(lit, X0 + 5500000, y + 280000, 400000, 450000, col, "", 12)
    rect(lit, X0 + 5900000, y, 5374552, 1010000, NAVY, redondo=True)
    caja(lit, X0 + 6100000, y, 4974552, 1010000, hec, 18, color=BLANCO, bold=True, anchor=MSO_ANCHOR.MIDDLE)
poner_texto(forma(lit, "Fuentes"),
            "Referencias: Leung et al. (2023), PLOS NTD; Carvajal et al. (2018); Mayta-Quispe y Alemán (2025); Tian et al. (2024); Hii et al. (2012); Benedum et al. (2020).")

# ------------------------------------------------------- hiperparametros
hp = nueva()
titulo(hp, "En XGBoost, la búsqueda de 30 configuraciones bajó el error de validación de 0.82 a 0.73")
filas = [
    ["Hiperparámetro", "Probados", "Predice 2023", "Predice 2024"],
    ["n_estimators", "100, 200, 400, 600", "100", "100"],
    ["max_depth", "2, 3, 4, 6", "6", "4"],
    ["learning_rate", "0.01, 0.02, 0.05, 0.1", "0.05", "0.05"],
    ["subsample", "0.6, 0.8, 1.0", "0.8", "0.6"],
    ["colsample_bytree", "0.5, 0.8, 1.0", "0.8", "0.8"],
    ["min_child_weight", "1, 5, 10, 20", "10", "20"],
    ["reg_lambda", "1, 5, 10, 30", "1", "1"],
]
tabla(hp, X0, 1371600, [2300000, 2900000, 1400000, 1400000], filas, 548640, size=17,
      alinear_izq=(0, 1))
caja(hp, 8700000, 1371600, 3030000, 800000, "0.82 → 0.73", 36, color=AZUL, bold=True)
caja(hp, 8700000, 2450000, 3000000, 1400000,
     "error de validación relativo a la persistencia (1.0 = igual)", 20, color=NAVY, bold=True)
caja(hp, 8700000, 3900000, 3000000, 1900000,
     "Búsqueda aleatoria con validación cruzada temporal (2016, 2017, 2020–2022). Para 2023 se eligen con datos hasta 2022; para 2024, hasta 2023 (0.82 → 0.74).",
     16, color=GRIS)
poner_texto(forma(hp, "Fuentes"),
            "Fuentes: results/tuning_hiperparametros.json; src/models.py (espacio de búsqueda); notebook 03_xgboost.")

# ------------------------------------------------------- grafico XGBoost
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Arial"
import pandas as pd
_pl = pd.read_csv(RAIZ / "results/predicciones_lima.csv", parse_dates=["fecha_inicio"])
_d = _pl.fecha_inicio >= "2022-10-01"
_fig, _ax = plt.subplots(figsize=(7.4, 4.6))
_ax.fill_between(_pl.fecha_inicio[_d], _pl.real[_d], color="lightgray", label="Casos reales (t+4)")
for _col, _c, _n in (("Persistencia", "tab:blue", "Persistencia"), ("XGBoost tuneado", "tab:orange", "XGBoost base"),
                     ("XGBoost tuneado + regional + nuevas", "tab:red", "XGBoost completo")):
    _ax.plot(_pl.fecha_inicio[_d], _pl[_col][_d], lw=1.8, color=_c, label=_n)
_ax.set_ylabel("Casos por semana", fontsize=13)
_ax.set_yticks([0, 5000, 10000]); _ax.set_yticklabels(["0", "5,000", "10,000"])
_ax.legend(fontsize=12, loc="upper left", framealpha=0.9); _ax.grid(alpha=0.3); _ax.tick_params(labelsize=12)
import matplotlib.dates as _md
_ax.xaxis.set_major_locator(_md.MonthLocator(bymonth=[1, 7]))
_ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: ("Ene" if _md.num2date(v).month == 1 else "Jul") + " " + str(_md.num2date(v).year % 100)))
for _sp in ("top", "right"):
    _ax.spines[_sp].set_visible(False)
_fig.tight_layout()
_fig.savefig(IMG / "xgboost_vs_real.png", dpi=170)
plt.close(_fig)
gx = nueva()
titulo(gx, "XGBoost reduce el error a la mitad en 2024, pero predice el pico 2 semanas tarde")
_w = 6900000
gx.shapes.add_picture(str(IMG / "xgboost_vs_real.png"), Emu(X0), Emu(1371600), Emu(_w), Emu(int(_w * 4.6 / 7.4)))
caja(gx, 7600000, 1371600, 4131752, 330000, "MAE en Lima, 2024 (casos por semana)", 14, color=GRIS, bold=True)
tabla(gx, 7600000, 1800000, [2531752, 1600000],
      [["Modelo", "MAE"], ["Persistencia", "1,688"], ["GRU base", "1,065"], ["LSTM base", "846"],
       ["XGBoost base", "985"], ["XGBoost completo", "793"]],
      480000, size=14, mejores={(5, 1)})
caja(gx, 7600000, 4800000, 4131752, 600000,
     "En la semana del pico subestima 5,232 casos: llega a esa altura tarde.", 16, color=NAVY, bold=True)
rect(gx, 7600000, 5450000, 4131752, 800000, CLARO, redondo=True)
caja(gx, 7750000, 5480000, 3850000, 740000,
     ["Persistencia: repetir los casos de hace 4 semanas.", "MAE: error promedio en casos por semana.",
      "En 2024, XGBoost y redes no se distinguen (IC 95%)."],
     12, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
poner_texto(forma(gx, "Fuentes"),
            "Referencias: Zhou (2024); Tian (2024); Mayta-Quispe y Alemán (2025); Leung (2023); Carvajal (2018); Hii (2012); Benedum (2020).")

# ------------------------------------------------------------- siguientes pasos
titulo(S[4], "XGBoost reduce el error a la mitad y avisa antes que la persistencia, pero aún tarde")
limpiar(S[4])
XD = X0 + 5600000
rect(S[4], X0, 1371600, 5400000, 4700000, NAVY, redondo=True)
caja(S[4], X0 + 300000, 1520000, 4800000, 300000, "CONCLUSIONES", 14, color=AMARILLO, bold=True)
for i, (num, tx) in enumerate((("−50%", "de error (MAE) frente a la persistencia; −48% sin ICEN"),
                               ("Ablación", "el MAE baja sin ICEN o sin tendencias recientes; sube al quitar los otros tres grupos"),
                               ("LSTM y GRU", "sin diferencia significativa con XGBoost (IC 95%)"),
                               ("4 → 1–3 semanas", "de retraso al avisar 500 casos; 22 variantes no lo bajaron"))):
    y = 1900000 + i * 1030000
    caja(S[4], X0 + 300000, y, 4800000, 560000, num, 34 if i < 2 else 28, color=AMARILLO, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
    caja(S[4], X0 + 300000, y + 560000, 4900000, 330000, tx, 15, color=BLANCO)
caja(S[4], XD, 1371600, 5600000, 300000, "SIGUIENTES PASOS", 14, color=AZUL, bold=True)
for i, (et, tx, col) in enumerate((
        ("PASO 1", "Operar con datos publicados cada semana", AZUL),
        ("PASO 2", "Sumar brotes de zonas endémicas (Junín)", ORO),
        ("PASO 3", "Alertar el riesgo de superar un umbral", NAVY),
        ("PASO 4", "Por distrito: ¿iniciará un brote? (sí/no)", AZUL))):
    tarjeta(S[4], XD, 1750000 + i * 1110000, 5674552, 1030000, et, tx, col)
forma(S[4], "Fuentes")._element.getparent().remove(forma(S[4], "Fuentes")._element)

# -------------------------------------------------------------- portada
pt = nueva()
for sh in list(pt.shapes):
    if sh.name in ("Fuentes", "Slide Number Placeholder 0"):
        sh._element.getparent().remove(sh._element)
rect(pt, 0, 0, 7000000, 6858000, NAVY, atras=True)
foto(pt, "portada.jpg", 7000000, 0, 5192000, 6858000)
foto(pt, "logo_fci.png", 600000, 470000, 2900000, int(2900000 * 52 / 202))
rect(pt, 600000, 1500000, 900000, 90000, AMARILLO)
tit = forma(pt, "Text 2")
tit.left, tit.top, tit.width, tit.height = Emu(600000), Emu(1750000), Emu(5900000), Emu(2400000)
poner_texto(tit, "Predicción de casos de dengue en Lima con 4 semanas de anticipación")
r0 = tit.text_frame.paragraphs[0].runs[0]
r0.font.size = Pt(40)
r0.font.color.rgb = BLANCO
caja(pt, 600000, 4500000, 5900000, 450000, "Luis Leiva y Alonso Gutiérrez", 26, color=AMARILLO, bold=True)
caja(pt, 600000, 5100000, 5900000, 700000,
     ["Inteligencia Artificial Aplicada (1INF62)", "Grupo 1 · 2026-2"], 18, color=BLANCO)
caja(pt, 7100000, 6500000, 5000000, 250000, "Foto: Aedes aegypti, Wikimedia Commons", 12, color=BLANCO)

# ---------------------------------------------------------------- orden
lista = prs.slides._sldIdLst
ids = list(lista)
orden = {id(s): e for s, e in zip(prs.slides, ids)}
final = [pt, S[0], util, dato, perf, gx, S[4], cmp_, hp, anat, S[2], S[1], S[3]]
for _o in (cmp_, hp, anat, S[2], S[1], S[3]):
    _o._element.set("show", "0")
_e_lit = orden[id(lit)]
prs.part.drop_rel(_e_lit.rId)
for e in ids:
    lista.remove(e)
for s in final:
    lista.append(orden[id(s)])

import re
INTERNO = re.compile(r"notebook|results/|src/|\.csv|\.json|Kaggle")
for sl in final:
    for sh in list(sl.shapes):
        if sh.name == "Fuentes":
            txt = sh.text_frame.text
            pref, _, resto = txt.partition(":")
            partes = [re.sub(r",?\s*notebook \w+( \([^)]*\))?", "", x).strip(" .") for x in re.split(r"[;]", resto)]
            partes = [x for x in partes if not INTERNO.search(x)]
            partes = [x for x in partes if x]
            if not partes:
                sh._element.getparent().remove(sh._element)
            else:
                poner_texto(sh, pref + ": " + "; ".join(partes) + ".")

# --------------------------------------- alineacion a los margenes de la plantilla
import graficos
graficos.dataset()
graficos.temperatura()
for sh in list(S[1].shapes):
    if sh.name == "Gráfico temperatura":
        sh._element.getparent().remove(sh._element)
_pic = S[1].shapes.add_picture(str(IMG / "temperatura_casos.png"), Emu(X0), Emu(1371600),
                               Emu(ANCHO), Emu(int(ANCHO * 5.0 / 12.33)))
_pic.name = "Gráfico temperatura"
for sh in S[2].shapes:
    if sh.name in ("Cuadrícula 59", "Etiqueta con casos", "Etiqueta 0 casos"):
        sh.left = Emu(sh.left - 91440)
    if sh.name == "Cuadrícula título":
        poner_texto(sh, "Cada cuadro es 1% de las 782 semanas")
        sh.left = Emu(X0 - 91440)
    if sh.name == "Etiqueta con casos":
        poner_texto(sh, "41%", "semanas con casos")
    if sh.name == "Etiqueta 0 casos":
        poner_texto(sh, "59%", "semanas con 0 casos")
        sh.left, sh.width = Emu(sh.left - 150000), Emu(sh.width + 300000)
    if sh.name == "Decisión texto":
        sh.text_frame.paragraphs[0].runs[0].text = "Trabajamos en log(1 + casos)"
    if sh.name == "Cuadrícula 59":
        sh._element.nvPicPr.cNvPr.set("descr", "Cuadrícula de 100 cuadros, cada uno 1% de las 782 semanas de Lima. "
                                      "59 azules: semanas con 0 casos; 41 blancos: semanas con casos.")
    if sh.name == "Concentración texto":
        sh.width = Emu(X0 + ANCHO - sh.left)

# ------------------------------------------- tipografia (Manual de identidad PUCP)
# Tipografias seguras para plantillas de escritorio: Georgia (titulos) y Arial (texto).
FUENTE_TIT, FUENTE_TXT = "Georgia", "Arial"


def _tipografia(shapes):
    for sh in shapes:
        marcos = []
        if sh.has_text_frame:
            marcos.append(sh.text_frame)
        if getattr(sh, "has_table", False) and sh.has_table:
            marcos += [c.text_frame for f in sh.table.rows for c in f.cells]
        for tf in marcos:
            for par in tf.paragraphs:
                for run in par.runs:
                    run.font.name = FUENTE_TIT if sh.name == "Text 2" else FUENTE_TXT


for sl in final:
    _tipografia(sl.shapes)

NOTAS = [
    ("0:00–0:10", "Somos Luis Leiva y Alonso Gutiérrez, del curso Inteligencia Artificial Aplicada. Presentamos un modelo para predecir casos de dengue en Lima con 4 semanas de anticipación."),
    ("0:15–0:45 (30 s)", "PROBLEMA. Explicar cada cifra, sin apurar: 3,474 casos en 13 años, 118,599 en solo 2, y 10,256 en una semana. Lima no es zona endémica, pero el 97.2% de sus casos ocurrió en 2023 y 2024: 118,599 casos en dos años, contra 3,474 en los 13 años anteriores. Se reacciona tarde a los brotes."),
    ("0:45–1:15 (30 s)", "SOLUCIÓN. Señalar cada foto y cada flecha: hoy se predice, antes del brote se fumiga, en la semana +4 los hospitales están listos. Con 4 semanas de aviso se puede fumigar, eliminar criaderos y preparar camas y personal. El modelo predice los casos de dentro de 4 semanas."),
    ("1:15–1:40 (25 s)", "De 937,119 registros individuales de dengue en Perú (2010–2024) nos quedamos con los de Lima, el segundo departamento con más casos del país tras Piura, agrupados en 782 semanas de 81 distritos, y les sumamos clima (NASA POWER) y el ICEN del IGP: cuánto más cálido o frío que lo normal está el mar frente a Perú; en julio de 2023 llegó a +2.9. Resultado: 45 variables por semana. De la literatura tomamos cuatro ideas: el clima actúa con rezago (60% de los 99 modelos de Leung et al., 2023, lo corrige), así que usamos rezagos de 2 a 12 semanas; los modelos simples compiten con los profundos (Mayta-Quispe y Alemán, 2025; Tian et al., 2024), por eso comparamos XGBoost con LSTM, GRU y persistencia; hay que evaluar el pico y no solo el promedio (Hii et al., 2012; Benedum et al., 2020); y casi no hay ML para Lima con El Niño, por eso incluimos el ICEN. Las referencias están en la diapositiva de resultados."),
    ("2:00–2:15 (15 s)", "El 59% de las semanas tuvo cero casos y el pico llegó a 10,256. Por eso trabajamos en logaritmo."),
    ("2:15–2:30 (15 s)", "La temperatura alcanzó su máximo 6 semanas (2023) y 9 semanas (2024) antes que los casos. Solo son dos olas: respalda usar clima rezagado, no prueba causalidad."),
    ("2:30–3:00 (30 s)", "Ablación: quitamos un grupo de variables a la vez. El MAE baja sin ICEN o sin tendencias recientes y sube al quitar clima, estacionalidad o casos de otras regiones. Limitación: el ICEN es el valor definitivo, que se conoce después; sin él el MAE es 68.6 contra 132.8 de la persistencia. El 96.8% del error se concentra en las 77 semanas de brote de 759."),
    ("3:00–4:20 (80 s)", "Predecimos el cambio en el logaritmo de los casos para que los picos no dominen. Primero, qué comparamos: el baseline es la persistencia, que predice repitiendo los casos de hace 4 semanas; el MAE es el error promedio en casos por semana, y menos es mejor. Resultado en Lima 2024. Persistencia: 1,688. Con el mismo protocolo para todos, GRU: 1,065; LSTM: 846; XGBoost base: 985; completo: 793, menos de la mitad. Con solo 43 semanas, la diferencia con LSTM no es significativa. En 2023–2024 el pico llega 2 semanas tarde, contra 4 de la persistencia, con casi la altura real (10,296 contra 10,256), pero por ese retraso en la semana del pico subestima 5,232 casos. En las 759 semanas, MAE 67.0 contra 132.8; el IC 95% excluye 0."),
    ("4:20–5:00 (40 s)", "Conclusiones. Primero, XGBoost reduce el error a la mitad frente a la persistencia. Limitación: usamos el ICEN definitivo, que se conoce después; sin él, el MAE es 68.6, aún 48% menos que la persistencia. Segundo, el efecto de quitar variables depende del grupo: baja sin ICEN o tendencias recientes y sube sin clima, estacionalidad o casos de otras regiones. Tercero, la diferencia con LSTM y GRU no es significativa. Cuarto, el cruce de 500 casos semanales se predice 3 semanas tarde en 2023 y 1 en 2024, contra 4 de la persistencia; probamos 22 variantes y ninguna lo adelantó. Siguientes pasos: operar con los datos tal como se publican cada semana, sumar brotes de zonas endémicas como Junín, emitir una alerta con la probabilidad de superar un umbral, y llevarlo a nivel de distrito. Gracias."),
    ("OCULTA, para preguntas", "Tabla completa: 759 semanas (MAE, WAPE) y 2023–24, para todos los modelos con el mismo walk-forward, universo, variables, objetivo, semillas y búsqueda de hiperparámetros (results/comparacion_justa.csv). LSTM y GRU: tuning aleatorio de 10 configuraciones con validación temporal. GRU es más variable entre semillas (sd 12 casos contra 1.6 de XGBoost). Completo = base + Callao, Ica, La Libertad, Áncash + tendencias recientes. La ablación usa el protocolo original reproducido en Colab (completo 70.5); la tabla común usa el promedio por semilla (67.0). Literatura: ARIMA supera a LSTM en la selva (Mayta-Quispe y Alemán, 2025); XGBoost mejor en Singapur (Tian et al., 2024)."),
    ("OCULTA, para preguntas", "Hiperparámetros XGBoost: búsqueda aleatoria de 30 configuraciones, validación cruzada temporal (2016, 2017, 2020–2022). Error de validación relativo a la persistencia: 0.82 a 0.73 con datos hasta 2022 (para predecir 2023) y 0.82 a 0.74 con datos hasta 2023 (para 2024). Se probaron esos valores por ser rangos habituales de XGBoost; el detalle va en el informe."),
]
NOTAS.insert(4, ("", "Ejemplo real: semana del 17 de marzo de 2024. El modelo ve 5,291 casos, que venían subiendo; la temperatura de 20.6 °C y sus valores de hasta 12 semanas atrás; el ICEN en +0.38; la semana 12 del año; y los casos de otras regiones. Con eso predice los casos de 4 semanas después, el 14 de abril: fueron 10,256, el pico de 2024. Si preguntan por qué estas 45 variables: cada grupo responde a un hallazgo de la literatura (clima rezagado, El Niño, casos regionales, estacionalidad) y la ablación mide el aporte de cada grupo. Si preguntan por PCA: no la usamos porque XGBoost tolera variables correlacionadas y PCA mezclaría las variables, impidiendo medir el aporte de cada grupo en la ablación."))
NOTAS.append(("", "Perfil de los casos de Lima 2023–24: 5 distritos reúnen 40% y 10 distritos 64%; Comas y San Juan de Lurigancho tienen unos 13,000 casos cada uno. 43% tiene entre 30 y 59 años, 53% son mujeres y 92% es dengue sin signos de alarma."))
_orden_n = [pt, S[0], util, dato, anat, S[2], S[1], S[3], gx, S[4], cmp_, hp, perf]
_nota = {id(x): tx for x, (_t, tx) in zip(_orden_n, NOTAS)}
_HORA = ["0:00–0:10", "0:10–0:30", "0:30–0:50", "0:50–1:15", "1:15–1:40", "1:40–4:00",
         "4:00–5:00"] + ["OCULTA, para preguntas"] * 6
for sl, (t, tx) in [(x, (h, _nota[id(x)])) for x, h in zip(final, _HORA)]:
    ns = sl.notes_slide
    if ns.notes_text_frame is None:   # la plantilla no trae placeholder de notas
        from lxml import etree
        xml = ('<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
               'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
               '<p:nvSpPr><p:cNvPr id="9999" name="Notas"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
               '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
               '<p:spPr><a:xfrm><a:off x="685800" y="4400550"/><a:ext cx="5486400" cy="3600450"/></a:xfrm>'
               '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
               '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="es-PE"/></a:p></p:txBody></p:sp>')
        ns.shapes._spTree.append(etree.fromstring(xml))
    ns.notes_text_frame.text = t + chr(10) + tx

prs.core_properties.title = "Predicción de casos de dengue en Lima con 4 semanas de anticipación"
prs.core_properties.subject = "Inteligencia Artificial Aplicada (1INF62), 2026-2"
prs.save(DESTINO)
print("guardado", DESTINO, len(final), "diapositivas")
