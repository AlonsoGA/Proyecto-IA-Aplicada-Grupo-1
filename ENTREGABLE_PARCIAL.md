# Entregable parcial (semana 8)

**Curso:** Inteligencia Artificial Aplicada (1INF62), 2026-2, Grupo 1
**Tema:** predicción de número de casos de dengue en el distrito de Lima para las próximas 4 semanas epidemiológicas, usando el historial de casos y variables climáticas rezagadas.

## 1. Qué se completó

| Entregable | Estado | Dónde |
|---|---|---|
| README completo (problema, objetivo, metodología) | Completo | `README.md` |
| Papers revisados, mínimo 1 por integrante | Parcial (2 de 3) | `papers/` |
| Dataset con origen, características y permisos | Completo | `data/raw/dengue_kaggle.zip`, `README.md` (sección Dataset) |
| EDA con visualizaciones | Completo | `notebooks/01_eda.ipynb`, `results/plots/eda/` |
| Propuesta de modelos | Completo | sección 2 |
| Baseline funcionando | Completo | `src/models.py` (persistencia), `results/metrics.csv` |

## 2. Propuesta de modelos

Objetivo: `log(1 + casos en t+4)` de Lima. Todo modelo debe superar la persistencia (repetir los casos de hoy).

| Modelo | Responsable | Dónde | Justificación |
|---|---|---|---|
| Persistencia (baseline) | grupo | `src/models.py` | Referencia mínima: MAE 132.8 en 759 semanas de Lima |
| XGBoost tuneado | Luis | `src/models.py`, `notebooks/03_xgboost.ipynb` | Árboles potenciados con clima y casos rezagados; funcionan con pocas filas y capturan relaciones no lineales |
| LSTM y GRU | Alonso | `notebooks/02_modelos.ipynb` | Redes recurrentes sobre ventanas de 8 semanas; usadas en la literatura de predicción de brotes de dengue (Leung et al., 2023) |

## 3. Baseline

Persistencia evaluada en las 759 semanas de Lima (`src/evaluation.py`): MAE 132.8, RMSE 663.6, WAPE 82.6 %. Es la referencia para el resto de modelos. Resultados en `results/metrics.csv` y `results/model_comparison.txt`.

## 4. Pendientes

- Resumen de paper del tercer integrante en `papers/`.
- Informe final, presentación y `ENTREGABLE_FINAL.md`.
