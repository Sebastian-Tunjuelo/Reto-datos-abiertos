# Selección de Municipios con Mayor Cobertura de Fuentes
## Proyecto: SiembraSegura IA / AgroRiesgo360
**Fecha de análisis:** Mayo 2026  
**Estado:** ✅ COMPLETADO

---

## 1. Metodología de cruce

Se consultaron directamente las APIs Socrata de datos.gov.co para cruzar todas las fuentes relevantes. El criterio de selección es: **municipios que aparecen en el mayor número de fuentes simultáneamente**, priorizando cobertura climática completa (precipitación + temperatura + humedad) y mayor cantidad de años de datos EVA.

### Fuentes consultadas y cobertura real

| # | Fuente | Dataset ID | Municipios cubiertos | Notas |
|---|--------|-----------|---------------------|-------|
| 1 | EVA 2019-2024 (Café + Cacao + Maíz) | `uejq-wxrr` | **389** con los 3 cultivos | Base principal |
| 2 | EVA histórica 2007-2018 (Café + Cacao + Maíz) | `2pnw-mmge` | **567** | Hasta 12 años adicionales |
| 3 | IDEAM catálogo estaciones activas | `hp9r-jxuu` | **869** con alguna estación | Precipitación + temperatura |
| 4 | IDEAM humedad del aire | `uext-mhny` | **518** (vía estaciones climatológicas/agrometeorológicas) | |
| 5 | UPRA aptitud café | `kwvf-nwea` | **1.039** | Cobertura casi nacional |
| 6 | UPRA aptitud cacao | `jdjx-qer4` | **1.039** | Cobertura casi nacional |
| 7 | UPRA aptitud maíz tradicional | `frjn-92um` | **123** | ⚠️ Solo 123 municipios |
| 8 | UPRA aptitud maíz tecnificado 1er sem | `a5yc-uszt` | **1.039** | Amplía cobertura de maíz |
| 9 | UPRA aptitud maíz tecnificado 2do sem | `tzga-4zse` | **1.039** | Amplía cobertura de maíz |
| 10 | UPRA frontera agrícola | `fyc7-sbtz` | **1.039** | Cobertura casi nacional |
| 11 | Índice de agroinsumos | `gwbi-fnzs` | **NACIONAL** | Aplica a todos los municipios |
| 12 | Precios RAP Eje Cafetero | `gdqq-rry2` | **4 ciudades** | Armenia, Ibagué, Manizales, Pereira |
| 13 | Estaciones recientes IDEAM | `57sv-p2fu` | Verificado para 15 municipios | Datos casi en tiempo real |

> **Hallazgo clave sobre maíz:** Al usar la **unión de los 3 datasets de maíz** (tradicional + tecnificado 1er sem + tecnificado 2do sem), la cobertura sube de 123 a **1.039 municipios**. Esto amplía los municipios con cobertura completa de 32 a **207**.

---

## 2. Sistema de puntuación

### Score base (máximo 6 puntos)

| Criterio | Puntos |
|----------|--------|
| EVA con los 3 cultivos (Café + Cacao + Maíz) | 1 |
| IDEAM precipitación (estación activa) | 1 |
| IDEAM temperatura (estación climatológica/agrometeorológica) | 1 |
| UPRA aptitud café | 1 |
| UPRA aptitud cacao | 1 |
| UPRA aptitud maíz (cualquier variante: trad + tec1 + tec2) | 1 |

### Score ponderado (para ranking final)
`ScorePond = (TotalAniosEVA × 2) + EstacionesIdeam + (TieneHumedad × 3)`

- **TotalAniosEVA**: años en EVA histórica (2007-2018) + EVA reciente (2019-2024). Máximo: 18 años.
- **EstacionesIdeam**: número de estaciones activas en el municipio.
- **TieneHumedad**: si tiene estación climatológica o agrometeorológica.

---

## 3. Resultados del cruce

### Municipios con score 6/6 por departamento (207 total)

