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
| `eda_serie_semanal_lima.png` | Serie semanal de casos en Lima |
| `eda_casos_anuales_lima.png` | Casos por año |
| `eda_distribucion_casos.png` | Distribución de los casos semanales |
| `eda_estacionalidad_lima.png` | Estacionalidad por semana del año |
| `eda_boxplots.png` | Boxplots de las variables |
| `eda_casos_vs_temperatura.png` | Casos frente a temperatura |
| `eda_correlacion_heatmap.png` | Correlación entre variables |
| `eda_correlacion_lags.png` | Correlación con rezagos climáticos |
| `eda_clima_departamentos.png` | Clima por departamento |
| `eda_lima_vs_departamentos.png` | Lima frente a otros departamentos |
| `eda_split_objetivo.png` | División temporal del objetivo |

Los gráficos se regeneran al ejecutar el notebook correspondiente; no se editan a mano.
