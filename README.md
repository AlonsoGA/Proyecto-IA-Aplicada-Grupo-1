# Proyecto de Inteligencia Artificial Aplicada

**Curso:** Inteligencia Artificial Aplicada (1INF62)  
**Periodo:** 2026-2  
**Integrantes:** Luis Leiva, Alonso G. A.  
**Tema:** predicción de número de casos de dengue en el departamento de Lima (81 distritos agregados en una sola serie semanal) para las próximas 4 semanas epidemiológicas, usando el historial de casos y variables climáticas rezagadas. Se usan también series de otros departamentos como variables de apoyo, pero el objetivo a predecir es solo Lima.

## 1. Problema y objetivo
- **Problema que se busca resolver:** el dengue, transmitido por *Aedes* y sin vacuna eficaz, depende de variables climáticas con desfase temporal. Perú vive su peor epidemia histórica (2023-2024), asociada al Niño costero, con Lima muy afectada pese a no ser zona endémica tradicional. Los sistemas de vigilancia reaccionan tarde ante los brotes.
- **Objetivo general:** predecir el número de casos de dengue del departamento de Lima para las próximas 4 semanas epidemiológicas, usando el historial de casos y variables climáticas rezagadas.
- **Importancia de la problemática:** una predicción con 4 semanas de anticipación daría margen para fumigación, control de criaderos y preparación hospitalaria antes de que el brote crezca.

## 2. Dataset
- **Nombre y fuente:** Dengue Perú 2011-2024 con clima, Kaggle (datos públicos). Los datos de vigilancia son del MINSA (CDC Perú, RENACE) y el clima de NASA POWER.
- **Enlace:** <https://www.kaggle.com/datasets/stefanychavezherrera/dengue>
- **Tamaño y variables principales:** 5 archivos relacionados

  | Archivo | Contenido |
  |---|---|
  | Vigilancia epidemiológica | MINSA, 2000-2024, un caso por fila, con distrito y semana epidemiológica |
  | Tabla maestra de distritos | 660 distritos: ubicación, altitud, IDH, pobreza |
  | Clima semanal por celda de grilla | 2010-2024: temperatura, precipitación, humedad y viento, con rezagos de 2/4/6/8 semanas |
  | ICEN mensual | Índice Costero El Niño, 2009-2024 |
  | Enlace distrito-celda | Une cada distrito con su celda climática |

  **Alcance:** "Lima" en este proyecto es el departamento (`DEPARTAMENTO = "LIMA"` en `src/preprocessing.py`), no un distrito. Sus 81 distritos tienen clima disponible y suman 122,073 casos entre 2010 y 2024. El 97.2 % de esos casos se concentra en 2023-2024 (30,735 y 87,864 casos), por el megabrote ligado al Niño costero. De 2010 a 2022 las series son casi nulas, así que el modelo debe capturar una variabilidad temporal muy alta.
- **Permisos/licencia:** la vigilancia es dato público del MINSA con licencia ODC-BY (requiere atribución) y es provisional. Detalle en [`data/raw/README.md`](data/raw/README.md).
- Los datos originales se guardan en `data/raw/` (como `dengue_kaggle.zip`) y los procesados en `data/processed/`.

## 3. Literatura y modelos propuestos
**Papers revisados** (resumen en `papers/`):

| Paper | Qué aportó al proyecto |
|---|---|
| Leung et al. (2023), revisión sistemática de 99 modelos de predicción de brotes de dengue (Luis) | Todos los modelos usan clima y solo el 59.6 % ajusta rezagos, que los autores consideran indispensables: por eso usamos clima rezagado 2/4/6/8 semanas. Las técnicas más comunes de ML son redes neuronales (23.1 %), random forest (15.4 %) y ensembles (10.3 %). El 20.2 % no tiene validación: por eso validamos con cortes temporales (walk-forward) y bootstrap de bloques. |
| Chadalavada et al. (2025), revisión sistemática 2013-2025 (Alonso) | XGBoost aparece entre los métodos más confiables (aunque los estudios no son comparables entre sí) y un LSTM con historial y clima alcanzó MAPE 19.63 % (Chen y Moraga, 2025). Integrar datos epidemiológicos y climáticos mejora la predicción. |
| Mayta y Alemán (2025), DengueAI (Perú) | Compara series de tiempo y deep learning sobre datos abiertos de Perú: es el antecedente local de comparar modelos clásicos con redes. |