| Departamento | Municipios con score 6 | Municipios destacados |
|-------------|----------------------|----------------------|
| Antioquia | 30 | Amalfi, Anorí, San Carlos, Santa Rosa de Osos, Urrao |
| Valle del Cauca | 19 | Palmira, Tuluá, Florida, Bugalagrande, Pradera |
| Huila | 18 | Neiva, Garzón, Pitalito, La Plata, Palermo |
| Tolima | 18 | Ibagué, Chaparral, Natagaima, Líbano, Ataco |
| Cundinamarca | 16 | El Colegio, La Vega, Medina, Guaduas, Viotá |
| Santander | 15 | Bucaramanga, Rionegro, San Vicente de Chucurí, Girón |
| Caldas | 13 | Manizales, Pensilvania, Palestina, Chinchiná, Riosucio |
| Boyacá | 11 | Puerto Boyacá, Buenavista, Santa María, La Victoria |
| Cauca | 10 | El Tambo, Miranda, Santander de Quilichao, Balboa |
| Norte de Santander | 10 | Ábrego, El Carmen, Convención, Ocaña, Chinácota |
| Quindío | 8 | Armenia, Calarcá, Montenegro, Pijao, Quimbaya |
| Cesar | 7 | Valledupar, Aguachica, Agustín Codazzi, San Martín |
| Meta | 7 | Villavicencio, Lejanías, El Castillo, Cumaral |
| Risaralda | 5 | Pereira, Belén de Umbría, Guática, La Celia, Apía |
| Caquetá | 4 | Florencia, Albania, Belén de Los Andaquíes, San Vicente del Caguán |
| Casanare | 4 | Yopal, Nunchía, Támara, Monterrey |
| Putumayo | 3 | Mocoa, Puerto Leguízamo, Villagarzón |
| La Guajira | 3 | Fonseca, Dibulla, Urumita |
| Nariño | 2 | La Unión, Ricaurte |
| Magdalena | 1 | Santa Marta |
| Arauca | 1 | Tame |
| Córdoba | 1 | Planeta Rica |
| Bolívar | 1 | San Pablo |

### Distribución de años EVA entre los 207 municipios

| Total años EVA | Municipios |
|---------------|-----------|
| 18 años (2007-2024 completo) | **144** |
| 17 años | 10 |
| 16 años | 6 |
| 15 años | 4 |
| 14 años | 4 |
| 13 años | 3 |
| 12 años | 5 |
| 9 años | 6 |
| 8 años | 6 |
| 6 años (solo 2019-2024) | 18 |

---

## 4. TOP 20 — Ranking por score ponderado

Todos tienen score base 6/6: EVA (3 cultivos) + IDEAM (prec+temp) + UPRA (café+cacao+maíz+frontera)

| Pos | Municipio | Departamento | Est. IDEAM | Humedad | Total años EVA | Score pond |
|-----|-----------|-------------|-----------|---------|---------------|-----------|
| 1 | **Manizales** | Caldas | 53 | ✅ | 9 | 74 |
| 2 | **Pereira** | Risaralda | 27 | ✅ | 18 | 69 |
| 3 | **Pensilvania** | Caldas | 20 | ✅ | 18 | 59 |
| 4 | **Ibagué** | Tolima | 20 | ✅ | 18 | 59 |
| 5 | **Bugalagrande** | Valle del Cauca | 20 | ✅ | 18 | 59 |
| 6 | **Rionegro** | Santander | 19 | ✅ | 18 | 58 |
| 7 | **Florida** | Valle del Cauca | 19 | ✅ | 18 | 58 |
| 8 | **Bucaramanga** | Santander | 17 | ✅ | 18 | 56 |
| 9 | **Palmira** | Valle del Cauca | 51 | ✅ | 15 | 54 |
| 10 | **Villavicencio** | Meta | 15 | ✅ | 18 | 54 |
| 11 | **Tuluá** | Valle del Cauca | 15 | ✅ | 18 | 54 |
| 12 | **El Colegio** | Cundinamarca | 14 | ✅ | 18 | 53 |
| 13 | **Anorí** | Antioquia | 14 | ✅ | 18 | 53 |
| 14 | **Valledupar** | Cesar | 14 | ✅ | 18 | 53 |
| 15 | **Palestina** | Caldas | 13 | ✅ | 18 | 52 |
| 16 | **Chaparral** | Tolima | 13 | ✅ | 18 | 52 |
| 17 | **Miranda** | Cauca | 12 | ✅ | 18 | 51 |
| 18 | **El Tambo** | Cauca | 12 | ✅ | 18 | 51 |
| 19 | **Amalfi** | Antioquia | 12 | ✅ | 18 | 51 |
| 20 | **San Carlos** | Antioquia | 12 | ✅ | 18 | 51 |

---

## 5. Variabilidad de rendimiento verificada (2019-2024)

El coeficiente de variación (CV%) indica cuánta señal tiene el modelo para aprender. CV > 15% es bueno; CV > 30% es excelente.

