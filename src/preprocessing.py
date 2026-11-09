"""Preparacion de datos: dengue semanal en Lima (departamento) y clima.

Uso:
    python src/preprocessing.py

Lee los CSV de data/raw/ y escribe tablas pequenas en data/processed/.
"""
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from epiweeks import Week

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

ANIO_INI, ANIO_FIN = 2010, 2024  # el clima empieza en 2010
DEPARTAMENTO = "LIMA"
# Lima + departamentos con clima parecido (ver EDA, seccion 8)
DEPARTAMENTOS_MODELO = ["LIMA", "ICA", "LA LIBERTAD", "ANCASH", "CALLAO"]
HORIZONTE = 4  # semanas hacia adelante que se predicen

CLIMA_BASE = ["temp_media", "temp_max", "temp_min", "precip_total",
              "precip_max_d", "dias_lluvia", "hum_rel", "viento"]
CLIMA_LAGS = [f"{v}_lag{k}" for v in ("temp_media", "precip_total", "hum_rel")
              for k in (2, 4, 6, 8)]
CLIMA_COLS = CLIMA_BASE + CLIMA_LAGS


def clean_data(df):
    """Copia del DataFrame con tipos basicos corregidos.

    No se eliminan filas duplicadas: cada fila es un caso y no hay
    identificador de paciente, asi que dos casos distintos pueden ser identicos.
    """
    cleaned = df.copy()
    if "ubigeo" in cleaned.columns:
        cleaned["ubigeo"] = cleaned["ubigeo"].astype(str).str.zfill(6)
    return cleaned


def load_vigilancia(raw_dir=RAW):
    cols = ["departamento", "provincia", "distrito", "localidad", "ano",
            "semana", "ubigeo", "enfermedad"]
    df = pd.read_csv(raw_dir / "datos_abiertos_vigilancia_dengue_2000_2024.csv",
                     sep=";", encoding="utf-8-sig", usecols=cols,
                     dtype={"ubigeo": str}, low_memory=False)
    return clean_data(df)


def semanas_por_anio(df):
    """Semana epidemiologica maxima observada por anio (52 o 53)."""
    return df.groupby("ano").semana.max().to_dict()


def grilla_semanas(max_sem, desde=ANIO_INI, hasta=ANIO_FIN):
    """Todas las (ano, semana) del rango, con fecha de inicio (domingo CDC)."""
    filas = []
    for ano in range(desde, hasta + 1):
        for sem in range(1, int(max_sem[ano]) + 1):
            filas.append((ano, sem, Week(ano, sem, system="cdc").startdate()))
    g = pd.DataFrame(filas, columns=["ano", "semana", "fecha_inicio"])
    g["fecha_inicio"] = pd.to_datetime(g["fecha_inicio"])
    return g


def casos_semanales(df, grilla, departamento=None):
    """Casos por semana; las semanas sin filas se rellenan con 0."""
    d = df[df.ano.between(ANIO_INI, ANIO_FIN)]
    if departamento is not None:
        d = d[d.departamento == departamento]
    c = d.groupby(["ano", "semana"]).size().rename("casos").reset_index()
    out = grilla.merge(c, on=["ano", "semana"], how="left")
    out["casos"] = out["casos"].fillna(0).astype(int)
    return out


def casos_semanales_departamentos(df, grilla):
    d = df[df.ano.between(ANIO_INI, ANIO_FIN)]
    c = d.groupby(["departamento", "ano", "semana"]).size().rename("casos")
    deptos = sorted(d.departamento.unique())
    base = pd.MultiIndex.from_product(
        [deptos, grilla.index], names=["departamento", "i"]).to_frame(index=False)
    base[["ano", "semana", "fecha_inicio"]] = grilla.loc[
        base.i, ["ano", "semana", "fecha_inicio"]].values
    out = base.drop(columns="i").merge(
        c.reset_index(), on=["departamento", "ano", "semana"], how="left")
    out["casos"] = out["casos"].fillna(0).astype(int)
    # .values arriba mezcla tipos y deja columnas object
    out = out.astype({"ano": int, "semana": int})
    out["fecha_inicio"] = pd.to_datetime(out["fecha_inicio"])
    return out


def _promedio_ponderado(df, cols, pesos, claves):
    """Promedio ponderado por pesos que ignora NaN en cada columna."""
    res = {}
    grupos = [df[k] for k in claves]
    for c in cols:
        ok = df[c].notna()
        num = (df[c].where(ok, 0) * df[pesos]).groupby(grupos).sum()
        den = df[pesos].where(ok, 0).groupby(grupos).sum()
        res[c] = num / den.replace(0, np.nan)
    return pd.DataFrame(res).reset_index()


