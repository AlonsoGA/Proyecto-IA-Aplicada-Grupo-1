"""Metricas de evaluacion para la prediccion de casos de dengue.

El modelo predice `log(1 + casos)`, pero las metricas se reportan en casos
(escala original), que es lo que entiende quien toma decisiones.

- MAE: casos por semana en que nos equivocamos en promedio.
- RMSE: como el MAE pero castiga mas los errores grandes (los picos).
- WAPE: error total / casos totales. 0 % = perfecto, 100 % = no acierta nada
  del volumen. No se usa MAPE porque el 59 % de las semanas tiene 0 casos
  y el MAPE se indefine (division por cero).
"""
import numpy as np

PASOS = 8                # ventana del LSTM: la primera fila evaluable es la 8.a
HORIZONTE = 4            # semanas hacia adelante
PERCENTIL_BROTE = 90     # "semana de brote" = 10 % de semanas con mas casos reales


def a_casos(y_log):
    """Revierte log(1 + casos) y evita casos negativos."""
    return np.maximum(np.expm1(np.asarray(y_log, dtype=float)), 0)


def mae(y_true, y_pred):
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def wape(y_true, y_pred):
    """Error absoluto total sobre casos totales, en %. NaN si no hay casos."""
    y_true = np.asarray(y_true, dtype=float)
    total = np.abs(y_true).sum()
    if total == 0:
        return float("nan")
    return float(np.abs(y_true - np.asarray(y_pred)).sum() / total * 100)


def evaluate_model(y_true, y_pred, log_target=True):
    """Calcula MAE, RMSE y WAPE en casos.

    Si `log_target` es True, `y_true` e `y_pred` vienen en log(1 + casos)
    (como la columna `objetivo`) y se revierten antes de medir.
    """
    if log_target:
        y_true, y_pred = a_casos(y_true), a_casos(y_pred)
    return {"MAE": mae(y_true, y_pred),
            "RMSE": rmse(y_true, y_pred),
            "WAPE": wape(y_true, y_pred)}


# --- conjunto de prueba y metricas del proyecto ------------------------------

def prueba_lima(modelado):
    """Las 759 semanas de Lima que evalua el LSTM, para comparar con la misma prueba."""
    lima = (modelado[modelado.departamento == "LIMA"]
            .sort_values("fecha_inicio").reset_index(drop=True))
    return lima.iloc[PASOS - 1:len(lima) - HORIZONTE].reset_index(drop=True)


def metricas(real_log, pred_log, fechas, umbral_brote):
    """MAE/RMSE/WAPE globales, en semanas de brote y error en la semana pico."""
    real, pred = a_casos(real_log), a_casos(pred_log)
    out = evaluate_model(real, pred, log_target=False)
    b = real >= umbral_brote
    out.update({f"{k}_brote": v for k, v in
                evaluate_model(real[b], pred[b], log_target=False).items()})
    ip = int(np.argmax(real))
    out["Error_pico"] = float(pred[ip] - real[ip])  # casos; negativo = subestima
    ventana = np.abs((fechas - fechas[ip]).days) <= 120
    ipred = int(np.argmax(np.where(ventana, pred, -1)))
    out["Desfase_pico_sem"] = float((fechas[ipred] - fechas[ip]).days / 7)
    return out


def ic_bootstrap(real, pred, persistencia, bloque=8, n=2000, semilla=0):
    """Diferencia de MAE (modelo - persistencia) con IC 95 % por bootstrap de
    bloques (respeta la autocorrelacion). Devuelve (media, bajo, alto, P(mejor))."""
    rng = np.random.default_rng(semilla)
    real, pred, persistencia = map(np.asarray, (real, pred, persistencia))
    d = np.abs(real - pred) - np.abs(real - persistencia)
    k = int(np.ceil(len(d) / bloque))
    medias = np.empty(n)
    for i in range(n):
        ini = rng.integers(0, len(d) - bloque + 1, k)
        medias[i] = np.concatenate([d[a:a + bloque] for a in ini])[:len(d)].mean()
    bajo, alto = np.percentile(medias, [2.5, 97.5])
    return float(d.mean()), float(bajo), float(alto), float((medias < 0).mean())
