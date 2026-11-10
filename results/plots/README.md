# Gráficos

Índice de los gráficos del proyecto: qué muestra cada uno y qué código lo genera.

## Evaluación de modelos
| Archivo | Qué muestra | Generado por |
|---|---|---|
| `xgboost_vs_real.png` | Lima 2023-2024: casos reales a 4 semanas vs persistencia, XGBoost tuneado y XGBoost + regional + variables nuevas (media de 3 semillas). | `notebooks/03_xgboost.ipynb`, sección 7 |

## Análisis exploratorio (`eda/`)
Generados por `notebooks/01_eda.ipynb`.
| Archivo | Qué muestra |
|---|---|
| `eda_serie_semanal_lima.png` | Casos semanales en Lima 2010-2024 (arriba) y detalle 2022-2024 (abajo) |
| `eda_casos_anuales_lima.png` | Casos totales por año en Lima; 2023 y 2024 resaltados |
| `eda_distribucion_casos.png` | Histogramas de casos semanales de Lima: escala lineal y log(1 + casos) |
| `eda_estacionalidad_lima.png` | Casos por semana epidemiológica en Lima, una línea por año (2022, 2023, 2024) |
| `eda_boxplots.png` | Boxplots de casos, temperatura (media, máx., mín.), precipitación, humedad, viento y log(1 + casos), con el conteo de atípicos por IQR |
| `eda_casos_vs_temperatura.png` | Casos (arriba) y temperatura media (abajo) en Lima 2023-2024, misma línea de tiempo |
| `eda_correlacion_heatmap.png` | Matriz de correlación en Lima 2010-2024: variables climáticas, ICEN, dos rezagos y log(1 + casos) |
| `eda_correlacion_lags.png` | Correlación entre log(1 + casos) en t y clima/ICEN en t − k (k = 0 a 12 semanas), Lima 2023-2024 |
| `eda_clima_departamentos.png` | Dispersión de temperatura media vs precipitación semanal media 2010-2024, un punto por departamento (Lima resaltada) |
| `eda_lima_vs_departamentos.png` | Casos anuales (escala log) de Lima y los 8 departamentos con más casos |
| `eda_split_objetivo.png` | Histogramas del objetivo log(1 + casos a 4 semanas) en train, validación y test |

Los gráficos se regeneran al ejecutar el notebook correspondiente; no se editan a mano.
