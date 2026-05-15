# Spec D1 — Pipeline EVA (Evaluaciones Agropecuarias Municipales)

## Objetivo
Descargar, limpiar y unificar los datos de rendimiento agrícola de los 15 municipios del MVP desde las dos fuentes EVA (2007-2018 y 2019-2024), produciendo dos archivos Parquet con esquema unificado.

## Módulo
`modules/agricultural/ingestion.py`

## Inputs
### Fuente 1: EVA histórica 2007-2018
- Dataset ID: `2pnw-mmge`
- URL: `https://www.datos.gov.co/resource/2pnw-mmge.json`
- Filtros: `cultivo IN ('CAFÉ','CACAO','MAÍZ')` y municipios del MVP
- Columnas a usar: `c_d_mun`, `municipio`, `departamento`, `cultivo`, `a_o`, `periodo`, `rendimiento_t_ha`, `rea_sembrada_ha`, `rea_cosechada_ha`, `producci_n_t`, `ciclo_de_cultivo`

### Fuente 2: EVA reciente 2019-2024
- Dataset ID: `uejq-wxrr`
- URL: `https://www.datos.gov.co/resource/uejq-wxrr.json`
- Filtros: `cultivo IN ('Café','Cacao','Maíz')` y municipios del MVP
- Columnas a usar: `c_digo_dane_municipio`, `municipio`, `departamento`, `cultivo`, `a_o`, `periodo`, `rendimiento`, `rea_sembrada`, `rea_cosechada`, `producci_n`, `ciclo_del_cultivo`

## Outputs
### `data/eva_historica.parquet`
### `data/eva_reciente.parquet`
### `data/eva_completa.parquet` (unión de los dos anteriores)

Esquema unificado de los 3 archivos:
```
codigo_dane     : str    — 5 dígitos con cero a la izquierda
municipio       : str    — Title Case normalizado
departamento    : str    — Title Case normalizado
cultivo         : str    — 'Café' | 'Cacao' | 'Maíz'
año             : int    — 2007..2024
periodo         : str    — '2022A' | '2022B' | '2022'
rendimiento     : float  — t/ha, None si no disponible o fuera de rango
area_sembrada   : float  — ha
area_cosechada  : float  — ha
produccion      : float  — toneladas
ciclo           : str    — 'PERMANENTE' | 'TRANSITORIO'
fuente          : str    — 'historica' | 'reciente'
```

## Municipios del MVP (los 15)
```python
MUNICIPIOS_MVP = [
    ('Ibagué', '73001'), ('Chaparral', '73168'),
    ('Neiva', '41001'), ('Garzón', '41298'), ('Pitalito', '41551'),
    ('San Vicente de Chucurí', '68689'), ('Rionegro', '68615'),
    ('Anorí', '05036'), ('Amalfi', '05030'),
    ('Pensilvania', '17541'), ('Palestina', '17524'),
    ('Villavicencio', '50001'),
    ('El Tambo', '19256'), ('Miranda', '19418'),
    ('Valledupar', '20001'),
]
```

## Lógica de transformación
1. Descargar EVA histórica filtrando por los 15 municipios y los 3 cultivos
2. Renombrar columnas al esquema unificado
3. Convertir `rendimiento_t_ha` a float, marcar como None si no convertible
4. Marcar valores fuera de rango como None (ver rangos en convenciones.md)
5. Agregar columna `fuente = 'historica'`
6. Repetir pasos 1-5 para EVA reciente
7. Concatenar ambos DataFrames → `eva_completa`
8. Guardar los 3 archivos Parquet

## Criterios de aceptación
- [ ] `eva_historica.parquet` existe y tiene registros para años 2007-2018
- [ ] `eva_reciente.parquet` existe y tiene registros para años 2019-2024
- [ ] `eva_completa.parquet` es la unión exacta de los dos anteriores
- [ ] Los 15 municipios del MVP están presentes en `eva_completa`
- [ ] Los 3 cultivos (Café, Cacao, Maíz) están presentes
- [ ] La columna `codigo_dane` tiene siempre 5 caracteres
- [ ] La columna `rendimiento` es float (no string)
- [ ] No hay duplicados por (codigo_dane, cultivo, año, periodo, fuente)
- [ ] El script imprime un resumen: municipios encontrados, años cubiertos, registros por cultivo

## Dependencias
- `shared/dane_codes.py` — mapa nombre → código DANE
- `shared/normalization.py` — función normalize_name()
- `shared/socrata_client.py` — cliente HTTP con reintentos

## Restricciones técnicas
- Paginación: máximo 5000 registros por llamada, usar $offset
- No descargar todos los municipios de Colombia, filtrar por los 15 del MVP
- Usar `requests`, no `sodapy`
- Guardar con `df.to_parquet(path, index=False, engine='pyarrow')`
