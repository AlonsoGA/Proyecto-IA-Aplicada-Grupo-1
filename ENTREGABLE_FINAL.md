# Entregable final (semana 15)

**Curso:** Inteligencia Artificial Aplicada (1INF62), 2026-2, Grupo 1  
**Integrantes:** Luis Alberto Leiva Grajales y Alonso Elías Gutiérrez Aguirre  
**Tema:** Predicción del número de casos semanales de dengue en el departamento de Lima con cuatro semanas de anticipación.

## 1. Qué se completó

| Entregable | Estado | Dónde |
|---|---|---|
| README con el problema, los datos y la metodología | Completo | `README.md` |
| Revisión de literatura y análisis exploratorio | Completo | `papers/`, `notebooks/01_eda.ipynb` |
| Implementación y evaluación de los modelos | Completo | `notebooks/02_modelos.ipynb`, `notebooks/03_xgboost.ipynb`, `src/comparacion_justa.py` |
| Ablación y análisis del error por fase | Completo | `notebooks/anexo_ablacion_errores.ipynb`, `results/ablacion.csv`, `results/error_por_fase.csv` |
| Reporte académico | Completo | `Reporte_academico.pdf` |
| Presentación | Completo | `presentación.pdf` |

## 2. Modelos evaluados

El objetivo fue pronosticar el número de casos en Lima cuatro semanas después de cada fecha de emisión.

| Modelo | Responsable | Dónde | Descripción |
|---|---|---|---|
| Persistencia | Grupo | `src/models.py` | Usa el conteo de la semana actual como pronóstico a cuatro semanas. |
| XGBoost | Luis Leiva | `notebooks/03_xgboost.ipynb` | Compara una variante base con otra que incorpora información regional y tendencias recientes. |
| LSTM y GRU | Alonso Gutiérrez | `notebooks/02_modelos.ipynb` | Redes recurrentes que procesan ventanas de ocho semanas. Se probaron variantes con historial, clima y entrenamiento regional. |

## 3. Resultados

En el protocolo común de **759 semanas de Lima**, XGBoost completo obtuvo un MAE de **67,05 casos por semana**, seguido de LSTM base (**73,33**), GRU base (**91,04**) y persistencia (**132,76**). Los intervalos de confianza de las diferencias entre XGBoost y las redes incluyeron cero. El detalle está en `results/comparacion_justa.csv`.

En la ablación reproducida, retirar por separado el ICEN o las tendencias recientes redujo ligeramente el MAE histórico. Retirar el clima, la estacionalidad o la información regional lo aumentó. Las 77 semanas de brote concentraron el **96,8 %** del error absoluto del modelo completo.