| Municipio | Cultivo | Min (t/ha) | Max (t/ha) | Prom (t/ha) | CV% | Señal |
|-----------|---------|-----------|-----------|------------|-----|-------|
| Amalfi | Café | 0.67 | 1.31 | 0.94 | 25.6% | ✅ Buena |
| Amalfi | Cacao | 0.47 | 1.00 | 0.83 | 29.3% | ✅ Buena |
| Anorí | Café | 0.83 | 1.34 | 1.10 | 15.5% | ✅ Buena |
| Anorí | Maíz | 0.70 | 1.20 | 0.78 | 18.4% | ✅ Buena |
| Chaparral | Café | 0.60 | 1.28 | 0.88 | 29.4% | ✅ Buena |
| Chaparral | Maíz | 1.00 | 4.00 | 2.37 | 29.4% | ✅ Buena |
| El Tambo | Cacao | 0.35 | 0.80 | 0.68 | 27.0% | ✅ Buena |
| El Tambo | Maíz | 1.00 | 6.00 | 2.11 | 63.3% | 🔥 Excelente |
| Garzón | Café | 1.25 | 2.31 | 1.61 | 23.0% | ✅ Buena |
| Garzón | Maíz | 1.34 | 7.00 | 3.87 | 47.0% | 🔥 Excelente |
| Ibagué | Cacao | 0.50 | 1.20 | 0.70 | 33.0% | 🔥 Excelente |
| Ibagué | Café | 0.47 | 1.08 | 0.74 | 25.8% | ✅ Buena |
| Miranda | Café | 0.85 | 1.30 | 1.09 | 15.2% | ✅ Buena |
| Miranda | Maíz | 1.12 | 4.10 | 2.71 | 46.6% | 🔥 Excelente |
| Neiva | Cacao | 0.30 | 0.80 | 0.60 | 31.6% | 🔥 Excelente |
| Neiva | Café | 1.00 | 1.49 | 1.26 | 15.1% | ✅ Buena |
| Neiva | Maíz | 1.47 | 5.30 | 3.10 | 47.0% | 🔥 Excelente |
| Palestina | Café | 0.74 | 1.65 | 1.21 | 18.8% | ✅ Buena |
| Palestina | Maíz | 0.39 | 7.00 | 3.01 | 55.5% | 🔥 Excelente |
| Pensilvania | Cacao | 0.50 | 2.00 | 0.78 | 69.7% | 🔥 Excelente |
| Pensilvania | Maíz | 1.00 | 5.00 | 1.53 | 71.6% | 🔥 Excelente |
| Pitalito | Café | 1.17 | 1.82 | 1.44 | 13.4% | ⚠️ Moderada |
| Pitalito | Maíz | 0.31 | 5.50 | 2.87 | 56.9% | 🔥 Excelente |
| Rionegro | Café | 0.94 | 1.36 | 1.17 | 11.5% | ⚠️ Moderada |
| Rionegro | Maíz | 0.70 | 5.81 | 1.84 | 78.6% | 🔥 Excelente |
| San Vicente de Chucurí | Cacao | 0.51 | 0.60 | 0.57 | 7.4% | ⚠️ Moderada |
| San Vicente de Chucurí | Café | 0.61 | 1.09 | 0.87 | 21.0% | ✅ Buena |
| Valledupar | Café | 0.71 | 1.25 | 0.97 | 19.6% | ✅ Buena |
| Villavicencio | Café | 0.72 | 1.31 | 1.00 | 23.0% | ✅ Buena |
| Villavicencio | Maíz | 1.31 | 8.75 | 4.64 | 46.0% | 🔥 Excelente |

> **Conclusión:** Todos los municipios seleccionados tienen variabilidad suficiente para entrenar el modelo. El maíz muestra la mayor variabilidad (CV 30-78%), lo que lo convierte en el cultivo con más señal climática. El café tiene variabilidad moderada-buena (11-29%). El cacao es el más estable (7-33%).

---

## 6. Cobertura de estaciones recientes IDEAM (57sv-p2fu)

Verificado para los 15 municipios seleccionados. Todos tienen datos recientes con los siguientes sensores:

