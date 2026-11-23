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
| LSTM y GRU | `src/models.py`, `notebooks/02_modelos.ipynb` | Redes recurrentes, las más usadas en la literatura para series con clima (Leung: redes neuronales; Chadalavada: LSTM). Reciben ventanas de 8 semanas de historial y clima; la variante regional agrega departamentos vecinos. La GRU es una versión más liviana de la LSTM. |

**Configuración de LSTM y GRU.** Misma arquitectura para ambas: una capa recurrente de 32 unidades, `Dropout(0.2)` y `Dense(1)`; optimizador Adam, pérdida MSE sobre `log(1 + casos)`, lotes de 32, ventana de 8 semanas y parada temprana (paciencia 8) según el MAE en casos. Qué sale de la literatura y qué es decisión propia:

| Decisión | Valor | Respaldo |
|---|---|---|
| Arquitectura | 1 capa recurrente + `Dropout` + `Dense` | Majeed et al. (2023, IJERPH): LSTM de una capa con `Dropout` 0.2 y pérdida MSE para dengue semanal. |
| Optimizador y pérdida | Adam, MSE | Flores et al. (2026, IJEECS): LSTM, BiLSTM, GRU y BiGRU con Adam y MSE sobre casos semanales de dengue del MINSA (Perú). |
| Tamaño de capa | 32 unidades | Rango de la literatura: 4 (Majeed et al.) a 100 (Flores et al.). Elegimos un valor intermedio y pequeño porque solo hay dos olas epidémicas para entrenar. |
| Ventana | 8 semanas | Propia. Flores et al. usan 52 semanas y Majeed et al. de 1 a 6 pasos; con 15 años de datos casi nulos antes de 2023, una ventana larga deja pocas muestras útiles. Falta probar otras ventanas. |
| Escala log y parada temprana | `log(1 + casos)`, paciencia 8 | Propia: estabiliza los picos y evita sobreajustar. Flores et al. entrenan 100 épocas fijas sin parada temprana. |

Diferencias con Flores et al. (2026): ellos usan solo el historial de casos a nivel nacional y predicen 1 a 5 pasos con atención; nosotros agregamos clima rezagado (recomendado por Leung et al.) y predicimos a 4 semanas. En el experimento original de `notebooks/02_modelos.ipynb` no se hizo una búsqueda de hiperparámetros comparable a la de XGBoost. Posteriormente, `src/comparacion_justa.py` incorporó una búsqueda de hiperparámetros para LSTM/GRU con validación temporal (ajustada con las variables base y reutilizada en la variante completa). Por ello, ambos experimentos deben reportarse por separado.

Resultado resumido (sección 7): XGBoost completo presenta el menor MAE promedio en la comparación común, seguido de cerca por LSTM base. Sin embargo, los intervalos de confianza de la comparación directa incluyen cero; no se demuestra una superioridad estadísticamente significativa de XGBoost frente a LSTM. Los picos epidémicos siguen siendo difíciles de anticipar.

**Métricas.** Se reportan en casos (no en log):
- **MAE:** error absoluto medio, en casos por semana.
- **RMSE:** como el MAE pero penaliza más los errores grandes (los picos).
- **WAPE** (*weighted absolute percentage error*): `Σ|y − ŷ| / Σ|y| × 100`, es decir, el error total como porcentaje de los casos totales. 0 % indica predicciones perfectas; 100 % significa que la suma de errores absolutos iguala el volumen total observado, pero no implica necesariamente que ninguna predicción sea correcta. Es equivalente al cociente MAD/Mean de Kolassa y Schütz (2007). Lo elegimos porque el 59 % de las semanas de Lima tiene 0 casos, lo que vuelve indefinido al MAPE (división por cero); el WAPE pondera por volumen, no depende de la escala y se lee directamente como "% de casos mal predichos".

## 4. Metodología
1. Revisión de literatura académica revisada por pares (sección 3).
2. Análisis exploratorio de datos en `notebooks/01_eda.ipynb`.
3. Preparación de datos con funciones de `src/preprocessing.py`.
4. Implementación del baseline (persistencia) y de XGBoost tuneado en `src/models.py`; LSTM y GRU en `notebooks/02_modelos.ipynb` (justificación en la sección 3).
5. Evaluación con métricas apropiadas en `src/evaluation.py` (MAE, RMSE y WAPE en casos, definidas en la sección 3).
6. Experimento original y análisis de ablación (`notebooks/03_xgboost.ipynb`, `notebooks/anexo_ablacion_errores.ipynb`).
7. Comparación adicional con protocolo común para persistencia, XGBoost, LSTM y GRU (`src/comparacion_justa.py`), con sus métricas y contrastes estadísticos en `results/comparacion_justa.csv` y `results/comparacion_justa_xgb_vs_redes.csv`.