**Modelos a implementar** (el baseline se compara con cada uno):

| Modelo | Dónde | Por qué se eligió |
|---|---|---|
| Persistencia (baseline) | `src/models.py` | Repite los casos de hoy a 4 semanas. Referencia mínima que todo modelo debe superar. |
| XGBoost tuneado | `src/models.py`, `notebooks/03_xgboost.ipynb` | Ensemble de árboles, familia respaldada por Leung (random forest y ensembles) y por Chadalavada (XGBoost). Funciona con pocas filas, captura relaciones no lineales entre clima rezagado y casos, y permite medir importancia de variables. |
| LSTM y GRU | `notebooks/02_modelos.ipynb` | Redes recurrentes, las más usadas en la literatura para series con clima (Leung: redes neuronales; Chadalavada: LSTM). Reciben ventanas de 8 semanas de historial y clima; la variante regional agrega departamentos vecinos. La GRU es una versión más liviana de la LSTM. |

Resultado resumido (sección 7): XGBoost supera a LSTM y GRU. Con solo dos olas epidémicas (2023 y 2024) hay pocos datos para entrenar redes recurrentes, y estas terminan subestimando los picos.

**Métricas.** Se reportan en casos (no en log):
- **MAE:** error absoluto medio, en casos por semana.
- **RMSE:** como el MAE pero penaliza más los errores grandes (los picos).
- **WAPE** (*weighted absolute percentage error*): `Σ|y − ŷ| / Σ|y| × 100`, es decir, el error total como porcentaje de los casos totales. 0 % es perfecto y 100 % equivale a no acertar nada del volumen. Es equivalente al cociente MAD/Mean de Kolassa y Schütz (2007). Lo elegimos porque el 59 % de las semanas de Lima tiene 0 casos, lo que vuelve indefinido al MAPE (división por cero); el WAPE pondera por volumen, no depende de la escala y se lee directamente como "% de casos mal predichos".

## 4. Metodología
1. Revisión de literatura académica revisada por pares (sección 3).
2. Análisis exploratorio de datos en `notebooks/01_eda.ipynb`.
3. Preparación de datos con funciones de `src/preprocessing.py`.
4. Implementación del baseline (persistencia) y de XGBoost tuneado en `src/models.py`; LSTM y GRU en `notebooks/02_modelos.ipynb` (justificación en la sección 3).
5. Evaluación con métricas apropiadas en `src/evaluation.py` (MAE, RMSE y WAPE en casos, definidas en la sección 3).
6. Comparación y discusión de resultados (`notebooks/03_xgboost.ipynb`, `results/model_comparison.txt`).

## 5. Estructura
- `data/raw/`: datos originales.
- `data/processed/`: datos limpios y preparados.
- `notebooks/`: `01_eda.ipynb` (exploración), `02_modelos.ipynb` (LSTM y GRU) y `03_xgboost.ipynb` (XGBoost tuneado y comparación); anexo opcional: `anexo_ablacion_errores.ipynb` (ablación de variables y errores por fase).
- `src/`: `preprocessing.py` (datos, variables regionales y nuevas), `models.py` (persistencia y XGBoost con tuning y walk-forward) y `evaluation.py` (métricas, prueba de Lima y bootstrap).
- `results/`: métricas, gráficos y análisis comparativo.
- `papers/`: artículos revisados por el grupo.

## 6. Cómo ejecutar
1. Instalar Python 3.10 o superior.
2. Crear y activar un entorno virtual.
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Descomprimir `data/raw/dengue_kaggle.zip` dentro de `data/raw/` y generar las tablas procesadas:
   ```bash
   python src/preprocessing.py
   ```
