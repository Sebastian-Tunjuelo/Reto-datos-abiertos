# Conocimiento de la API datos.gov.co — Socrata

## Cómo funciona la API
- Base URL: `https://www.datos.gov.co/resource/{dataset_id}.json`
- Protocolo: REST, responde JSON
- Librería Python recomendada: `requests`
- Límite por defecto: 1000 registros. Siempre usar `$limit` explícito.
- Paginación: usar `$offset`. Máximo práctico por llamada: 5000 registros.
- Filtros: parámetro `$where` con sintaxis SoQL
- Agregaciones: `$select` con `count()`, `sum()`, `avg()` + `$group`

## Truco crítico para datasets con geometrías (UPRA)
Los datasets de aptitud UPRA tienen 400k-500k registros con geometrías MultiPolygon.
**NUNCA descargar sin GROUP BY** — se cuelga.
Siempre usar:
```
$select=municipio,departamen,cod_dane_m,aptitud&$group=municipio,departamen,cod_dane_m,aptitud&$limit=5000
```

## Datasets y sus columnas reales (verificadas en producción)

### EVA reciente 2019-2024 — `uejq-wxrr`
- `municipio` — Title Case con tildes (ej: "Ibagué")
- `departamento` — Title Case
- `c_digo_dane_municipio` — código DANE 5 dígitos
- `cultivo` — "Café", "Cacao", "Maíz"
- `a_o` — año como string
- `periodo` — "2022A", "2022B"
- `rendimiento` — t/ha como string → convertir a float
- `rea_sembrada`, `rea_cosechada`, `producci_n`
- `ciclo_del_cultivo` — "PERMANENTE" o "TRANSITORIO"

### EVA histórica 2007-2018 — `2pnw-mmge`
- `municipio` — MAYÚSCULAS (ej: "IBAGUÉ")
- `departamento` — MAYÚSCULAS
- `c_d_mun` — código DANE
- `cultivo` — MAYÚSCULAS: "CAFÉ", "CACAO", "MAÍZ"
- `a_o` — año
- `rendimiento_t_ha`, `rea_sembrada_ha`, `rea_cosechada_ha`, `producci_n_t`
- `ciclo_de_cultivo`

> ⚠️ Columnas con nombres DISTINTOS entre las dos versiones de EVA. Normalizar al unir.

### Catálogo estaciones IDEAM — `hp9r-jxuu`
- `codigo`, `nombre`, `categoria`, `estado`
- `municipio` (Title Case), `departamento`
- `latitud`, `longitud`, `altitud`
- Categorías con temperatura: "Climatológica Principal", "Climatológica Ordinaria", "Agrometeorológica"
- Categorías con precipitación: todas las anteriores + "Pluviométrica", "Pluviográfica"

### Precipitación IDEAM — `s54a-sgyg`
- `codigoestacion`, `fechaobservacion`, `valorobservado` (mm)
- `municipio` (MAYÚSCULAS), `departamento` (MAYÚSCULAS)
- `latitud`, `longitud`, `descripcionsensor`, `unidadmedida`
- ⚠️ Dataset enorme. Filtrar siempre por estación o municipio. Agregar por mes/año.

### Temperatura IDEAM — `sbwg-7ju4`
Misma estructura que precipitación.

### Humedad IDEAM — `uext-mhny`
Misma estructura.

### Estaciones recientes — `57sv-p2fu`
Misma estructura. Múltiples sensores. Datos casi en tiempo real.

### Aptitud café UPRA — `kwvf-nwea`
- `municipio`, `departamen` (truncado), `cod_dane_m`
- `aptitud`: "Aptitud alta", "Aptitud media", "Aptitud baja", "No apta", "Exclusión legal"
- `area_ha` (string)

### Aptitud cacao — `jdjx-qer4` | Maíz tradicional — `frjn-92um`
### Maíz tec 1er sem — `a5yc-uszt` | Maíz tec 2do sem — `tzga-4zse`
Misma estructura que café. Para maíz usar UNIÓN de los 3 datasets.

### Frontera agrícola — `fyc7-sbtz`
- `municipio`, `departamen`, `cod_dane_m`
- `tipo_front`: "Condicionada" / "No condicionada"

### Índice agroinsumos — `gwbi-fnzs`
- `fecha`, `indice_total`, `total_fertilizantes`, `total_plaguicidas`
- `urea_46`, `dap_18_46`, `kcl_0_0_60`
- Dataset pequeño (~200 registros). Descargar completo.

## Normalización de nombres de municipios
```python
import unicodedata
def normalize_name(name: str) -> str:
    name = name.strip().upper()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name
```

## Rangos de rendimiento válidos (para limpieza)
| Cultivo | Mín | Máx | Unidad |
|---------|-----|-----|--------|
| Café | 0.3 | 3.0 | t/ha |
| Cacao | 0.2 | 2.5 | t/ha |
| Maíz tradicional | 0.5 | 4.0 | t/ha |
| Maíz tecnificado | 2.0 | 10.0 | t/ha |
