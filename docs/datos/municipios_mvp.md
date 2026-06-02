# Municipios del MVP — SiembraSegura IA

15 municipios seleccionados por máxima cobertura de fuentes simultáneas, diversidad geográfica e impacto social. Todos tienen 18 años de datos EVA (2007–2024) y cobertura completa en las 7 fuentes del proyecto.

---

## Tabla de referencia rápida

| # | Municipio | Departamento | Código DANE | Est. IDEAM | Zona PDET | Cultivos con señal |
|---|-----------|-------------|-------------|-----------|-----------|-------------------|
| 1 | Ibagué | Tolima | `73001` | 20 | No | Café✅ Cacao🔥 Maíz✅ |
| 2 | Chaparral | Tolima | `73168` | 13 | ✅ Sí | Café✅ Maíz✅ |
| 3 | Neiva | Huila | `41001` | 10 | No | Café✅ Cacao🔥 Maíz🔥 |
| 4 | Garzón | Huila | `41298` | 9 | No | Café✅ Cacao✅ Maíz🔥 |
| 5 | Pitalito | Huila | `41551` | 6 | No | Café✅ Maíz🔥 |
| 6 | San Vicente de Chucurí | Santander | `68689` | 12 | No | Café✅ Cacao✅ |
| 7 | Rionegro | Santander | `68615` | 19 | No | Café✅ Maíz🔥 |
| 8 | Anorí | Antioquia | `05036` | 14 | ✅ Sí | Café✅ Cacao✅ Maíz✅ |
| 9 | Amalfi | Antioquia | `05030` | 12 | No | Café✅ Cacao✅ |
| 10 | Pensilvania | Caldas | `17541` | 20 | No | Cacao🔥 Maíz🔥 |
| 11 | Palestina | Caldas | `17524` | 13 | No | Café✅ Maíz🔥 |
| 12 | Villavicencio | Meta | `50001` | 15 | No | Café✅ Maíz🔥 |
| 13 | El Tambo | Cauca | `19256` | 12 | ✅ Sí | Café✅ Cacao✅ Maíz🔥 |
| 14 | Miranda | Cauca | `19418` | 12 | No | Café✅ Maíz🔥 |
| 15 | Valledupar | Cesar | `20001` | 14 | No | Café✅ Cacao✅ Maíz✅ |

**Leyenda señal:** ✅ Buena (CV 11–29%) | 🔥 Excelente (CV > 30%) | — Sin datos suficientes

---

## Cobertura de fuentes por municipio

| Municipio | EVA 07-24 | Prec. | Temp. | Hum. | Est. recientes | Aptitud | Frontera | Agroinsumos |
|-----------|-----------|-------|-------|------|---------------|---------|----------|-------------|
| Ibagué | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |
| Chaparral | ✅ | ✅ | ✅ | ✅ | catálogo | ✅ | ✅ | ✅ |
| Neiva | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |
| Garzón | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |
| Pitalito | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |
| San Vicente de Chucurí | ✅ | ✅ | ✅ | ✅ | catálogo | ✅ | ✅ | ✅ |
| Rionegro | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |
| Anorí | ✅ | ✅ | ✅ | ✅ | catálogo | ✅ | ✅ | ✅ |
| Amalfi | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |
| Pensilvania | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |
| Palestina | ✅ | ✅ | ✅ | ✅ | catálogo | ✅ | ✅ | ✅ |
| Villavicencio | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |
| El Tambo | ✅ | ✅ | ✅ | ✅ | catálogo | ✅ | ✅ | ✅ |
| Miranda | ✅ | ✅ | ✅ | ✅ | catálogo | ✅ | ✅ | ✅ |
| Valledupar | ✅ | ✅ | ✅ | ✅ | ✅ directa | ✅ | ✅ | ✅ |

---

## Variabilidad de rendimiento verificada (2019-2024)

CV% = coeficiente de variación. Indica cuánta señal tiene el modelo para aprender. CV > 15% es bueno; CV > 30% es excelente.

