"""Comparacion justa: persistencia, XGBoost y LSTM/GRU en el MISMO protocolo.

Uso (desde la raiz del repo; ~1-2 h con CPU):
    python src/comparacion_justa.py

Protocolo comun (ver src/models.py):
- prueba: las 759 semanas de Lima de `prueba_lima`;
- walk-forward: reentreno cada 13 semanas solo con filas cuyo objetivo ya se conocia;
- universo de entrenamiento: Lima, Ica, La Libertad, Ancash y Callao;
- objetivo: delta = log1p(casos t+4) - log1p(casos t);
- variables: base (FEATURES) y completo (+ regional + nuevas), iguales para todos;
- semillas 42-44; busqueda aleatoria + CV temporal con los mismos cortes (2022, 2023).

Escribe results/comparacion_justa.csv, results/predicciones_walkforward.csv y
results/tuning_rnn.json. Las etapas largas se guardan en results/_cache_wf/
(se puede interrumpir y reanudar); la carpeta se puede borrar al terminar.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluation import PERCENTIL_BROTE, a_casos, ic_bootstrap, metricas, prueba_lima
from models import (SEMILLAS, buscar, ventanas_rnn, walk_forward, walk_forward_rnn,
                    buscar_rnn)
from preprocessing import (DEPARTAMENTOS_MODELO, FEATURES, NUEVAS, PROCESSED, REG,
                           preparar)

RESULTS = Path(__file__).resolve().parents[1] / "results"
CACHE = RESULTS / "_cache_wf"
CACHE.mkdir(exist_ok=True)
FAMILIAS = ("LSTM", "GRU")
VARIANTES = {"": FEATURES, " + regional + nuevas": FEATURES + REG + NUEVAS}


def cargar_json(ruta, calcular):
    if ruta.exists():
        return json.loads(ruta.read_text())
    out = calcular()
    ruta.write_text(json.dumps(out, indent=2))
    return out


def main():
    import tensorflow as tf
    tf.config.experimental.enable_op_determinism()  # misma semilla -> mismo resultado

    ref = prueba_lima(pd.read_csv(PROCESSED / "modelado.csv", parse_dates=["fecha_inicio"]))
    m = preparar(DEPARTAMENTOS_MODELO)
    lima = m[m.departamento == "LIMA"]
    test_idx = lima.index[lima.fecha_inicio.isin(ref.fecha_inicio)]
    prueba = m.loc[test_idx].reset_index(drop=True)
    real_log = prueba["objetivo"].to_numpy()
    fechas = pd.DatetimeIndex(prueba["fecha_inicio"])
    umbral = np.percentile(a_casos(real_log), PERCENTIL_BROTE)
    print(f"prueba Lima: {len(prueba)} semanas | umbral de brote {umbral:.0f} casos", flush=True)

    # --- XGBoost: hiperparametros ya buscados (results/tuning_hiperparametros.json)
    mejores_xgb = cargar_json(RESULTS / "tuning_hiperparametros.json", lambda: buscar(m)[0])

    preds = {"Persistencia": [prueba["log_casos"].to_numpy()]}
    for sufijo, cols in VARIANTES.items():
        nombre = f"XGBoost tuneado{sufijo}"
        preds[nombre] = [walk_forward(m, test_idx, mejores_xgb, s, cols) for s in SEMILLAS]
        print(nombre, "listo", flush=True)

    # --- LSTM / GRU en el mismo protocolo
    tuning_rnn = {}
    ruta_tuning = RESULTS / "tuning_rnn.json"
    if ruta_tuning.exists():
        tuning_rnn = json.loads(ruta_tuning.read_text())
    for fam in FAMILIAS:
        if fam not in tuning_rnn:  # el tuning se hace con las variables base y se reusa en completo
            X, valida = ventanas_rnn(m, FEATURES)
            tuning_rnn[fam] = buscar_rnn(fam, m, X, valida)
            ruta_tuning.write_text(json.dumps(tuning_rnn, indent=2))
    for fam in FAMILIAS:
        for sufijo, cols in VARIANTES.items():
            nombre = f"{fam}{sufijo}"
            X, valida = ventanas_rnn(m, cols)
            preds[nombre] = []
            for s in SEMILLAS:
                f = CACHE / f"{fam}{'_completo' if sufijo else '_base'}_{s}.npy"
                if f.exists():
                    p = np.load(f)
                else:
                    p = walk_forward_rnn(fam, m, X, valida, test_idx, tuning_rnn[fam], s)
                    np.save(f, p)
                preds[nombre].append(p)
                print(nombre, "semilla", s, "listo", flush=True)

    # --- predicciones guardadas
    out = pd.DataFrame({"fecha_inicio": fechas, "real": a_casos(real_log)})
    for nombre, ps in preds.items():
        for s, p in zip(SEMILLAS if len(ps) > 1 else [0], ps):
            out[f"{nombre} s{s}"] = a_casos(p)
    out.to_csv(RESULTS / "predicciones_walkforward.csv", index=False)

    # --- metricas: todo el periodo, 2023-2024 y 2024 (mismas semanas para todos)
    real = a_casos(real_log)
    pers = a_casos(preds["Persistencia"][0])
    recortes = {"759 semanas": np.ones(len(prueba), bool),
                "2023-2024": np.asarray(fechas >= "2023-01-01"),
                "2024": np.asarray(fechas >= "2024-01-01")}
    filas = []
    for nombre, ps in preds.items():
        fila = {"modelo": nombre}
        for rec, mask in recortes.items():
            r = [metricas(real_log[mask], p[mask], fechas[mask], umbral) for p in ps]
            fila[f"MAE {rec}"] = np.mean([x["MAE"] for x in r])
            fila[f"sd MAE {rec}"] = np.std([x["MAE"] for x in r])
            fila[f"RMSE {rec}"] = np.mean([x["RMSE"] for x in r])
            fila[f"WAPE % {rec}"] = np.mean([x["WAPE"] for x in r])
        r = [metricas(real_log, p, fechas, umbral) for p in ps]
        fila["MAE brote"] = np.mean([x["MAE_brote"] for x in r])
        fila["Error pico"] = np.mean([x["Error_pico"] for x in r])
        media = np.mean([a_casos(p) for p in ps], axis=0)
        d, lo, hi, pm = ic_bootstrap(real, media, pers)
        fila.update({"dif MAE vs pers": d, "IC95 bajo": lo, "IC95 alto": hi, "P(mejor que pers)": pm})
        filas.append(fila)
    tabla = pd.DataFrame(filas).set_index("modelo")
    tabla.round(2).to_csv(RESULTS / "comparacion_justa.csv")
    print(tabla.round(1).T.to_string(), flush=True)

    # --- comparacion directa XGBoost vs cada red (mismas semanas, bootstrap de bloques)
    print("\nDiferencia de MAE (XGBoost completo - red), IC 95 % bootstrap de bloques; negativo = XGBoost mejor")
    xgb = np.mean([a_casos(p) for p in preds["XGBoost tuneado + regional + nuevas"]], axis=0)
    filas = []
    for nombre in preds:
        if nombre.startswith(FAMILIAS):
            rn = np.mean([a_casos(p) for p in preds[nombre]], axis=0)
            for rec, mask in recortes.items():
                d, lo, hi, pm = ic_bootstrap(real[mask], xgb[mask], rn[mask])
                filas.append((nombre, rec, round(d, 1), round(lo, 1), round(hi, 1)))
    dif = pd.DataFrame(filas, columns=["red", "periodo", "dif MAE", "IC95 bajo", "IC95 alto"])
    dif.to_csv(RESULTS / "comparacion_justa_xgb_vs_redes.csv", index=False)
    print(dif.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
