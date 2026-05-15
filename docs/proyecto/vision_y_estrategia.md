# Visión y estrategia — SiembraSegura IA

## Qué es el proyecto

**SiembraSegura IA** es una plataforma web que predice rendimiento agrícola y riesgo climático por municipio y cultivo en Colombia, integrando datos abiertos de EVA, IDEAM, UPRA y agroinsumos. Permite a productores, extensionistas y entidades municipales tomar decisiones informadas sobre qué cultivo sembrar, cuándo y con qué riesgo esperado.

---

## El problema que resuelve

Muchos municipios productores tienen variabilidad fuerte de precipitación y temperatura. Un productor, una UMATA o una secretaría de agricultura puede ver datos históricos, pero no tiene una herramienta que diga:

> "Para este municipio y este cultivo, el riesgo de bajo rendimiento está aumentando por déficit de lluvia, exceso de temperatura o acumulación anormal de precipitación."

Sin cruzar EVA + IDEAM + UPRA, el productor o planificador no tiene una recomendación objetiva. La solución convierte datos técnicos complejos en una decisión simple y accionable.

---

## Usuarios objetivo

| Usuario | Necesidad principal |
|---------|-------------------|
| **Extensionista / UMATA** | Saber qué municipios tienen mayor riesgo para priorizar visitas técnicas |
| **Productor organizado** | Decidir qué cultivo sembrar y cuándo, con respaldo de datos |
| **Secretaría de agricultura** | Planificar asistencia técnica y activar seguros agrícolas |
| **Asociación productiva** | Anticipar caídas de rendimiento para gestionar inventarios y precios |

El diseño prioriza **UMATAs y extensionistas** como usuarios primarios. El lenguaje de la interfaz y los reportes debe ser accesible para técnicos de campo, no solo para científicos de datos.

---

## Qué entrega la plataforma

Para cada combinación `municipio + cultivo + periodo`, la plataforma entrega:

1. **Rendimiento esperado** — predicción en t/ha con XGBoost Regressor
2. **Semáforo de riesgo** — Bajo / Medio / Alto con probabilidad
3. **Factores explicativos** — top 5 variables que explican el riesgo (SHAP)
4. **Aptitud territorial** — porcentaje de área en aptitud alta/media/baja (UPRA)
5. **Riesgo económico** — señal basada en índice de agroinsumos + precio regional
6. **Recomendación accionable** — texto en lenguaje claro para el usuario
7. **Reporte automático** — PDF/texto listo para compartir por WhatsApp o imprimir
8. **Asistente IA** — responde preguntas en lenguaje natural usando resultados del modelo

---

## Cultivos del MVP

| Cultivo | Justificación |
|---------|--------------|
| **Café** | Alto impacto social, pequeños productores, sensible a clima, aptitud UPRA disponible |
| **Cacao** | Zonas rurales vulnerables, PDET, sustitución de cultivos, aptitud UPRA disponible |
| **Maíz** | Seguridad alimentaria, alta variabilidad climática (CV 30–78%), cultivo transitorio |

Tres cultivos bien resueltos es mejor que diez superficialmente cubiertos.

---

## Cobertura geográfica del MVP

**15 municipios** seleccionados por máxima cobertura de fuentes simultáneas (ver `docs/datos/municipios_mvp.md`):

- 8 departamentos: Tolima, Huila, Santander, Antioquia, Caldas, Meta, Cauca, Cesar
- 3 zonas PDET: Chaparral, Anorí, El Tambo
- 18 años de datos EVA (2007–2024) en todos los municipios

---

## Diferenciadores frente a soluciones tradicionales

| Solución tradicional | SiembraSegura IA |
|---------------------|-----------------|
| Muestra clima histórico | Calcula riesgo productivo futuro |
| Muestra producción pasada | Predice rendimiento esperado |
| Dashboard descriptivo | Recomendación accionable |
| Sin explicación del resultado | Explica factores de riesgo con SHAP |
| Usa datos aislados | Cruza EVA + IDEAM + UPRA + agroinsumos |
| Solo para expertos | Diseñado para extensionistas y productores |

---

## Errores críticos a evitar

### Errores técnicos
1. **Fuga de información**: no usar `producción` ni `área_cosechada` del mismo año como variables predictoras — el rendimiento se calcula a partir de ellas.
2. **Split aleatorio**: en series temporales agrícolas se valida por años futuros, nunca mezclando pasado y futuro.
3. **Descargar IDEAM sin agregación**: son millones de registros. Usar agregaciones por municipio/mes/año.
4. **Predecir a nivel finca**: los datos EVA son municipales. No prometer precisión de parcela.
5. **No unificar códigos DANE**: usar nombres de municipios falla por tildes y variaciones. Siempre usar código DANE de 5 dígitos como llave.

### Errores estratégicos
1. **Hacer solo un dashboard descriptivo**: no se siente como IA aplicada.
2. **No conectar con decisiones reales**: el usuario debe saber qué hacer con el resultado.
3. **Sobrecomplicar con deep learning**: un XGBoost bien validado y explicable gana más que una red neuronal mal calibrada en 1 mes.
4. **No mostrar trazabilidad de datos**: el jurado debe ver qué datasets se usaron y cómo.

---

## Plan de trabajo de 4 semanas

| Semana | Foco | Entregables |
|--------|------|-------------|
| 1 | Datos | Pipelines D1–D4 + tabla maestra D5 |
| 2 | Modelo | Features M1 + modelos M2–M3 + SHAP M4 + escenarios M5 |
| 3 | Producto | API A1–A4 + frontend F1–F4 |
| 4 | Demo | Asistente C1–C3 + pitch + ensayo demo |

---

## Criterios de éxito para la demo

La demo debe mostrar en este orden:
1. Mapa nacional coloreado por nivel de riesgo, filtrado por cultivo
2. Click en un municipio rural → ficha con rendimiento histórico + predicción + semáforo
3. Comparación de 2–3 cultivos en el mismo municipio
4. Factores SHAP que explican el riesgo
5. Generación de reporte automático
6. Pregunta al asistente IA: "Explícame este riesgo en lenguaje sencillo para un productor"
7. Trazabilidad: mostrar qué datasets se usaron (EVA + IDEAM + UPRA + agroinsumos)