| Municipio | Cultivo | Min (t/ha) | Max (t/ha) | Prom (t/ha) | CV% | Señal |
|-----------|---------|-----------|-----------|------------|-----|-------|
| Ibagué | Café | 0.47 | 1.08 | 0.74 | 25.8% | ✅ |
| Ibagué | Cacao | 0.50 | 1.20 | 0.70 | 33.0% | 🔥 |
| Chaparral | Café | 0.60 | 1.28 | 0.88 | 29.4% | ✅ |
| Chaparral | Maíz | 1.00 | 4.00 | 2.37 | 29.4% | ✅ |
| Neiva | Café | 1.00 | 1.49 | 1.26 | 15.1% | ✅ |
| Neiva | Cacao | 0.30 | 0.80 | 0.60 | 31.6% | 🔥 |
| Neiva | Maíz | 1.47 | 5.30 | 3.10 | 47.0% | 🔥 |
| Garzón | Café | 1.25 | 2.31 | 1.61 | 23.0% | ✅ |
| Garzón | Maíz | 1.34 | 7.00 | 3.87 | 47.0% | 🔥 |
| Pitalito | Café | 1.17 | 1.82 | 1.44 | 13.4% | ⚠️ |
| Pitalito | Maíz | 0.31 | 5.50 | 2.87 | 56.9% | 🔥 |
| San Vicente de Chucurí | Café | 0.61 | 1.09 | 0.87 | 21.0% | ✅ |
| San Vicente de Chucurí | Cacao | 0.51 | 0.60 | 0.57 | 7.4% | ⚠️ |
| Rionegro | Café | 0.94 | 1.36 | 1.17 | 11.5% | ⚠️ |
| Rionegro | Maíz | 0.70 | 5.81 | 1.84 | 78.6% | 🔥 |
| Anorí | Café | 0.83 | 1.34 | 1.10 | 15.5% | ✅ |
| Anorí | Maíz | 0.70 | 1.20 | 0.78 | 18.4% | ✅ |
| Amalfi | Café | 0.67 | 1.31 | 0.94 | 25.6% | ✅ |
| Amalfi | Cacao | 0.47 | 1.00 | 0.83 | 29.3% | ✅ |
| Pensilvania | Cacao | 0.50 | 2.00 | 0.78 | 69.7% | 🔥 |
| Pensilvania | Maíz | 1.00 | 5.00 | 1.53 | 71.6% | 🔥 |
| Palestina | Café | 0.74 | 1.65 | 1.21 | 18.8% | ✅ |
| Palestina | Maíz | 0.39 | 7.00 | 3.01 | 55.5% | 🔥 |
| Villavicencio | Café | 0.72 | 1.31 | 1.00 | 23.0% | ✅ |
| Villavicencio | Maíz | 1.31 | 8.75 | 4.64 | 46.0% | 🔥 |
| El Tambo | Cacao | 0.35 | 0.80 | 0.68 | 27.0% | ✅ |
| El Tambo | Maíz | 1.00 | 6.00 | 2.11 | 63.3% | 🔥 |
| Miranda | Café | 0.85 | 1.30 | 1.09 | 15.2% | ✅ |
| Miranda | Maíz | 1.12 | 4.10 | 2.71 | 46.6% | 🔥 |
| Valledupar | Café | 0.71 | 1.25 | 0.97 | 19.6% | ✅ |

---

## Mapa de códigos DANE

Para uso directo en filtros SoQL y como llave de unión entre datasets:

```python
MVP_CODIGOS = [
    '73001',  # Ibagué
    '73168',  # Chaparral
    '41001',  # Neiva
    '41298',  # Garzón
    '41551',  # Pitalito
    '68689',  # San Vicente de Chucurí
    '68615',  # Rionegro
    '05036',  # Anorí
    '05030',  # Amalfi
    '17541',  # Pensilvania
    '17524',  # Palestina
    '50001',  # Villavicencio
    '19256',  # El Tambo
    '19418',  # Miranda
    '20001',  # Valledupar
]
```

> Estos códigos están definidos en `shared/dane_codes.py → MVP_CODIGOS`. No redefinirlos en otros módulos.

---

## Notas por municipio

**Ibagué** — Hub de datos más rico de Tolima. 20 estaciones IDEAM. Los 3 cultivos con buena señal. Capital departamental.

**Chaparral** — Zona PDET. Municipio rural vulnerable. Alta variabilidad en café y maíz. Sin estaciones recientes en `57sv-p2fu` — usar catálogo histórico.

**Pitalito** — Mayor productor de café especial de Colombia. Maíz con CV 57%. Solo 6 estaciones IDEAM pero cobertura completa.

**San Vicente de Chucurí** — Capital cacaotera de Colombia. Referente nacional para cacao. Cacao con CV bajo (7.4%) — señal moderada para el modelo.

**Rionegro (Santander)** — 19 estaciones IDEAM. Maíz con CV 79% — mayor señal climática del grupo. No confundir con Rionegro (Antioquia), que no está en el MVP.

**Pensilvania** — 20 estaciones IDEAM. Cacao CV 70%, maíz CV 72% — señal excepcional en ambos cultivos.

**Palestina** — Corazón del Eje Cafetero. Cerca de Manizales (precios RAP disponibles). Sin estaciones recientes — usar catálogo histórico.

**El Tambo** — Zona PDET. Maíz CV 63%. Los 3 cultivos presentes. Sin estaciones recientes — usar catálogo histórico.

**Anorí** — Zona PDET. 14 estaciones. Los 3 cultivos con buena señal. Sin estaciones recientes — usar catálogo histórico.