def clima_departamento(df_vig, mapa, clima, departamento):
    """Clima semanal del departamento: promedio de sus celdas, ponderado por
    el numero de distritos del departamento que cae en cada celda."""
    ubigeos = df_vig.loc[df_vig.departamento == departamento, "ubigeo"].unique()
    peso = (mapa[mapa.ubigeo.isin(ubigeos)].celda_grilla.value_counts()
            .rename_axis("celda_grilla").rename("peso").reset_index())
    c = clima.merge(peso, on="celda_grilla")
    return _promedio_ponderado(c, CLIMA_COLS, "peso", ["ano", "semana"])


def icen_semanal(grilla, icen):
    """ICEN mensual asignado a cada semana por el mes de su miercoles."""
    g = grilla.copy()
    miercoles = g.fecha_inicio + timedelta(days=3)
    g["ano_cal"], g["mes"] = miercoles.dt.year, miercoles.dt.month
    m = icen[["ano", "mes", "icen"]].rename(columns={"ano": "ano_cal"})
    return g.merge(m, on=["ano_cal", "mes"], how="left")[["ano", "semana", "icen"]]


def climatologia_departamentos(df_vig, mapa, clima):
    """Clima promedio 2010-2024 por departamento (para comparar con Lima)."""
    ubi = df_vig[["ubigeo", "departamento"]].drop_duplicates()
    m = mapa[["ubigeo", "celda_grilla"]].merge(ubi, on="ubigeo")
    peso = (m.groupby(["departamento", "celda_grilla"]).size()
            .rename("peso").reset_index())
    vars_ = ["temp_media", "temp_max", "precip_total", "hum_rel"]
    medias = clima.groupby("celda_grilla")[vars_].mean().reset_index()
    j = peso.merge(medias, on="celda_grilla")
    out = _promedio_ponderado(j, vars_, "peso", ["departamento"])
    out["n_distritos"] = out.departamento.map(
        m.groupby("departamento").ubigeo.nunique())
    return out


def dataset_modelado(casos_deptos, clima_por_depto, icen, horizonte=HORIZONTE):
    """Tabla de modelado: una fila por (departamento, semana t).

    Features con informacion hasta t; `objetivo` = log1p(casos en t+horizonte).
    Se eliminan las filas sin lags de clima (8 primeras semanas de 2010, 1 % de
    las filas) y las ultimas `horizonte` semanas de cada departamento (sin
    objetivo). No se parte en train/val/test aqui: eso se hace en el notebook
    con train_test_split, como en los laboratorios.
    """
    partes = []
    for depto, clima in clima_por_depto.items():
        d = (casos_deptos[casos_deptos.departamento == depto]
             .sort_values("fecha_inicio").reset_index(drop=True))
        d = d.merge(clima, on=["ano", "semana"], how="left")
        d["log_casos"] = np.log1p(d.casos)
        for k in (1, 2, 3):
            d[f"log_casos_lag{k}"] = d.log_casos.shift(k)
        d["log_casos_mm4"] = d.log_casos.rolling(4).mean()
        d["objetivo"] = d.log_casos.shift(-horizonte)
        partes.append(d.drop(columns="casos"))
    m = pd.concat(partes, ignore_index=True)
    m = m.merge(icen, on=["ano", "semana"], how="left")

    # calendario: la semana del anio como ciclo (la 52 queda cerca de la 1)
    ang = 2 * np.pi * m.semana / 52
    m["sem_sin"], m["sem_cos"] = np.sin(ang), np.cos(ang)

    m = m.dropna(subset=CLIMA_COLS + ["log_casos_lag3", "log_casos_mm4", "objetivo"])
    columnas = [c for c in m.columns if c != "objetivo"] + ["objetivo"]
    return m[columnas].reset_index(drop=True)


