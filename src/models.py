"""Modelos: persistencia (baseline) y XGBoost tuneado.

- Persistencia: predecir que dentro de 4 semanas habra los mismos casos que
  esta semana. Cualquier modelo debe superarla para justificar su complejidad.
- XGBoost: no predice el nivel sino el cambio `delta = objetivo - log_casos`
  (en log). Asi no depende de la escala de cada departamento y "no cambia
  nada" equivale a la persistencia.

Tuning y prueba sin filtrar el futuro
-------------------------------------
- La busqueda usa validacion cruzada temporal (ventana creciente): para cada
  anio de validacion Y se entrena con filas cuyo objetivo se conocia antes del
  1-ene-Y y se evalua en Y (anios 2016, 2017, 2020, 2021, 2022[, 2023]).
  Puntaje = MAE relativo a la persistencia, promedio entre anios.
- Dos busquedas (cortes 2022 y 2023), cada una solo con datos de su epoca.
- Walk-forward en la prueba: cada 13 semanas se reentrena con filas cuyo
  objetivo ya se conocia, con los hiperparametros que existian en esa fecha
  (defecto antes de 2023, corte 2022 durante 2023, corte 2023 durante 2024).

OJO: XGBoost no da el mismo resultado con distinto numero de hilos
(N_JOBS). Compara siempre corridas con el mismo N_JOBS (por defecto 1).
"""
import json
import os
import time
import warnings

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from evaluation import a_casos
from preprocessing import FEATURES

BLOQUE = 13          # semanas entre reentrenamientos (walk-forward)
MIN_TRAIN = 300      # filas minimas para reentrenar (si no, persistencia)
SEMILLA_BUSQUEDA = 42
SEMILLAS = [42, 43, 44]
N_BUSQUEDA = 30
N_JOBS = int(os.environ.get("N_JOBS", "1"))

ANIOS_VAL = {"2022": [2016, 2017, 2020, 2021, 2022],
             "2023": [2016, 2017, 2020, 2021, 2022, 2023]}
CORTES = {"2022": pd.Timestamp("2022-12-31"), "2023": pd.Timestamp("2023-12-31")}
DEFECTO = dict(n_estimators=300, max_depth=3, learning_rate=0.05,
               subsample=0.8, colsample_bytree=0.8)
ESPACIO = dict(n_estimators=[100, 200, 400, 600], max_depth=[2, 3, 4, 6],
               learning_rate=[0.01, 0.02, 0.05, 0.1], subsample=[0.6, 0.8, 1.0],
               colsample_bytree=[0.5, 0.8, 1.0], min_child_weight=[1, 5, 10, 20],
               reg_lambda=[1, 5, 10, 30])


class PersistenceBaseline:
    """Predice `objetivo` (log(1 + casos) en t+4) repitiendo `log_casos` en t."""

    def __init__(self, columna="log_casos"):
        self.columna = columna

    def fit(self, X=None, y=None):
        return self  # no aprende nada: es una regla fija

    def predict(self, X):
        return np.asarray(X[self.columna], dtype=float)


def build_baseline():
    """Devuelve el baseline de persistencia."""
    return PersistenceBaseline()


def ajustar_predecir(params, cols, train, test, semilla=SEMILLA_BUSQUEDA):
    """Ajusta XGBoost sobre `delta` y devuelve el delta predicho (en log)."""
    train = train.dropna(subset=["delta"])
    modelo = XGBRegressor(random_state=semilla, n_jobs=N_JOBS, **params)
    return modelo.fit(train[cols], train["delta"]).predict(test[cols])