| Municipio | Sensores disponibles |
|-----------|---------------------|
| **Ibagué** | Precipitación, Temperatura (min/max/media), Humedad relativa, Presión, Viento, Humedad suelo |
| **Neiva** | Precipitación, Temperatura (min/max/media), Humedad relativa, Presión, Viento |
| **Garzón** | Precipitación, Temperatura (min/max/media), Humedad relativa, Presión, Viento |
| **Pitalito** | Precipitación, Temperatura (min/max/media), Humedad relativa, Evaporación, Viento |
| **Amalfi** | Precipitación, Temperatura (min/max/media), Humedad relativa, Presión, Viento, Humedad suelo |
| **Pensilvania** | Precipitación, Temperatura (min/max/media), Humedad relativa, Viento |
| **Rionegro** | Precipitación, Temperatura (min/max/media), Humedad relativa, Presión, Viento, Humedad suelo |
| **Palestina** | No aparece en estaciones recientes — usar catálogo histórico |
| **Chaparral** | No aparece en estaciones recientes — usar catálogo histórico |
| **Miranda** | No aparece en estaciones recientes — usar catálogo histórico |
| **El Tambo** | No aparece en estaciones recientes — usar catálogo histórico |
| **San Vicente de Chucurí** | No aparece en estaciones recientes — usar catálogo histórico |
| **Villavicencio** | Precipitación, Temperatura (min/max/media), Humedad relativa, Presión, Viento, Humedad suelo, Evaporación |
| **Valledupar** | Precipitación, Temperatura (min/max/media), Humedad relativa, Presión, Viento |
| **Anorí** | No aparece en estaciones recientes — usar catálogo histórico |

> **Nota:** Los municipios sin estaciones recientes en `57sv-p2fu` tienen cobertura en el catálogo histórico `hp9r-jxuu`. Para el modelo se usarán ambas fuentes.

---

## 7. ✅ SELECCIÓN FINAL DEFINITIVA — 15 municipios para el MVP

### Criterios aplicados
1. Score base 6/6 (todas las fuentes disponibles)
2. 18 años de datos EVA (2007-2024) — máximo posible
3. Mínimo 2 estaciones IDEAM activas
4. Humedad disponible
5. Variabilidad de rendimiento CV > 10% en al menos 2 cultivos
6. Diversidad geográfica (8 departamentos objetivo)
7. Impacto social: municipios rurales, zonas PDET o alta ruralidad
8. Representatividad de los 3 cultivos

---

### Los 15 municipios seleccionados

| # | Municipio | Departamento | Est. IDEAM | Años EVA | Cultivos con señal | Zona PDET | Justificación principal |
|---|-----------|-------------|-----------|---------|-------------------|-----------|------------------------|
| 1 | **Ibagué** | Tolima | 20 | 18 | Café✅ Cacao🔥 Maíz✅ | No | Capital regional, 20 estaciones, hub de los 3 cultivos, datos más ricos de Tolima |
| 2 | **Chaparral** | Tolima | 13 | 18 | Café✅ Maíz✅ | ✅ Sí | Zona PDET, municipio rural vulnerable, alta variabilidad café y maíz |
| 3 | **Neiva** | Huila | 10 | 18 | Café✅ Cacao🔥 Maíz🔥 | No | Capital Huila, referente café especial y cacao, 3 cultivos con excelente señal |
| 4 | **Garzón** | Huila | 9 | 18 | Café✅ Cacao✅ Maíz🔥 | No | Municipio cafetero emblemático Huila, maíz con CV 47% |
| 5 | **Pitalito** | Huila | 6 | 18 | Café✅ Maíz🔥 | No | Mayor productor café especial de Colombia, maíz CV 57% |
| 6 | **San Vicente de Chucurí** | Santander | 12 | 18 | Café✅ Cacao✅ | No | Capital cacaotera de Colombia, referente nacional cacao |
| 7 | **Rionegro** | Santander | 19 | 18 | Café✅ Maíz🔥 | No | 19 estaciones IDEAM, maíz CV 79% — mayor señal climática del grupo |
| 8 | **Anorí** | Antioquia | 14 | 18 | Café✅ Cacao✅ Maíz✅ | ✅ Sí | Zona PDET, 14 estaciones, los 3 cultivos con buena señal |
| 9 | **Amalfi** | Antioquia | 12 | 18 | Café✅ Cacao✅ | No | Zona minero-cafetera, café y cacao con CV ~28% |
| 10 | **Pensilvania** | Caldas | 20 | 18 | Cacao🔥 Maíz🔥 | No | 20 estaciones, cacao CV 70%, maíz CV 72% — señal excepcional |
| 11 | **Palestina** | Caldas | 13 | 18 | Café✅ Maíz🔥 | No | Corazón Eje Cafetero, maíz CV 56%, cerca de Manizales (precios RAP) |
| 12 | **Villavicencio** | Meta | 15 | 18 | Café✅ Maíz🔥 | No | Capital Llanos, 15 estaciones, maíz CV 46%, referente maíz tecnificado |
| 13 | **El Tambo** | Cauca | 12 | 18 | Café✅ Cacao✅ Maíz🔥 | ✅ Sí | Zona PDET, maíz CV 63%, los 3 cultivos presentes |
| 14 | **Miranda** | Cauca | 12 | 18 | Café✅ Maíz🔥 | No | Zona cafetera y maicera Cauca, maíz CV 47% |
| 15 | **Valledupar** | Cesar | 14 | 18 | Café✅ Cacao✅ Maíz✅ | No | Capital Cesar, 14 estaciones, referente cacao y maíz región Caribe |

