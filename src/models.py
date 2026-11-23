"""Modelos: persistencia (baseline), XGBoost tuneado y redes recurrentes (LSTM/GRU).

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
import gc
import json
import os
import time
import warnings

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from evaluation import HORIZONTE, PASOS, a_casos
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


# =============================================================================
# Redes recurrentes (LSTM / GRU)
# =============================================================================
# Ventanas de PASOS semanas de historial (y clima) -> casos de t+HORIZONTE.
# TensorFlow se importa dentro de las funciones: asi importar este modulo (para
# persistencia o XGBoost) no exige ni carga TensorFlow.

LIMA = "LIMA"
PRUEBA_DESDE = pd.Timestamp("2024-01-01")
INICIOS_VALIDACION = pd.to_datetime(["2021-01-01", "2022-01-01", "2023-01-01"])
HISTORIAL = ["log_casos", "log_casos_lag1", "log_casos_lag2",
             "log_casos_lag3", "log_casos_mm4", "sem_sin", "sem_cos"]
UNIDADES, DROPOUT, LOTE = 32, 0.2, 32
EPOCAS_MAX, PACIENCIA, SEMILLA_RNN = 80, 8, 42


def cargar_datos_recurrente(processed):
    """Lee modelado.csv, recupera la fecha objetivo desde la grilla semanal y
    devuelve (df, variables): `variables` = historial + clima (el historial va
    primero, asi las variantes "solo historial" usan las primeras columnas)."""
    df = pd.read_csv(processed / "modelado.csv", parse_dates=["fecha_inicio"])
    grilla = pd.read_csv(
        processed / "departamentos_semanal.csv", parse_dates=["fecha_inicio"],
        usecols=["departamento", "fecha_inicio"],
    ).sort_values(["departamento", "fecha_inicio"])
    grilla["fecha_objetivo"] = grilla.groupby("departamento").fecha_inicio.shift(-HORIZONTE)
    df = df.merge(grilla, on=["departamento", "fecha_inicio"], validate="one_to_one")
    df = df.loc[df.fecha_objetivo.sub(df.fecha_inicio).eq(pd.Timedelta(weeks=HORIZONTE))]
    clima = [c for c in df if c.startswith(("temp_", "precip_", "hum_rel"))
             or c in {"dias_lluvia", "viento"}]
    return df, HISTORIAL + clima


def construir_ventanas(df, variables):
    """Ventanas de PASOS semanas consecutivas por departamento.

    Devuelve (X, y, meta): X (n, PASOS, n_vars), y = objetivo en log(1 + casos)
    y meta con departamento, origen y fecha_objetivo de cada ventana."""
    ventanas, filas = [], []
    for departamento, grupo in df.groupby("departamento"):
        grupo = grupo.sort_values("fecha_inicio")
        if grupo.fecha_inicio.duplicated().any():
            raise ValueError(f"Semanas duplicadas en {departamento}")
        valores = grupo[variables].to_numpy(dtype=np.float32)
        for i in range(PASOS - 1, len(grupo)):
            fila = grupo.iloc[i]
            inicio = i - PASOS + 1
            fechas = grupo.fecha_inicio.iloc[inicio:i + 1]
            if not fechas.diff().iloc[1:].eq(pd.Timedelta(weeks=1)).all():
                continue
            if fila.fecha_objetivo - fila.fecha_inicio != pd.Timedelta(weeks=HORIZONTE):
                raise ValueError("La etiqueta no corresponde a t+4")
            ventana = valores[inicio:i + 1]
            if not np.isfinite(ventana).all() or not np.isfinite(fila.objetivo):
                raise ValueError(f"Valor no finito en {departamento}, {fila.fecha_inicio}")
            ventanas.append(ventana)
            filas.append((departamento, fila.fecha_inicio, fila.fecha_objetivo, fila.objetivo))
    meta = pd.DataFrame(filas, columns=["departamento", "origen", "fecha_objetivo", "objetivo"])
    return np.stack(ventanas), meta.objetivo.to_numpy(dtype=np.float32), meta


def particion(meta, desde, hasta=None):
    """Mascaras (train, evalua): se entrena con etiquetas anteriores a `desde`
    y se evalua en Lima con origenes desde `desde` (y objetivo antes de `hasta`)."""
    train = meta.fecha_objetivo.lt(desde)
    evalua = meta.departamento.eq(LIMA) & meta.origen.ge(desde)
    if hasta is not None:
        evalua &= meta.fecha_objetivo.lt(hasta)
    if not train.any() or not evalua.any():
        raise ValueError(f"Particion vacia desde {desde:%Y-%m-%d}")
    assert meta.loc[train, "fecha_objetivo"].max() < meta.loc[evalua, "origen"].min()
    return train.to_numpy(), evalua.to_numpy()


def escalar(X, train, evalua, n_variables):
    """Estandariza con media y desvio del entrenamiento (sin mirar el futuro)."""
    from sklearn.preprocessing import StandardScaler
    x_train = X[train, :, :n_variables]
    x_eval = X[evalua, :, :n_variables]
    scaler = StandardScaler().fit(x_train.reshape(-1, n_variables))

    def transformar(x):
        return scaler.transform(x.reshape(-1, n_variables)).reshape(x.shape)

    return transformar(x_train), transformar(x_eval)


def configuraciones_recurrente(n_historial, n_variables):
    """{nombre: (familia, solo_lima, n_variables)} para LSTM y GRU."""
    entradas = {
        "Lima, historial": (True, n_historial),
        "Lima, historial y clima": (True, n_variables),
        "regional, historial y clima": (False, n_variables),
    }
    return {f"{familia} {nombre}": (familia, solo_lima, n)
            for familia in ("LSTM", "GRU")
            for nombre, (solo_lima, n) in entradas.items()}


def modelo_recurrente(familia, n_variables):
    """Una capa recurrente (LSTM o GRU) + Dropout + Dense(1), Adam y MSE."""
    import tensorflow as tf
    capa = {"LSTM": tf.keras.layers.LSTM, "GRU": tf.keras.layers.GRU}[familia]
    modelo = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(PASOS, n_variables)),
        capa(UNIDADES),
        tf.keras.layers.Dropout(DROPOUT),
        tf.keras.layers.Dense(1),
    ])
    modelo.compile(optimizer="adam", loss="mse")
    return modelo


def ajustar_recurrente(X, y, meta, train, evalua, config, epocas=None):
    """Entrena y predice (en casos) los origenes `evalua`.

    Sin `epocas`: parada temprana por MAE en casos sobre `evalua` (validacion).
    Con `epocas`: entrena ese numero fijo (prueba final, sin mirar `evalua`).
    Devuelve (prediccion en casos, mejor epoca)."""
    import tensorflow as tf
    familia, solo_lima, n_variables = config
    if solo_lima:
        train = train & meta.departamento.eq(LIMA).to_numpy()
    x_train, x_eval = escalar(X, train, evalua, n_variables)
    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(SEMILLA_RNN)
    modelo = modelo_recurrente(familia, n_variables)

    class MAEEnCasos(tf.keras.callbacks.Callback):
        def __init__(self, x_val, reales):
            super().__init__()
            self.x_val, self.reales = x_val, reales

        def on_epoch_end(self, epoch, logs=None):
            pred = a_casos(self.model(self.x_val, training=False).numpy().ravel())
            logs["val_mae_casos"] = float(np.abs(pred - self.reales).mean())

    opciones = {}
    if epocas is None:
        opciones = {
            "validation_data": (x_eval, y[evalua]),
            "callbacks": [
                MAEEnCasos(x_eval, a_casos(y[evalua])),
                tf.keras.callbacks.EarlyStopping(
                    monitor="val_mae_casos", mode="min", patience=PACIENCIA,
                    restore_best_weights=True),
            ],
        }
    ajuste = modelo.fit(x_train, y[train], epochs=epocas or EPOCAS_MAX, batch_size=LOTE,
                        shuffle=False, verbose=0, **opciones)
    mejor_epoca = epocas or int(np.argmin(ajuste.history["val_mae_casos"])) + 1
    return a_casos(modelo.predict(x_eval, verbose=0).ravel()), mejor_epoca


# =============================================================================
# LSTM / GRU en el MISMO protocolo que XGBoost (comparacion justa)
# =============================================================================
# Misma prueba (semanas de Lima), mismo walk-forward (reentreno cada BLOQUE
# semanas con filas cuyo objetivo ya se conocia), mismo universo de
# entrenamiento, mismas variables, mismo objetivo (`delta`), mismas semillas y
# misma busqueda de hiperparametros (aleatoria, CV temporal). La red ve las
# ultimas PASOS semanas de las mismas columnas que XGBoost ve en la semana t.

ESPACIO_RNN = dict(unidades=[16, 32, 64], dropout=[0.1, 0.2, 0.3],
                   lr=[0.001, 0.003, 0.01], epocas=[10, 20, 40])
DEFECTO_RNN = dict(unidades=32, dropout=0.2, lr=0.001, epocas=20)
N_BUSQUEDA_RNN = 10


def ventanas_rnn(m, cols):
    """X (n, PASOS, len(cols)) alineado con las filas de `m` (ordenado por
    departamento y fecha, indice 0..n-1) y `valida` (ventana de PASOS semanas
    consecutivas del mismo departamento y sin valores no finitos).
    Las ventanas invalidas quedan en NaN."""
    assert m.index.equals(pd.RangeIndex(len(m))), "m debe tener indice 0..n-1"
    X = np.full((len(m), PASOS, len(cols)), np.nan, dtype=np.float32)
    valida = np.zeros(len(m), dtype=bool)
    valores = m[cols].to_numpy(dtype=np.float32)
    fechas = m["fecha_inicio"].to_numpy()
    for _, pos in m.groupby("departamento").indices.items():
        for k in range(PASOS - 1, len(pos)):
            idx = pos[k - PASOS + 1:k + 1]
            if (fechas[idx[-1]] - fechas[idx[0]]) != np.timedelta64(7 * (PASOS - 1), "D"):
                continue
            X[pos[k]] = valores[idx]
            valida[pos[k]] = np.isfinite(valores[idx]).all()
    return X, valida


def ajustar_predecir_rnn(familia, params, X, y, tr, te, semilla):
    """Entrena una capa LSTM/GRU sobre `delta` con las filas `tr` y devuelve el
    delta predicho (en log) para las filas `te`. Epocas fijas (sin mirar `te`)."""
    import tensorflow as tf
    from sklearn.preprocessing import StandardScaler
    k = X.shape[2]
    sc = StandardScaler().fit(X[tr].reshape(-1, k))

    def esc(x):  # NaN -> 0 (la media del entrenamiento): solo aparece en filas de prueba tempranas
        return np.nan_to_num(sc.transform(x.reshape(-1, k)).reshape(x.shape))

    capa = {"LSTM": tf.keras.layers.LSTM, "GRU": tf.keras.layers.GRU}[familia]
    tf.keras.backend.clear_session()
    tf.keras.utils.set_random_seed(semilla)
    modelo = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(PASOS, k)),
        capa(params["unidades"]),
        tf.keras.layers.Dropout(params["dropout"]),
        tf.keras.layers.Dense(1),
    ])
    modelo.compile(optimizer=tf.keras.optimizers.Adam(params["lr"]), loss="mse")
    modelo.fit(esc(X[tr]), y[tr], epochs=params["epocas"], batch_size=LOTE,
               shuffle=False, verbose=0)
    pred = modelo.predict(esc(X[te]), verbose=0).ravel()
    del modelo
    tf.keras.backend.clear_session()
    gc.collect()  # evita acumular memoria en cientos de reentrenos seguidos
    return pred


def puntaje_cv_rnn(familia, m, X, valida, params, anios, corte, semilla=SEMILLA_BUSQUEDA):
    """Igual que puntaje_cv (XGBoost): MAE relativo a la persistencia por anio."""
    y = m["delta"].to_numpy(dtype=np.float32)
    rel = []
    for Y in anios:
        ini, fin = pd.Timestamp(f"{Y}-01-01"), pd.Timestamp(f"{Y + 1}-01-01")
        tr_m = (m["fecha_obj"] < ini).to_numpy()
        va = ((m["fecha_inicio"] >= ini) & (m["fecha_inicio"] < fin)
              & (m["fecha_obj"] <= corte)).to_numpy()
        if tr_m.sum() < MIN_TRAIN or not va.any():
            continue
        real = a_casos(m.loc[va, "objetivo"].to_numpy())
        base = np.abs(real - a_casos(m.loc[va, "log_casos"].to_numpy())).mean()
        if base == 0:
            continue
        tr = tr_m & valida & ~np.isnan(y)
        delta = ajustar_predecir_rnn(familia, params, X, y, tr, va, semilla)
        pred = a_casos(np.maximum(m.loc[va, "log_casos"].to_numpy() + delta, 0))
        rel.append(np.abs(real - pred).mean() / base)
    return float(np.mean(rel)) if rel else np.inf


def buscar_rnn(familia, m, X, valida):
    """Busqueda aleatoria (N_BUSQUEDA_RNN configs) por corte, como `buscar`.
    Devuelve mejores[corte] = {params, cv, cv_defecto}. Si nada supera al
    defecto se conserva el defecto."""
    rng = np.random.default_rng(SEMILLA_BUSQUEDA)
    configs = muestrear(ESPACIO_RNN, N_BUSQUEDA_RNN, rng)
    mejores = {}
    for corte_nombre, corte in CORTES.items():
        anios = ANIOS_VAL[corte_nombre]
        t0 = time.time()
        cv_def = puntaje_cv_rnn(familia, m, X, valida, DEFECTO_RNN, anios, corte)
        mejor = (np.inf, None)
        for params in configs:
            s = puntaje_cv_rnn(familia, m, X, valida, params, anios, corte)
            if s < mejor[0]:
                mejor = (s, params)
        if mejor[0] >= cv_def:
            mejor = (cv_def, DEFECTO_RNN)
        mejores[corte_nombre] = {"params": mejor[1], "cv": round(mejor[0], 4),
                                 "cv_defecto": round(cv_def, 4)}
        print(f"{familia} corte {corte_nombre}: CV defecto {cv_def:.3f} -> mejor "
              f"{mejor[0]:.3f} [{time.time() - t0:.0f}s]", flush=True)
    return mejores


def walk_forward_rnn(familia, m, X, valida, test_idx, mejores, semilla):
    """Igual que `walk_forward`: prediccion (log) para `test_idx`; cada bloque
    reentrena con filas cuyo objetivo ya se conocia y usa los hiperparametros
    disponibles en su fecha (defecto antes de 2023)."""
    y = m["delta"].to_numpy(dtype=np.float32)
    prueba = m.loc[test_idx]
    fechas = prueba["fecha_inicio"]
    pred = np.empty(len(prueba))
    orden = sorted(fechas.unique())
    for ini in range(0, len(orden), BLOQUE):
        bloque_f = orden[ini:ini + BLOQUE]
        corte = bloque_f[0]
        sel = fechas.isin(bloque_f).to_numpy()
        tr_m = (m["fecha_obj"] <= corte).to_numpy()
        if tr_m.sum() < MIN_TRAIN:
            pred[sel] = 0.0
            continue
        if corte < pd.Timestamp("2023-01-01"):
            params = DEFECTO_RNN
        elif corte < pd.Timestamp("2024-01-01"):
            params = mejores["2022"]["params"]
        else:
            params = mejores["2023"]["params"]
        te = np.zeros(len(m), dtype=bool)
        te[prueba.index[sel]] = True
        tr = tr_m & valida & ~np.isnan(y)
        pred[sel] = ajustar_predecir_rnn(familia, params, X, y, tr, te, semilla)
    return np.maximum(prueba["log_casos"].to_numpy() + pred, 0)
