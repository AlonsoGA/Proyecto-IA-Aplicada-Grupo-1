# Datos crudos

Los 5 CSV originales vienen comprimidos en `dengue_kaggle.zip` (23.8 MB). Los CSV descomprimidos pesan ~200 MB (el de vigilancia, 108 MB, supera el límite de 100 MB de GitHub), por eso están en `.gitignore` y solo se sube el zip.

## Cómo usarlos

1. Descomprimir `dengue_kaggle.zip` dentro de esta carpeta (`data/raw/`), de modo que los 5 CSV queden aquí.
2. Ejecutar `python src/preprocessing.py` para generar las tablas de `data/processed/`.

Origen del zip: dataset de Kaggle <https://www.kaggle.com/datasets/stefanychavezherrera/dengue>, sin modificar.

## Archivos

| Archivo | Tamaño | Contenido | Fuente original |
|---|---|---|---|
| `datos_abiertos_vigilancia_dengue_2000_2024.csv` | 108.5 MB | Un caso por fila (departamento, distrito, año, semana, diagnóstico, edad, sexo). Separador `;` | CDC Perú-MINSA (RENACE), [datosabiertos.gob.pe](https://www.datosabiertos.gob.pe/dataset/vigilancia-epidemiol%C3%B3gica-de-dengue) |
| `clima_celda_semana.csv` | 91.1 MB | Clima semanal por celda de grilla (~55 km), 2010-2024, con rezagos de 2/4/6/8 semanas y anomalías | NASA POWER (MERRA-2) |
| `icen_mensual.csv` | 23 KB | Índice Costero El Niño, mensual, 2009-2024 | IGP / ENFEN |
| `distritos_dengue_centroides.csv` | 144 KB | 660 distritos con ubicación, altitud, IDH y pobreza | Compilado en el dataset de Kaggle |
| `mapa_ubigeo_celda.csv` | 51 KB | Distrito (ubigeo) a celda de grilla climática | Compilado en el dataset de Kaggle |

## Permisos y licencia

- Fecha de descarga: 2026-10-10 (Kaggle, dataset completo de 5 archivos).
- La vigilancia es dato público del MINSA con licencia ODC-BY (requiere atribución). La ficha oficial indica que los datos son provisionales.
- No se verificó la licencia del dataset de Kaggle que reúne los 5 archivos.

## Notas

- `ubigeo` debe leerse como texto; si no, se pierde el cero inicial de los departamentos con código menor a 10.
- Las filas duplicadas de la vigilancia no se eliminan (cada fila es un caso, no hay identificador de paciente).
- Los datos llegan hasta 2024. Existen datos de 2025-2026 solo en boletines del CDC (no integrados aún).