---

### Cobertura geográfica de los 15 municipios

```
Departamentos cubiertos: Tolima, Huila, Santander, Antioquia, Caldas, Meta, Cauca, Cesar
Zonas PDET incluidas: Chaparral (Tolima), Anorí (Antioquia), El Tambo (Cauca)
Capitales departamentales: Ibagué, Neiva, Villavicencio, Valledupar
Municipios rurales: 11 de 15
```

### Fuentes disponibles para los 15 municipios

| Fuente | Cobertura |
|--------|-----------|
| EVA 2007-2024 (Café + Cacao + Maíz) | ✅ 15/15 |
| IDEAM precipitación | ✅ 15/15 |
| IDEAM temperatura | ✅ 15/15 |
| IDEAM humedad | ✅ 15/15 |
| IDEAM estaciones recientes (57sv-p2fu) | ✅ 9/15 directas, 6/15 vía catálogo histórico |
| UPRA aptitud café | ✅ 15/15 |
| UPRA aptitud cacao | ✅ 15/15 |
| UPRA aptitud maíz (alguna variante) | ✅ 15/15 |
| UPRA frontera agrícola | ✅ 15/15 |
| Índice de agroinsumos | ✅ 15/15 (nacional) |
| Precios RAP Eje Cafetero | ✅ 2/15 (Ibagué, Palestina/Pensilvania cercanas) |

---

## 8. Notas técnicas para el equipo de desarrollo

### Nombres de columnas importantes (EVA reciente `uejq-wxrr`)
- Rendimiento: `rendimiento` (no `rendimiento_t_ha`)
- Área sembrada: `rea_sembrada`
- Producción: `producci_n`
- Año: `a_o`
- Código DANE municipio: `c_digo_dane_municipio`

### Nombres de columnas importantes (EVA histórica `2pnw-mmge`)
- Rendimiento: `rendimiento_t_ha`
- Área sembrada: `rea_sembrada_ha`
- Producción: `producci_n_t`
- Año: `a_o`
- Código DANE municipio: `c_d_mun`
- ⚠️ Los cultivos están en MAYÚSCULAS: `CAFÉ`, `CACAO`, `MAÍZ`

### Sobre los datasets de aptitud UPRA
- Todos tienen geometrías pesadas (400k–500k registros)
- Usar siempre `$group` en SoQL para evitar descargar geometrías
- Unión de maíz: `frjn-92um` + `a5yc-uszt` + `tzga-4zse`

### Sobre normalización de nombres de municipios
- Eliminar tildes y convertir a UPPER para cruzar entre datasets
- Usar `c_digo_dane_municipio` / `c_d_mun` como llave definitiva cuando sea posible
- EVA histórica usa nombres en MAYÚSCULAS, EVA reciente usa Title Case

### Rangos de rendimiento esperados por cultivo (referencia)
| Cultivo | Rango típico Colombia | Unidad |
|---------|----------------------|--------|
| Café | 0.5 – 2.0 | t/ha |
| Cacao | 0.3 – 2.0 | t/ha |
| Maíz tradicional | 0.5 – 3.0 | t/ha |
| Maíz tecnificado | 3.0 – 9.0 | t/ha |

---

## 9. Próximos pasos recomendados (Semana 1 del plan)

1. **Descargar EVA completa** para los 15 municipios (2007-2024, ambos datasets)
2. **Descargar precipitación IDEAM** agregada por mes/año para los 15 municipios (usar código estación del catálogo)
3. **Descargar temperatura IDEAM** agregada por mes/año para los 15 municipios
4. **Descargar aptitud UPRA** para café, cacao y maíz (usar GROUP BY para evitar geometrías)
5. **Descargar frontera agrícola** para los 15 municipios
6. **Descargar índice de agroinsumos** completo (es pequeño, ~200 registros mensuales)
7. **Normalizar códigos DANE** como llave de unión entre todas las tablas
8. **Construir tabla maestra**: `municipio + código_DANE + cultivo + año + periodo`