## 5. Estructura
- `data/raw/`: datos originales.
- `data/processed/`: datos limpios y preparados.
- `notebooks/`: `01_eda.ipynb` (exploración), `02_modelos.ipynb` (LSTM y GRU, usa `src/models.py`) y `03_xgboost.ipynb` (XGBoost tuneado y comparación); anexo opcional: `anexo_ablacion_errores.ipynb` (ablación de variables y errores por fase).
- `src/`: `preprocessing.py` (datos, variables regionales y nuevas), `models.py` (persistencia, XGBoost con tuning y walk-forward, y LSTM/GRU) y `evaluation.py` (métricas, prueba de Lima y bootstrap), además de `comparacion_justa.py` (comparación común de arquitecturas).
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
   `03_xgboost.ipynb` usa los hiperparámetros guardados en `results/tuning_hiperparametros.json`; si no existen, repite la búsqueda. Si falta `data/processed/modelado_ampliado.csv`, intenta extraer los datos originales desde `data/raw/dengue_kaggle.zip` (si es necesario) y generar el dataset ampliado. Antes de ejecutar el experimento es necesario disponer de `data/processed/modelado.csv` y las otras tablas que construye el preprocesamiento.
6. Para reproducir la comparación común, desde la raíz del proyecto:
   ```bash
   python src/comparacion_justa.py
   ```
   Esta evaluación puede ser prolongada en CPU, utiliza tres semillas y guarda predicciones intermedias en `results/_cache_wf/`. Para contrastar ejecuciones hay que registrar versiones de Python y bibliotecas, datos preparados y `N_JOBS` (por defecto 1). `requirements.txt` todavía no fija versiones, por lo que **no se garantiza identidad numérica entre entornos**.

## 7. Resultados

### 7.1. Comparación principal: protocolo común (*walk-forward*)

La comparación principal entre arquitecturas está implementada en [`src/comparacion_justa.py`](src/comparacion_justa.py). Evalúa los mismos **759 orígenes semanales de Lima** con horizonte de **cuatro semanas**, reentrenamiento cada **13 semanas**, entrenamiento con Lima, Ica, La Libertad, Áncash y Callao y tres semillas (42, 43 y 44). Usa validación temporal para seleccionar hiperparámetros y considera dos conjuntos de variables: base y base + regionales + nuevas. Los valores de MAE y RMSE están expresados en **casos**.

Fuente: [`results/comparacion_justa.csv`](results/comparacion_justa.csv).

| Modelo | MAE 759 semanas | RMSE 759 semanas | WAPE 759 semanas | MAE 2024 | RMSE 2024 | WAPE 2024 |
|---|---:|---:|---:|---:|---:|---:|
| Persistencia | 132.76 | 663.61 | 82.61 % | 1688.19 | 2641.48 | 83.18 % |
| XGBoost tuneado | 79.06 | 463.62 | 49.20 % | 985.43 | 1816.35 | 48.55 % |
| **XGBoost + regional + nuevas** | **67.05** | **371.18** | **41.72 %** | **793.41** | **1416.31** | **39.09 %** |
| LSTM | 73.33 | 411.56 | 45.63 % | 846.36 | 1547.03 | 41.70 % |
| LSTM + regional + nuevas | 76.49 | 443.16 | 47.60 % | 976.76 | 1771.38 | 48.12 % |
| GRU | 91.04 | 537.92 | 56.65 % | 1064.91 | 2081.13 | 52.47 % |
| GRU + regional + nuevas | 91.36 | 528.59 | 56.85 % | 1077.37 | 2046.94 | 53.08 % |

En este protocolo, el XGBoost completo obtiene el menor MAE promedio observado. En 2024 reduce el MAE aproximadamente **53.0 % frente a persistencia**. No obstante, su ventaja descriptiva frente a LSTM base **no implica superioridad estadísticamente demostrada**: el contraste directo por bootstrap de bloques sobre el MAE arroja un intervalo del 95 % de **−247.6 a 174.6** para 2024, que incluye el cero. Los demás contrastes directos se encuentran en [`results/comparacion_justa_xgb_vs_redes.csv`](results/comparacion_justa_xgb_vs_redes.csv). Los intervalos se calculan sobre diferencias de error, y no deben confundirse con la diferencia de los MAE medios de la tabla.

### 7.2. Experimento original de notebooks y comparación de 43 orígenes

Los notebooks `02_modelos.ipynb` y `03_xgboost.ipynb` conservan un **experimento distinto**: la comparación de 2024 sobre **43 orígenes comunes** entre sus predicciones. Sus métricas se guardan en `results/comparacion_2024.csv` y `results/metrics.csv`. No deben combinarse fila por fila con la evaluación común de la sección 7.1, porque los procedimientos de entrenamiento y las variantes recurrentes son diferentes.

