# Proyecto de Inteligencia Artificial Aplicada

**Curso:** Inteligencia Artificial Aplicada (1INF62)  
**Periodo:** 2026-2  
**Integrantes:** Luis Leiva, Alonso G. A., ______  
**Tema:** predicción de número de casos de dengue en el distrito de Lima para las próximas 4 semanas epidemiológicas, usando el historial de casos y variables climáticas rezagadas.

## 1. Problema y objetivo
- **Problema que se busca resolver:** el dengue, transmitido por *Aedes* y sin vacuna eficaz, depende de variables climáticas con desfase temporal. Perú vive su peor epidemia histórica (2023-2024), asociada al Niño costero, con Lima muy afectada pese a no ser zona endémica tradicional. Los sistemas de vigilancia reaccionan tarde ante los brotes.
- **Objetivo general:** predecir el número de casos de dengue en Lima para las próximas 4 semanas epidemiológicas, usando el historial de casos y variables climáticas rezagadas.
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

  Lima tiene 81 distritos con clima disponible para todos y 122,073 casos entre 2010 y 2024. El 97.2 % de esos casos se concentra en 2023-2024 (30,735 y 87,864 casos), por el megabrote ligado al Niño costero. De 2010 a 2022 las series son casi nulas, así que el modelo debe capturar una variabilidad temporal muy alta.
- **Permisos/licencia:** la vigilancia es dato público del MINSA con licencia ODC-BY (requiere atribución) y es provisional. Detalle en [`data/raw/README.md`](data/raw/README.md).
- Los datos originales se guardan en `data/raw/` (como `dengue_kaggle.zip`) y los procesados en `data/processed/`.

## 3. Metodología
1. Revisión de literatura académica revisada por pares.
2. Análisis exploratorio de datos en `notebooks/01_eda.ipynb`.
3. Preparación de datos con funciones de `src/preprocessing.py`.
4. Implementación de un baseline y otros modelos en `src/models.py`.
5. Evaluación con métricas apropiadas en `src/evaluation.py`.
6. Comparación y discusión de resultados.

## 4. Estructura
- `data/raw/`: datos originales.
- `data/processed/`: datos limpios y preparados.
- `notebooks/`: análisis exploratorio y experimentos.
- `src/`: funciones de preparación, modelos y evaluación.
- `results/`: métricas, gráficos y análisis comparativo.
- `papers/`: artículos revisados por el grupo.

## 5. Cómo ejecutar
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
5. Abrir los notebooks:
   ```bash
   jupyter notebook
   ```

Completar las instrucciones específicas cuando se elijan el dataset y los modelos.

## 6. Resultados
Los resultados finales se registrarán en `results/metrics.csv`, los gráficos en `results/plots/` y el análisis en `results/model_comparison.txt`.

## 7. Referencias
- Leung, X. Y., Islam, R. M., Adhami, M., Ilic, D., McDonald, L., Palawaththa, S., Diug, B., Munshi, S. U., & Karim, M. N. (2023). A systematic review of dengue outbreak prediction models: Current scenario and future directions. *PLOS Neglected Tropical Diseases, 17*(2), e0010631. https://doi.org/10.1371/journal.pntd.0010631
- Añadir referencias de los papers de los demás integrantes.