def puntaje_cv(m, params, anios, corte, cols=FEATURES):
    """MAE relativo a la persistencia, promedio entre anios de validacion."""
    rel = []
    for Y in anios:
        ini, fin = pd.Timestamp(f"{Y}-01-01"), pd.Timestamp(f"{Y + 1}-01-01")
        tr = m[m["fecha_obj"] < ini]
        va = m[(m["fecha_inicio"] >= ini) & (m["fecha_inicio"] < fin) & (m["fecha_obj"] <= corte)]
        if len(tr) < MIN_TRAIN or va.empty:
            continue
        real = a_casos(va["objetivo"].to_numpy())
        base = np.abs(real - a_casos(va["log_casos"].to_numpy())).mean()
        if base == 0:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            delta = ajustar_predecir(params, cols, tr, va)
        pred = a_casos(np.maximum(va["log_casos"].to_numpy() + delta, 0))
        rel.append(np.abs(real - pred).mean() / base)
    return float(np.mean(rel)) if rel else np.inf


def muestrear(espacio, n, rng):
    """n configuraciones aleatorias distintas del espacio de busqueda."""
    vistos, out = set(), []
    while len(out) < n:
        c = {k: v[rng.integers(len(v))] for k, v in espacio.items()}
        c = {k: (v.item() if hasattr(v, "item") else v) for k, v in c.items()}
        clave = json.dumps(c, sort_keys=True)
        if clave not in vistos:
            vistos.add(clave)
            out.append(c)
    return out


def buscar(m, cols=FEATURES):
    """Busqueda aleatoria por corte. Devuelve (mejores, tabla_cv); si nada supera
    a los valores por defecto se conservan.
    mejores[corte]["XGBoost"] = {params, cv, cv_defecto}."""
    rng = np.random.default_rng(SEMILLA_BUSQUEDA)
    mejores, filas = {}, []
    for corte_nombre, corte in CORTES.items():
        anios = ANIOS_VAL[corte_nombre]
        t0 = time.time()
        cv_def = puntaje_cv(m, DEFECTO, anios, corte, cols)
        mejor = (np.inf, None)
        for i, params in enumerate(muestrear(ESPACIO, N_BUSQUEDA, rng)):
            s = puntaje_cv(m, params, anios, corte, cols)
            filas.append((corte_nombre, f"cfg{i}", json.dumps(params), round(s, 4)))
            if s < mejor[0]:
                mejor = (s, params)
        if mejor[0] >= cv_def:
            mejor = (cv_def, DEFECTO)
        mejores[corte_nombre] = {"XGBoost": {"params": mejor[1], "cv": round(mejor[0], 4),
                                             "cv_defecto": round(cv_def, 4)}}
        print(f"corte {corte_nombre}: CV defecto {cv_def:.3f} -> mejor {mejor[0]:.3f} "
              f"[{time.time() - t0:.0f}s]", flush=True)
    tabla = pd.DataFrame(filas, columns=["corte", "config", "params", "cv_rel_persistencia"])
    return mejores, tabla


def walk_forward(m, test_idx, mejores, semilla, cols=FEATURES):
    """Prediccion (log) para las filas `test_idx`; cada bloque usa los
    hiperparametros disponibles en su fecha. `cols` define las variables."""
    prueba = m.loc[test_idx]
    fechas = prueba["fecha_inicio"]
    pred = np.empty(len(prueba))
    orden = sorted(fechas.unique())   # bloques de BLOQUE semanas (sirve con varios deptos)
    for ini in range(0, len(orden), BLOQUE):
        bloque_f = orden[ini:ini + BLOQUE]
        corte = bloque_f[0]
        sel = fechas.isin(bloque_f).to_numpy()
        bloque = prueba[sel]
        tr = m[m["fecha_obj"] <= corte]
        if len(tr) < MIN_TRAIN:
            pred[sel] = 0.0
            continue
        if corte < pd.Timestamp("2023-01-01"):
            params = DEFECTO
        elif corte < pd.Timestamp("2024-01-01"):
            params = mejores["2022"]["XGBoost"]["params"]
        else:
            params = mejores["2023"]["XGBoost"]["params"]
        pred[sel] = ajustar_predecir(params, cols, tr, bloque, semilla)
    return np.maximum(prueba["log_casos"].to_numpy() + pred, 0)