5. Abrir los notebooks (desde `notebooks/`):
   ```bash
   jupyter notebook
   ```
   `03_xgboost.ipynb` usa los hiperparámetros guardados en `results/tuning_hiperparametros.json`; si no existen, repite la búsqueda (~10 min). Genera `data/processed/modelado_ampliado.csv` (18 departamentos) si falta. Para comparar corridas de XGBoost hay que usar el mismo `N_JOBS` (por defecto 1).

## 7. Resultados
Resultados en `results/metrics.csv`, gráficos en `results/plots/` y análisis en `results/model_comparison.txt`. XGBoost (Lima, 759 semanas, MAE medio de 3 semillas):

| Modelo | MAE | RMSE | WAPE % |
|---|---|---|---|
| Persistencia (baseline) | 132.8 | 663.6 | 82.6 |
| XGBoost tuneado | 79.1 | 463.6 | 49.2 |
| XGBoost tuneado + regional + variables nuevas | 67.0 | 371.2 | 41.7 |

La mejora frente a la persistencia es significativa (IC 95 % de la diferencia de MAE por bootstrap de bloques excluye 0), y se mantiene en 7 de 8 departamentos con ola 2023-24.

**Comparación con LSTM y GRU (Alonso).** Su notebook evalúa solo 2024, así que la comparación se hace sobre esos mismos 43 orígenes de Lima (casos medios: 2030). Los números de LSTM/GRU salen de ejecutar `02_modelos.ipynb` (una semilla; variante regional con historial y clima); los demás, de `03_xgboost.ipynb`.

| Modelo (Lima, 2024) | MAE | RMSE | Sesgo |
|---|---|---|---|
| Persistencia (baseline) | 1688.2 | 2641.5 | +12 |
| LSTM regional (Alonso) | 1495.8 | 2865.8 | −1452 |
| GRU regional (Alonso) | 1678.2 | 3192.7 | −1669 |
| XGBoost tuneado | 968.6 | 1787.5 | −35 |
| XGBoost tuneado + regional + variables nuevas | 793.4 | 1387.9 | −169 |

LSTM y GRU subestiman ~1450-1670 casos por semana; la GRU no mejora a la persistencia en MAE. Limitaciones: solo dos olas, el pico sigue subestimado y solo ~15 % de los inicios de ola se avisan a tiempo con 4 semanas de anticipación.

## 8. Trabajo futuro (para el artículo)

- **Alerta de brote por distrito:** predecir, para los 5–10 distritos que concentran 40–64% de los casos (Lima 2023–24), si se iniciará un brote en 4 semanas. Plantear como clasificación binaria (brote sí/no) y no como conteo, porque las series por distrito son dispersas (muchas semanas en cero, solo dos olas). Limitación: a nivel Lima solo ~15% de las alzas se anticipa a tiempo, por lo que por distrito sería más difícil.

## 9. Referencias
- Leung, X. Y., Islam, R. M., Adhami, M., Ilic, D., McDonald, L., Palawaththa, S., Diug, B., Munshi, S. U., & Karim, M. N. (2023). A systematic review of dengue outbreak prediction models: Current scenario and future directions. *PLOS Neglected Tropical Diseases, 17*(2), e0010631. https://doi.org/10.1371/journal.pntd.0010631
- Chadalavada, S., Kamath, A. P., Sengur, A., Yarlagadda, T., Tan, R.-S., Ciaccio, E. J., Mathew, A., Deo, R., Barua, P. D., Hafeez-Baig, A., & Acharya, R. (2025). Automated detection and prediction of dengue fever: A systematic review from 2013 to 2025.
- Mayta Quispe, M. F., & Alemán Gonzales, L. (2025). DengueAI: Comparative time-series and deep-learning modeling for early prediction of dengue outbreaks in rural Peru using open data. *2025 IEEE XXXII International Conference on Electronics, Electrical Engineering and Computing (INTERCON)*. https://doi.org/10.1109/INTERCON67304.2025.11244382
- Kolassa, S., & Schütz, W. (2007). Advantages of the MAD/Mean ratio over the MAPE. *Foresight: The International Journal of Applied Forecasting, 6*, 40-43. (Fuente del WAPE.)