def calidad(raw_dir=RAW):
    """Metricas de calidad de la vigilancia (sobre el archivo completo)."""
    d = pd.read_csv(raw_dir / "datos_abiertos_vigilancia_dengue_2000_2024.csv",
                    sep=";", encoding="utf-8-sig", dtype={"ubigeo": str},
                    low_memory=False)
    d = d[d.ano.between(ANIO_INI, ANIO_FIN)]
    lima = d[d.departamento == DEPARTAMENTO]
    return pd.DataFrame([
        ("filas_2010_2024", len(d)),
        ("pct_filas_duplicadas", round(d.duplicated().mean() * 100, 1)),
        ("pct_localidad_nula", round(d.localidad.isna().mean() * 100, 1)),
        ("pct_ubigeo_nulo", round(d.ubigeo.isna().mean() * 100, 1)),
        ("filas_lima", len(lima)),
        ("pct_duplicadas_lima", round(lima.duplicated().mean() * 100, 1)),
        ("distritos_lima", lima.ubigeo.nunique()),
        # validez (reglas de dominio) y consistencia, solo Lima
        ("pct_localidad_nula_lima", round(lima.localidad.isna().mean() * 100, 1)),
        ("semana_fuera_1_53_lima", int((~lima.semana.between(1, 53)).sum())),
        ("ubigeo_no_6_digitos_lima", int((lima.ubigeo.str.len() != 6).sum())),
        ("ubigeo_no_15_lima", int((~lima.ubigeo.str.startswith("15")).sum())),
        ("edad_anios_mayor_100_lima",
         int(((lima.tipo_edad == "A") & (lima.edad > 100)).sum())),
        ("edad_meses_mayor_11_lima",
         int(((lima.tipo_edad == "M") & (lima.edad > 11)).sum())),
    ], columns=["metrica", "valor"])


# --- Tabla de modelado de XGBoost (variables adicionales) --------------------

AMPLIADO = PROCESSED / "modelado_ampliado.csv"
UMBRAL_BROTE = 50        # una semana "con brote" tiene mas de 50 casos
MIN_SEMANAS_BROTE = 40   # y el departamento debe tener >= 40 antes de 2023

CASOS = ["log_casos", "log_casos_lag1", "log_casos_lag2", "log_casos_lag3",
         "log_casos_mm4", "crecimiento"]
EXT = [f"{v}_lag{k}" for v in ("temp_media", "precip_total", "hum_rel")
       for k in (10, 12)]
FEATURES = CLIMA_COLS + EXT + CASOS + ["icen"] + ["sem_sin", "sem_cos"]
# casos de los OTROS departamentos (alerta temprana regional)
REG = ["reg_log", "reg_crec", "reg_max"]
# variables dinamicas nuevas (todas usan solo informacion disponible en t)
NUEVAS = ["acum13", "acum52", "acel", "anom52", "reg_lag2", "reg_crec1", "temp_anom"]


def elegir_departamentos(casos_deptos):
    """Departamentos del modelo + los que tuvieron brotes antes de 2023.

    Regla fijada antes de ver resultados: solo usa datos previos a la prueba."""
    antes = casos_deptos[casos_deptos.fecha_inicio < "2023-01-01"]
    semanas = antes[antes.casos > UMBRAL_BROTE].groupby("departamento").size()
    nuevos = sorted(semanas[semanas >= MIN_SEMANAS_BROTE].index)
    return list(DEPARTAMENTOS_MODELO) + [d for d in nuevos if d not in DEPARTAMENTOS_MODELO]


def generar_ampliado():
    """Escribe data/processed/modelado_ampliado.csv (18 departamentos)."""
    casos = pd.read_csv(PROCESSED / "departamentos_semanal.csv", parse_dates=["fecha_inicio"])
    deptos = elegir_departamentos(casos)
    vig = load_vigilancia()
    mapa = pd.read_csv(RAW / "mapa_ubigeo_celda.csv", dtype={"ubigeo": str})
    clima = pd.read_csv(RAW / "clima_celda_semana.csv")
    icen = pd.read_csv(RAW / "icen_mensual.csv")
    grilla = grilla_semanas(semanas_por_anio(vig))
    clima_deptos = {d: clima_departamento(vig, mapa, clima, d) for d in deptos}
    modelado = dataset_modelado(casos, clima_deptos, icen_semanal(grilla, icen))
    modelado.to_csv(AMPLIADO, index=False)
    return modelado


def cargar(ruta=None):
    """Tabla de modelado + rezagos largos (10, 12 sem), crecimiento y `delta`.

    `delta = objetivo - log_casos` es lo que predicen los modelos: el cambio
    en log, asi no dependen de la escala de cada departamento."""
    m = pd.read_csv(ruta or PROCESSED / "modelado.csv", parse_dates=["fecha_inicio"])
    m = m.sort_values(["departamento", "fecha_inicio"]).reset_index(drop=True)
    g = m.groupby("departamento")
    for v in ("temp_media", "precip_total", "hum_rel"):
        for k in (10, 12):
            m[f"{v}_lag{k}"] = g[v].shift(k)
    m["crecimiento"] = m["log_casos"] - m["log_casos_lag3"]
    m["delta"] = m["objetivo"] - m["log_casos"]
    m["fecha_obj"] = m["fecha_inicio"] + pd.Timedelta(weeks=HORIZONTE)  # cuando se conoce
    return m