En una **repetición independiente de ese experimento en Google Colab (Python 3.13.18, XGBoost 3.4.1)** se obtuvieron las siguientes métricas de 2024, idénticas en dos ejecuciones del mismo entorno. **Estos resultados de Colab aún no sustituyen necesariamente los CSV versionados en el repositorio.**

| Modelo, experimento original en Colab | MAE 2024 | RMSE 2024 | WAPE 2024 |
|---|---:|---:|---:|
| Persistencia | 1688.2 | 2641.5 | 83.2 % |
| XGBoost tuneado | 1063.3 | 1978.7 | 52.4 % |
| XGBoost + regional + nuevas | **832.3** | **1465.7** | **41.0 %** |
| LSTM regional (Alonso) | 1495.8 | 2865.8 | 73.7 % |
| GRU regional (Alonso) | 1678.2 | 3192.7 | 82.7 % |

La diferencia entre los resultados de XGBoost en distintas ejecuciones no ha sido atribuida de manera concluyente a una sola causa. Los hiperparámetros guardados coinciden, pero `requirements.txt` no fija versiones y no se ha confirmado que los datasets usados históricamente fueran idénticos. La repetición en Colab **demuestra consistencia dentro de ese entorno**, no reproducción exacta en todos los equipos.

### 7.3. Ablación y errores por fase

El experimento de ablación se encuentra en `notebooks/anexo_ablacion_errores.ipynb`. En la repetición de Colab, el MAE histórico fue **70.5** para el modelo completo, **83.1** usando solo las variables base, **68.6** sin ICEN, **68.8** sin las variables nuevas, **73.1** sin clima, **75.8** sin estacionalidad y **77.1** sin información regional. Estas cifras corresponden al protocolo original y **no son una ablación de las siete variantes de la comparación justa**.

La contribución de cada grupo no fue uniformemente positiva: retirar información regional, clima o estacionalidad empeoró el MAE histórico; retirar ICEN o las variables nuevas lo redujo ligeramente en esta ejecución. La interpretación depende del periodo y del protocolo.

En el análisis de errores de esa misma ejecución, las **77 semanas de brote** (percentil 90 de casos) concentraron **96.8 %** del error absoluto del modelo completo. El principal desafío sigue siendo anticipar las subidas bruscas de casos y los picos epidémicos.

## 8. Trabajo futuro (para el artículo)

- **Alerta de brote por distrito:** predecir, para los 5–10 distritos que concentran 40–64% de los casos (Lima 2023–24), si se iniciará un brote en 4 semanas. Plantear como clasificación binaria (brote sí/no) y no como conteo, porque las series por distrito son dispersas (muchas semanas en cero, solo dos olas). Limitación: a nivel Lima el cruce de 500 casos se predice 3 semanas tarde en 2023 y 1 en 2024, por lo que por distrito sería más difícil.

## 9. Referencias
- Leung, X. Y., Islam, R. M., Adhami, M., Ilic, D., McDonald, L., Palawaththa, S., Diug, B., Munshi, S. U., & Karim, M. N. (2023). A systematic review of dengue outbreak prediction models: Current scenario and future directions. *PLOS Neglected Tropical Diseases, 17*(2), e0010631. https://doi.org/10.1371/journal.pntd.0010631
- Chadalavada, S., Kamath, A. P., Sengur, A., Yarlagadda, T., Tan, R.-S., Ciaccio, E. J., Mathew, A., Deo, R., Barua, P. D., Hafeez-Baig, A., & Acharya, R. (2025). Automated detection and prediction of dengue fever: A systematic review from 2013 to 2025.
- Mayta Quispe, M. F., & Alemán Gonzales, L. (2025). DengueAI: Comparative time-series and deep-learning modeling for early prediction of dengue outbreaks in rural Peru using open data. *2025 IEEE XXXII International Conference on Electronics, Electrical Engineering and Computing (INTERCON)*. https://doi.org/10.1109/INTERCON67304.2025.11244382
- Kolassa, S., & Schütz, W. (2007). Advantages of the MAD/Mean ratio over the MAPE. *Foresight: The International Journal of Applied Forecasting, 6*, 40-43. (Fuente del WAPE.)
- Flores, A., Tito Chura, H., Yana Mamani, V., & Rosado Chavez, C. (2026). Dengue case forecasting using multi-step deep learning models with attention layers. *Indonesian Journal of Electrical Engineering and Computer Science, 41*(2), 546-554. https://doi.org/10.11591/ijeecs.v41.i2.pp546-554
- Majeed, M. A., Shafri, H. Z. M., Zulkafli, Z., & Wayayok, A. (2023). A deep learning approach for dengue fever prediction in Malaysia using LSTM with spatial attention. *International Journal of Environmental Research and Public Health, 20*(5), 4130. https://doi.org/10.3390/ijerph20054130