def agregar_regional(m):
    """reg_log / reg_max / reg_crec: promedio, maximo y crecimiento (3 sem) de
    log(1 + casos) de los DEMAS departamentos (nunca el propio)."""
    piv = m.pivot(index="fecha_inicio", columns="departamento", values="log_casos")
    partes = []
    for dep in piv.columns:
        otros = piv.drop(columns=dep)
        r = pd.DataFrame({"reg_log": otros.mean(axis=1), "reg_max": otros.max(axis=1)})
        r["reg_crec"] = r["reg_log"] - r["reg_log"].shift(3)
        r["departamento"] = dep
        partes.append(r.reset_index())
    out = m.merge(pd.concat(partes, ignore_index=True), on=["departamento", "fecha_inicio"],
                  how="left", validate="1:1")
    out[REG] = out[REG].fillna(0)
    return out


def nuevas_variables(m):
    """acum13/acum52: casos acumulados (log); acel: aceleracion; anom52: nivel
    vs. promedio de 52 sem; reg_lag2/reg_crec1: dinamica regional;
    temp_anom: temperatura vs. su promedio de 52 sem. Requiere `agregar_regional`."""
    m = m.sort_values(["departamento", "fecha_inicio"]).copy()
    g = m.groupby("departamento", sort=False)
    m["_c"] = np.expm1(m["log_casos"])
    gc = m.groupby("departamento", sort=False)["_c"]
    m["acum13"] = np.log1p(gc.transform(lambda s: s.rolling(13, min_periods=4).sum()))
    m["acum52"] = np.log1p(gc.transform(lambda s: s.rolling(52, min_periods=13).sum()))
    m["acel"] = m["crecimiento"] - (m["log_casos_lag3"] - g["log_casos"].shift(6))
    m["anom52"] = m["log_casos"] - g["log_casos"].transform(
        lambda s: s.rolling(52, min_periods=13).mean())
    m["reg_lag2"] = g["reg_log"].shift(2)
    m["reg_crec1"] = m["reg_log"] - g["reg_log"].shift(1)
    m["temp_anom"] = m["temp_media"] - g["temp_media"].transform(
        lambda s: s.rolling(52, min_periods=13).mean())
    m[NUEVAS] = m[NUEVAS].fillna(0)
    return m.drop(columns="_c").sort_index()


def preparar(departamentos=None, ruta=AMPLIADO):
    """Tabla lista para XGBoost: base + regionales + nuevas.

    `departamentos`: universo de entrenamiento (p. ej. DEPARTAMENTOS_MODELO).
    Las variables regionales resumen a los otros departamentos de ese universo."""
    m = cargar(ruta)
    if departamentos is not None:
        m = m[m.departamento.isin(departamentos)].reset_index(drop=True)
    return nuevas_variables(agregar_regional(m)).sort_values(
        ["departamento", "fecha_inicio"]).reset_index(drop=True)


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    vig = load_vigilancia()
    mapa = pd.read_csv(RAW / "mapa_ubigeo_celda.csv", dtype={"ubigeo": str})
    clima = pd.read_csv(RAW / "clima_celda_semana.csv")
    icen = pd.read_csv(RAW / "icen_mensual.csv")

    grilla = grilla_semanas(semanas_por_anio(vig))

    lima = casos_semanales(vig, grilla, DEPARTAMENTO)
    lima = (lima.merge(clima_departamento(vig, mapa, clima, DEPARTAMENTO),
                       on=["ano", "semana"], how="left")
                .merge(icen_semanal(grilla, icen), on=["ano", "semana"], how="left"))
    lima.to_csv(PROCESSED / "lima_semanal.csv", index=False)

    casos_deptos = casos_semanales_departamentos(vig, grilla)
    casos_deptos.to_csv(PROCESSED / "departamentos_semanal.csv", index=False)

    clima_deptos = {d: clima_departamento(vig, mapa, clima, d)
                    for d in DEPARTAMENTOS_MODELO}
    modelado = dataset_modelado(casos_deptos, clima_deptos,
                                icen_semanal(grilla, icen))
    modelado.to_csv(PROCESSED / "modelado.csv", index=False)
    print("modelado:", modelado.shape)
    climatologia_departamentos(vig, mapa, clima).to_csv(
        PROCESSED / "clima_departamentos.csv", index=False)
    calidad().to_csv(PROCESSED / "calidad_vigilancia.csv", index=False)

    print("lima_semanal:", lima.shape, "| casos totales:", lima.casos.sum())
    print("NaN por columna (solo las que tienen):")
    print(lima.isna().sum().loc[lambda s: s > 0].to_string())


if __name__ == "__main__":
    main()
