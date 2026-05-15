# Investigación estratégica para el reto de Agricultura y Desarrollo Rural

Voy a pensarlo como jurado: la idea ganadora no debería ser solo “un modelo que predice rendimiento”. Eso lo van a proponer muchos equipos. La propuesta competitiva debe convertirse en una herramienta de decisión: **qué cultivo sembrar, dónde, cuándo, con qué riesgo climático y con qué expectativa productiva/económica**, usando datos abiertos verificables.

Mi recomendación final será construir un sistema tipo **“semáforo agroclimático municipal”** para priorizar cultivos y anticipar caídas de rendimiento.

---

# 1. PROBLEMAS ESPECÍFICOS — ENFOQUE ESTRATÉGICO

## Priorización general

| Prioridad | Problema concreto | Impacto en Colombia | Datos abiertos | Viabilidad 1 mes | Potencial hackathon |
|---:|---|---:|---:|---:|---:|
| 1 | Predicción de caída de rendimiento por anomalías de lluvia/temperatura en cultivos clave | Muy alto | Muy alto | Alta | Muy alto |
| 2 | Decisiones de siembra en municipios con baja aptitud o alta restricción agropecuaria | Muy alto | Muy alto | Alta-media | Muy alto |
| 3 | Riesgo económico por precios de mercado e insumos agrícolas | Alto | Medio-alto | Alta | Alto |
| 4 | Alertas de abastecimiento/precio para productos perecederos regionales | Medio-alto | Medio | Media | Medio-alto |
| 5 | Calidad/anomalías de datos meteorológicos para decisiones rurales | Medio | Alto | Alta | Medio |

---

## Problema 1 — Caídas de rendimiento agrícola por eventos climáticos no anticipados

### Qué ocurre

Muchos municipios productores tienen variabilidad fuerte de precipitación y temperatura. Un productor, una UMATA o una secretaría de agricultura puede ver datos históricos, pero no tiene una herramienta simple que diga:

> “Para este municipio y este cultivo, el riesgo de bajo rendimiento está aumentando por déficit de lluvia, exceso de temperatura o acumulación anormal de precipitación”.

### Ejemplos reales de enfoque

- Café en Huila, Tolima, Cauca, Nariño.
- Cacao en Santander, Norte de Santander, Arauca, Meta, Antioquia, Nariño.
- Maíz tradicional o tecnificado en Meta, Córdoba, Tolima, Cesar, Bolívar, Huila.

### Por qué es relevante

- Afecta seguridad alimentaria, ingresos rurales y planeación institucional.
- Es directamente alineado con el objetivo del reto: **predecir rendimientos agrícolas y riesgos climáticos**.
- Permite conectar producción agrícola, clima, uso del suelo y precios.

### Por qué es competitivo

Porque no es solo predicción; puede convertirse en un **semáforo accionable**:

- Riesgo bajo, medio, alto.
- Rendimiento esperado.
- Principales variables que explican el riesgo.
- Recomendación de acción: ajustar fecha de siembra, revisar alternativa de cultivo, priorizar asistencia técnica, activar seguros o apoyos.

---

## Problema 2 — Siembra en zonas no óptimas según aptitud, frontera agrícola y desempeño histórico

### Qué ocurre

En muchos territorios se siembran cultivos por tradición, mercado o presión económica, pero no siempre coinciden con:

- Aptitud agroecológica.
- Frontera agrícola.
- Rendimiento histórico municipal.
- Riesgo climático.
- Acceso a mercados.

### Ejemplo

Un municipio puede tener áreas con **aptitud baja o media para cacao**, pero buen desempeño histórico en otro cultivo. Sin cruzar datos de UPRA, EVA e IDEAM, el productor o planificador no tiene una recomendación objetiva.

### Por qué es relevante

- Reduce pérdidas por mala decisión de cultivo.
- Ayuda a evitar expansión agropecuaria en zonas no aptas o con restricciones.
- Tiene impacto social y ambiental.

### Por qué es competitivo

Una solución que diga “este cultivo tiene menor riesgo y mayor aptitud en tu municipio” es más útil que un dashboard descriptivo. Además, usa muy bien datos estratégicos de UPRA y MinAgricultura.

---

## Problema 3 — Rendimiento esperado no basta: el productor también necesita riesgo económico

### Qué ocurre

Un cultivo puede tener buen rendimiento esperado, pero si suben fertilizantes o cae el precio de mercado, la rentabilidad se reduce.

### Ejemplo

Un productor puede tener buen potencial productivo para maíz, pero si el índice de fertilizantes sube y el precio de venta baja, la recomendación cambia.

### Por qué es relevante

- El ingreso rural depende de rendimiento, precio y costos.
- El alza de agroinsumos afecta especialmente a pequeños productores.
- Permite pasar de “predicción agrícola” a “decisión económica”.

### Por qué es competitivo

Muchos equipos se quedarán en clima + rendimiento. Agregar precios e insumos permite presentar un sistema más integral:

> “No solo predigo cuánto produce; también estimo el riesgo de que no sea rentable”.

---

## Problema 4 — Volatilidad de precios y abastecimiento de productos perecederos

### Qué ocurre

Productos como tomate, papa, plátano, cebolla, mora, yuca o cítricos tienen variaciones fuertes de precio. Los productores no siempre saben si conviene vender, almacenar, mover a otro mercado o coordinar oferta.

### Enfoque viable

Tomar un territorio acotado, por ejemplo:

- Eje Cafetero.
- Tolima.
- Caldas.
- Huila.
- Antioquia.

Y predecir tendencia de precios de productos con datos históricos.

### Por qué es relevante

- Impacta ingresos de productores y precios al consumidor.
- Ayuda a reducir pérdidas y mala planeación de cosecha.
- Puede integrarse con clima y producción.

### Por qué es menos prioritario

La disponibilidad nacional de precios abiertos puede ser más fragmentada que EVA + IDEAM + UPRA. Aun así, es un buen complemento para la propuesta principal.

---

## Problema 5 — Datos climáticos con ruido, huecos o anomalías afectan decisiones agrícolas

### Qué ocurre

Los datos meteorológicos abiertos son enormes y útiles, pero contienen:

- Estaciones con huecos.
- Valores atípicos.
- Diferencias de cobertura territorial.
- Mediciones horarias o cada 10 minutos difíciles de procesar.

### Por qué es relevante

Un mal dato de precipitación puede llevar a una mala alerta agrícola.

### Por qué puede ser competitivo

Un módulo de calidad de datos aumenta el rigor técnico. Pero por sí solo puede ser menos atractivo socialmente que una solución de rendimiento/riesgo.

---

# 2. IDEAS DE PROYECTO — ALTO POTENCIAL PARA GANAR

## Idea 1 — “AgroRiesgo IA”: semáforo municipal de rendimiento y riesgo climático

### Qué hace

Predice para cada combinación `municipio + cultivo + periodo`:

- Rendimiento esperado.
- Probabilidad de caída de rendimiento.
- Riesgo climático por lluvia, temperatura y humedad.
- Variables que explican el riesgo.
- Recomendaciones simples para productores o técnicos.

### Usuarios

- UMATAs.
- Secretarías de agricultura.
- Asociaciones campesinas.
- Extensionistas.
- Cooperativas.
- Productores con apoyo técnico.

### Innovación

No es solo un modelo de regresión. Es un sistema de decisión:

- Modelo predictivo.
- Semáforo de riesgo.
- Explicabilidad.
- Simulación de escenarios climáticos.
- Reportes automáticos.
- Posible asistente conversacional.

### Diferencia frente a soluciones tradicionales

| Tradicional | AgroRiesgo IA |
|---|---|
| Muestra clima histórico | Calcula riesgo productivo |
| Muestra producción pasada | Predice rendimiento esperado |
| Dashboard descriptivo | Recomendación accionable |
| Sin explicación | Explica factores de riesgo |
| Uso aislado de datos | Cruza EVA + IDEAM + UPRA + precios |

---

## Idea 2 — “Siembra Inteligente”: recomendador de cultivo por municipio

### Qué hace

Para un municipio seleccionado, compara cultivos posibles y entrega un ranking:

1. Cultivo más recomendable.
2. Rendimiento esperado.
3. Aptitud territorial.
4. Riesgo climático.
5. Riesgo económico.
6. Restricciones de frontera agrícola.
7. Justificación entendible.

### Usuarios

- Campesinos.
- Extensionistas.
- Alcaldías.
- Gobernaciones.
- Entidades de planeación rural.

### Innovación

Convierte datos técnicos complejos de UPRA, IDEAM y MinAgricultura en una decisión simple:

> “En este municipio, entre café, cacao y maíz, el cultivo con mejor balance entre aptitud, rendimiento esperado y riesgo climático es X”.

### Diferencia frente a soluciones tradicionales

Las herramientas tradicionales suelen mostrar mapas de aptitud, pero no cruzan eso con rendimiento histórico, clima reciente y riesgo económico.

---

## Idea 3 — “Margen Rural IA”: predicción de riesgo económico agrícola

### Qué hace

Estima si un cultivo puede tener presión económica negativa por:

- Rendimiento esperado.
- Precio de mercado.
- Índice de precios de fertilizantes.
- Índice de plaguicidas.
- Variabilidad climática.

### Usuarios

- Productores organizados.
- Cooperativas.
- Bancos agrarios.
- Aseguradoras.
- Secretarías de agricultura.

### Innovación

No predice solo toneladas por hectárea, sino riesgo de rentabilidad.

### Diferencia frente a soluciones tradicionales

Normalmente el productor ve precios e insumos por separado. Aquí se combinan en un indicador de riesgo económico.

---

## Idea 4 — “Alerta Precio-Cosecha”: predicción regional de precios de alimentos perecederos

### Qué hace

Predice tendencia de precio por producto y mercado, por ejemplo:

- Plátano hartón verde.
- Papa criolla.
- Tomate chonto.
- Mora de Castilla.
- Yuca.
- Cebolla.
- Limón Tahití.

### Usuarios

- Comerciantes.
- Productores.
- Centrales de abasto.
- Gobiernos departamentales.
- Asociaciones agrícolas.

### Innovación

Integra precios, producción municipal y clima para anticipar presión de oferta.

### Diferencia frente a soluciones tradicionales

Va más allá de graficar precios históricos; detecta patrones y genera alertas de sobreoferta, escasez o volatilidad.

---

## Idea 5 — “ClimaConfiable Agro”: motor de calidad de datos meteorológicos

### Qué hace

Detecta:

- Estaciones con datos atípicos.
- Huecos de medición.
- Valores imposibles.
- Cambios bruscos no plausibles.
- Municipios con baja cobertura climática.

### Usuarios

- IDEAM.
- Alcaldías.
- Investigadores.
- Equipos que construyan modelos agroclimáticos.

### Innovación

Mejora la confiabilidad del insumo base de cualquier modelo climático.

### Diferencia frente a soluciones tradicionales

No solo consume datos climáticos; evalúa su calidad y confiabilidad antes de usarlos.

---

# 3. DATOS ABIERTOS RELEVANTES

## Datasets principales de datos.gov.co

| Dataset | ID / fuente | Variables clave | Uso en el modelo |
|---|---|---|---|
| Evaluaciones Agropecuarias Municipales EVA | `2pnw-mmge` | Departamento, municipio, cultivo, año, periodo, área sembrada, área cosechada, producción, rendimiento, ciclo de cultivo | Variable objetivo: `rendimiento_t_ha`. Base histórica de producción y productividad |
| Evaluaciones Agropecuarias Municipales EVA 2019-2024 Base Agrícola | `uejq-wxrr` | Código DANE, municipio, cultivo, área sembrada, área cosechada, producción, rendimiento, año, periodo | Actualización reciente para entrenar y validar modelos |
| Precipitación IDEAM | `s54a-sgyg` | Código estación, fecha observación, valor observado, municipio, departamento, latitud, longitud, unidad mm | Calcular lluvia acumulada, déficit, exceso, días secos, eventos extremos |
| Temperatura Ambiente del Aire IDEAM | `sbwg-7ju4` | Código estación, fecha, temperatura, municipio, latitud, longitud, unidad °C | Calcular temperatura media, anomalías, días calurosos, estrés térmico |
| Humedad del Aire IDEAM | `uext-mhny` | Código estación, fecha, humedad relativa, municipio, latitud, longitud | Riesgo de enfermedades, exceso de humedad, estrés agroclimático |
| Datos de Estaciones de IDEAM y de Terceros | `57sv-p2fu` | Código estación, sensor, fecha, valor, descripción sensor, municipio, latitud, longitud | Monitoreo reciente, alertas casi en tiempo real |
| Catálogo Nacional de Estaciones IDEAM | `hp9r-jxuu` | Código, nombre, categoría, tecnología, estado, municipio, ubicación, altitud | Selección de estaciones cercanas, calidad de datos, distancia municipio-estación |
| Censo Nacional Agropecuario - Uso de la tierra | `f9jj-yx8h` | Hectáreas por uso, tenencia, UPA, UPNA, uso agropecuario, bosque natural | Variables estructurales del municipio y uso del suelo |
| Identificación de frontera agrícola y frontera agrícola condicionada | `fyc7-sbtz` | Municipio, departamento, código DANE, tipo frontera, área en hectáreas | Evitar recomendaciones fuera de frontera agrícola o en zonas condicionadas |
| Zonificación de aptitud para café | `kwvf-nwea` | Municipio, departamento, código DANE, aptitud, área ha, gridcode | Variable de aptitud para café y recomendación de cultivo |
| Zonificación de aptitud para cacao | `jdjx-qer4` | Municipio, departamento, código DANE, aptitud, área ha, gridcode | Variable de aptitud para cacao |
| Zonificación de aptitud para maíz tradicional | `frjn-92um` | Municipio, departamento, código DANE, aptitud, área ha | Variable de aptitud para maíz tradicional |
| Zonificación de aptitud para maíz tecnificado primer semestre | `a5yc-uszt` | Municipio, departamento, aptitud, área ha | Comparación por semestre agrícola |
| Zonificación de aptitud para maíz tecnificado segundo semestre | `tzga-4zse` | Municipio, departamento, aptitud, área ha | Comparación por semestre agrícola |
| Índice de precios de insumos agrícolas | `gwbi-fnzs` | Fecha, índice total, fertilizantes, plaguicidas, herbicidas, fungicidas, insecticidas, urea, DAP, KCL | Riesgo económico por costos de producción |
| Histórico de Precios Productos de la Canasta Familiar RAP Eje Cafetero | `gdqq-rry2` | Producto, mercado, precio mínimo, máximo, medio, fecha inicial/final, categoría, ciudad | Tendencia de precios regionales, complemento económico |
| Precios comercialización agrícola | `hadm-n448` | Semana, producto, presentación, precios diarios | Fuente local complementaria, útil para demo regional pero limitada |

---

## Fuentes adicionales recomendadas

Estas no reemplazan datos.gov.co; se usan para enriquecer la solución si el concurso lo permite.

| Fuente | Uso recomendado |
|---|---|
| IDEAM pronósticos y boletines agroclimáticos | Escenarios de riesgo climático próximo |
| DANE SIPSA | Precios mayoristas y abastecimiento nacional de alimentos |
| NASA POWER | Clima histórico por coordenadas cuando no haya estación cercana |
| CHIRPS | Precipitación satelital histórica, útil en municipios con poca cobertura IDEAM |
| ERA5 / Copernicus | Temperatura, humedad y variables climáticas reanalizadas |
| TerriData / DNP | Variables socioeconómicas, ruralidad, pobreza, capacidades municipales |
| Datos PDET / ZOMAC / Reforma Rural | Priorización de impacto social en zonas vulnerables |

---

# 4. ENFOQUES DE INTELIGENCIA ARTIFICIAL

## 4.1 Predicción de rendimiento agrícola

### Objetivo

Predecir `rendimiento_t_ha` por `municipio + cultivo + año/periodo`.

### Modelo recomendado

**XGBoost Regressor** — es el modelo principal para este proyecto.

- Funciona muy bien con datos en tabla (filas y columnas), que es exactamente el formato de EVA + IDEAM + UPRA.
- Maneja sin problema variables categóricas como municipio y cultivo.
- Es rápido de entrenar, no requiere GPU.
- Compatible con SHAP para explicar cada predicción.
- Ampliamente documentado y con mucho soporte de la comunidad.
- La IA puede generar el código completo sin problemas.

### Variables de entrada

- Rendimiento histórico rezagado: año anterior, promedio 3 años, tendencia.
- Área sembrada histórica.
- Área cosechada histórica.
- Cambio de área sembrada.
- Precipitación acumulada.
- Anomalía de precipitación.
- Días secos consecutivos.
- Temperatura media.
- Días de calor extremo.
- Humedad promedio.
- Aptitud UPRA: porcentaje de área en aptitud alta/media/baja.
- Frontera agrícola: área condicionada/no condicionada.
- Índice de agroinsumos.
- Precio medio regional si aplica.

### Importante

No se debe usar `producción_t` ni `área_cosechada` del mismo periodo como variables predictoras si se busca predecir rendimiento futuro, porque el rendimiento se calcula a partir de producción y área. Eso sería fuga de información.

---

## 4.2 Clasificación de riesgo climático-productivo

### Objetivo

Clasificar el riesgo de bajo rendimiento:

- Bajo.
- Medio.
- Alto.

> Riesgo alto = rendimiento esperado cae más de 15 % o 20 % frente al promedio histórico municipal del cultivo.

### Modelo recomendado

**XGBoost Classifier** — el mismo algoritmo de XGBoost pero configurado para clasificar en lugar de predecir un número.

Ventaja: se entrena sobre las predicciones del modelo de rendimiento, por lo que reutiliza todo el trabajo ya hecho.

### Qué entrega

- Probabilidad de riesgo (ej. 78% de probabilidad de riesgo alto).
- Etiqueta final: Bajo / Medio / Alto.
- Variables que explican la clasificación vía SHAP.

---

## 4.3 Riesgo económico por precios e insumos

### Objetivo

Estimar si un cultivo puede tener presión económica negativa combinando rendimiento esperado + índice de agroinsumos + precio regional.

### Enfoque recomendado

No requiere un modelo separado. Se calcula como un **índice de scoring** simple sobre los resultados del XGBoost:

- Si el rendimiento esperado es bajo Y el índice de fertilizantes está alto → riesgo económico alto.
- Se expresa como un semáforo adicional en la ficha municipal.

---

## 4.4 Recomendador de cultivo

### Objetivo

Ranking de cultivos por municipio: dado un municipio, comparar café vs cacao vs maíz y recomendar el más adecuado.

### Enfoque recomendado

No es un modelo nuevo — es un **motor de scoring** que combina los resultados ya calculados:

| Factor | Peso sugerido |
|---|---|
| Rendimiento esperado (XGBoost) | Alto |
| Riesgo climático (XGBoost Classifier) | Alto |
| Aptitud UPRA | Medio |
| Frontera agrícola | Medio |
| Riesgo económico (índice insumos + precio) | Medio |
| Estabilidad histórica de rendimiento | Bajo |

Resultado: un ranking de 1 a 3 cultivos con justificación en lenguaje claro generada por el LLM.

---

# 5. ARQUITECTURA DEL SISTEMA

## Arquitectura recomendada para MVP

### 1. Ingesta de datos

Fuentes:

- API Socrata de datos.gov.co.
- Descarga parcial por filtros.
- Archivos geoespaciales de UPRA/CNA si se requiere.
- Fuentes adicionales opcionales como IDEAM, CHIRPS o NASA POWER.

Recomendación práctica:

- No descargar todos los 165 millones de registros de precipitación.
- Usar consultas agregadas por municipio, estación, mes o año.
- Guardar resultados ya procesados en Parquet o DuckDB.

---

### 2. Procesamiento

Crear una tabla maestra con esta granularidad:

`municipio + código DANE + cultivo + año + periodo`

Variables derivadas:

- Rendimiento histórico.
- Área sembrada rezagada.
- Cambio de área sembrada.
- Lluvia acumulada.
- Anomalía de lluvia.
- Días secos.
- Temperatura promedio.
- Temperatura extrema.
- Humedad promedio.
- Aptitud alta/media/baja en hectáreas.
- Porcentaje de frontera agrícola condicionada.
- Índice de agroinsumos.
- Precio regional si aplica.
- Calidad/cobertura climática.

---

### 3. Modelo

Pipeline:

1. Entrenamiento con datos históricos.
2. Validación temporal.
3. Predicción de rendimiento.
4. Clasificación de riesgo.
5. Explicabilidad con SHAP.
6. Generación de recomendaciones.

Métricas:

- MAE.
- RMSE.
- R².
- F1-score para riesgo.
- AUC si hay clasificación binaria.
- Error por cultivo.
- Error por departamento.
- Calibración de probabilidades.

---

### 4. Backend

| Componente | Tecnología | Por qué |
|---|---|---|
| API del modelo | FastAPI (Python) | Expone las predicciones del XGBoost como endpoints REST. Sintaxis idéntica a Express. La IA lo genera sin problema |
| Procesamiento de datos | Python + Pandas | Limpieza, agregación de datos climáticos y construcción de la tabla maestra |
| Análisis de datos históricos | DuckDB | Corre dentro del mismo proceso Python sin servidor. Permite hacer queries SQL sobre archivos Parquet directamente, ideal para explorar y agregar los millones de registros de IDEAM sin cargarlos todos en memoria |
| Almacenamiento de datos | Parquet | Formato eficiente para guardar la tabla maestra. DuckDB lo lee directamente |
| Base de datos de la app | PostgreSQL | Guarda predicciones ya calculadas, municipios, resultados listos para consultar desde Next.js |
| Modelo | XGBoost + scikit-learn | XGBoost para predicción y clasificación, scikit-learn para utilidades y métricas |
| Explicabilidad | SHAP | Genera los valores que explican cada predicción — se devuelven como JSON al frontend |
| Consumo de datos abiertos | API Socrata (datos.gov.co) | API REST normal, devuelve JSON, se consume igual que cualquier otra API |
| Empaquetado | Docker + Docker Compose | Permite que los 4 integrantes del equipo trabajen con el mismo entorno sin conflictos de versiones. Un solo `docker compose up` levanta FastAPI + PostgreSQL juntos |

---

### 5. Frontend

| Componente | Tecnología | Por qué |
|---|---|---|
| Framework | Next.js | SSR, rutas API integradas, fácil despliegue. Mejor opción para el equipo que ya sabe React |
| Mapas | react-leaflet | Versión oficial de Leaflet para React. Componentes como `<MapContainer>`, `<Marker>`, `<Polygon>` directamente en JSX |
| Gráficas | react-plotly.js | Gráficas interactivas de tendencia, barras de SHAP, comparadores de cultivos |
| UI / Selectores | shadcn/ui | Librería de componentes moderna para Next.js. Selectores de departamento, municipio y cultivo |
| Comunicación con backend | fetch / axios | Consume los endpoints de FastAPI igual que cualquier otra API REST |

Pantallas mínimas:

1. **Mapa nacional de riesgo**
   - Color por municipio.
   - Filtro por cultivo.

2. **Ficha municipal**
   - Rendimiento histórico.
   - Rendimiento esperado.
   - Riesgo climático.
   - Variables explicativas.
   - Calidad del dato.

3. **Comparador de cultivos**
   - Café vs cacao vs maíz.
   - Ranking recomendado.

4. **Reporte automático**
   - PDF o texto generado para UMATA/productor.

5. **Asistente IA**
   - Preguntas en lenguaje natural sobre resultados del modelo.

---

# 6. DIFERENCIADORES PARA GANAR

## Innovación

Para maximizar innovación, la solución debe ser más que un dashboard.

Diferenciadores fuertes:

- Predicción de rendimiento.
- Clasificación de riesgo climático.
- Recomendación de cultivo.
- Simulación de escenarios:
  - Año seco.
  - Año lluvioso.
  - Aumento de temperatura.
  - Subida de fertilizantes.
- Explicabilidad del modelo.
- Asistente generativo que traduzca resultados técnicos a lenguaje campesino/institucional.

---

## Uso de datos abiertos

Para puntuar alto:

- Usar varios datasets reales de datos.gov.co.
- Mostrar trazabilidad: “esta predicción usa EVA + IDEAM + UPRA + precios”.
- Incluir IDs de datasets en la presentación.
- Mostrar actualización mediante API.
- No usar solo un CSV descargado manualmente.

Datasets mínimos recomendados para la demo:

1. EVA `2pnw-mmge` / `uejq-wxrr`.
2. Precipitación IDEAM `s54a-sgyg`.
3. Temperatura IDEAM `sbwg-7ju4`.
4. Catálogo estaciones IDEAM `hp9r-jxuu`.
5. Frontera agrícola UPRA `fyc7-sbtz`.
6. Aptitud por cultivo UPRA, por ejemplo `kwvf-nwea`, `jdjx-qer4`, `frjn-92um`.
7. Índice de agroinsumos `gwbi-fnzs`.

---

## Impacto social

Para que el jurado vea impacto real:

- Enfocar en pequeños productores y municipios rurales vulnerables.
- Priorizar zonas PDET, alta ruralidad o baja capacidad institucional.
- Diseñar para UMATAs y extensionistas, no solo para científicos de datos.
- Entregar recomendaciones en lenguaje simple.
- Generar reportes listos para compartir por WhatsApp o PDF.

---

## Escalabilidad

El sistema debe diseñarse como motor reutilizable:

- Agregar nuevos cultivos cambiando configuración.
- Agregar nuevos municipios automáticamente.
- Actualizar datos vía API.
- Separar modelo, datos y visualización.
- Permitir despliegue en nube.

---

## Extras potentes

### 1. IA generativa

Usarla como interfaz, no como modelo predictivo principal.

Ejemplo de pregunta:

> “¿Qué municipios de Cauca tienen mayor riesgo de caída de rendimiento en cacao y por qué?”

El asistente debe responder usando resultados del modelo, no inventando.

---

### 2. Reportes automáticos

Generar un reporte por municipio:

- Riesgo actual.
- Cultivos más vulnerables.
- Factores principales.
- Recomendaciones.
- Datos usados.
- Nivel de confianza.

---

### 3. Explicabilidad

Mostrar:

- “El riesgo subió principalmente por déficit de lluvia acumulada”.
- “La aptitud media/baja reduce la expectativa de rendimiento”.
- “El precio de fertilizantes aumenta el riesgo económico”.

Esto da mucho rigor técnico ante jurados.

---

# 7. PROPUESTA FINAL RECOMENDADA

## Idea ganadora recomendada

# **SiembraSegura IA: semáforo de rendimiento, riesgo climático y recomendación de cultivo para municipios rurales de Colombia**

---

## Qué es

Una plataforma web que permite seleccionar:

- Departamento.
- Municipio.
- Cultivo.
- Periodo agrícola.

Y entrega:

1. Rendimiento esperado.
2. Riesgo de caída de rendimiento.
3. Riesgo climático.
4. Aptitud territorial.
5. Riesgo económico básico.
6. Recomendación accionable.
7. Explicación en lenguaje claro.
8. Reporte automático.

---

## Por qué es la mejor opción para ganar

### 1. Está perfectamente alineada con el reto

El reto pide:

- Producción agrícola.
- Uso del suelo.
- Meteorología.
- Precios de mercado.
- IA para predecir rendimiento y riesgo climático.

Esta idea usa todo eso.

---

### 2. Tiene impacto social claro

Sirve para:

- Campesinos.
- Extensionistas.
- Alcaldías.
- Secretarías de agricultura.
- Asociaciones productivas.

No es una solución abstracta.

---

### 3. Es viable en 1 mes

No requiere entrenar modelos satelitales complejos ni deep learning pesado. Puede hacerse con:

- Datos tabulares.
- Agregaciones climáticas.
- XGBoost (predicción y clasificación de riesgo).
- Dashboard en Next.js con react-leaflet y react-plotly.js.
- Asistente generativo con RAG sobre los resultados del modelo.

---

### 4. Es demostrable

En la demo se puede mostrar:

- Mapa de riesgo.
- Predicción por municipio.
- Comparación de cultivos.
- Explicación del modelo.
- Reporte automático.
- Chatbot consultando resultados.

Eso es mucho más convincente que mostrar solo una métrica de modelo.

---

## Alcance realista en 1 mes

### Cultivos recomendados para MVP

Escoger 3:

1. **Café**
   - Alto impacto social.
   - Mucha presencia de pequeños productores.
   - Dataset de aptitud UPRA disponible.
   - Sensible a clima.

2. **Cacao**
   - Relevante en zonas rurales vulnerables.
   - Relación con sustitución, desarrollo rural y economías campesinas.
   - Dataset de aptitud UPRA disponible.

3. **Maíz**
   - Seguridad alimentaria.
   - Cultivo transitorio.
   - Datos de aptitud por semestre.
   - Buena conexión con riesgo climático.

---

## Cobertura geográfica recomendada

Para MVP no intentaría resolver todo Colombia desde el primer día. Recomiendo:

### Opción A — Más estratégica

Foco inicial en 8 departamentos:

- Huila.
- Tolima.
- Cauca.
- Nariño.
- Santander.
- Norte de Santander.
- Meta.
- Antioquia.

### Opción B — Más ambiciosa

Modelo nacional, pero demo profunda en 10 a 20 municipios priorizados.

Mi recomendación: **modelo nacional para 3 cultivos, demo profunda en municipios seleccionados**.

---

## MVP mínimo viable

Debe incluir:

### 1. Pipeline de datos

- EVA histórica.
- IDEAM precipitación.
- IDEAM temperatura.
- UPRA aptitud.
- UPRA frontera agrícola.
- Índice de agroinsumos.
- Precios regionales si aplican.

---

### 2. Modelo predictivo

- Predicción de rendimiento.
- Clasificación de riesgo.
- Validación temporal.
- Explicabilidad con SHAP.

---

### 3. Dashboard

Pantallas mínimas:

- Mapa de riesgo.
- Detalle por municipio/cultivo.
- Comparador de cultivos.
- Factores que explican riesgo.
- Recomendación final.

---

### 4. Asistente IA

Preguntas posibles:

- “¿Cuál es el cultivo con menor riesgo en este municipio?”
- “¿Por qué el modelo marca alto riesgo para cacao?”
- “¿Qué municipios de Huila tienen mayor riesgo para café?”
- “Genera un reporte para la UMATA de este municipio”.

---

## Qué mostrar en la demo final

### Demo sugerida

1. Abrir el mapa nacional.
2. Filtrar por cultivo: cacao, café o maíz.
3. Seleccionar un municipio rural.
4. Mostrar:
   - Rendimiento histórico.
   - Rendimiento esperado.
   - Semáforo de riesgo.
   - Variables que explican el resultado.
5. Comparar con otro cultivo.
6. Generar reporte automático.
7. Preguntar al asistente IA:
   - “Explícame este riesgo en lenguaje sencillo para un productor”.
8. Mostrar trazabilidad de datos:
   - EVA.
   - IDEAM.
   - UPRA.
   - Agroinsumos.
   - Precios.

---

## Plan de trabajo de 4 semanas

### Semana 1 — Datos y alcance

- Definir cultivos.
- Descargar/consultar datasets.
- Normalizar códigos DANE.
- Crear tabla base municipal.
- Agregar clima por municipio/año.

### Semana 2 — Features y modelo

- Crear variables climáticas.
- Crear variables de aptitud.
- Entrenar baseline.
- Validar temporalmente.
- Medir errores.

### Semana 3 — Producto

- Construir dashboard.
- Integrar mapas.
- Añadir explicabilidad.
- Crear semáforo y recomendaciones.

### Semana 4 — Demo y narrativa

- Agregar asistente IA.
- Generar reportes.
- Preparar pitch.
- Documentar datasets.
- Ensayar demo con casos reales.

---

# 8. ERRORES COMUNES A EVITAR

## Errores técnicos

1. **Intentar predecir a nivel finca con datos municipales**
   - Los datos EVA son municipales. No prometan precisión de parcela.

2. **Usar producción y área cosechada del mismo año como variables**
   - Eso causa fuga de información porque el rendimiento se deriva de producción/área.

3. **Hacer split aleatorio**
   - En series temporales agrícolas se debe validar por años futuros, no mezclar pasado y futuro.

4. **Descargar todos los datos crudos de IDEAM sin agregación**
   - Son millones de registros. Mejor usar agregaciones por fecha, estación y municipio.

5. **No controlar calidad climática**
   - Hay estaciones con huecos o valores raros. Incluyan filtros básicos.

6. **No unificar códigos DANE**
   - Usar nombres de municipios puede fallar por tildes, cambios o variaciones.

7. **Usar demasiados cultivos**
   - Mejor 3 cultivos bien resueltos que 30 superficialmente.

8. **No explicar el modelo**
   - El jurado necesita entender por qué el sistema recomienda algo.

9. **Confundir precio de mercado con precio pagado al productor**
   - Si usan precios mayoristas o de canasta, aclaren la limitación.

10. **Prometer predicción climática sin fuente de pronóstico**
   - Si no tienen pronóstico real, presenten escenarios: seco, normal, lluvioso.

---

## Errores estratégicos

1. **Hacer solo un dashboard descriptivo**
   - Eso no se siente como IA aplicada.

2. **No conectar la solución con decisiones reales**
   - El usuario debe saber qué hacer con el resultado.

3. **No definir usuario**
   - “Para todos” suele ser “para nadie”. Enfoquen UMATAs, extensionistas y asociaciones.

4. **No contar historia social**
   - El jurado debe ver impacto en productores vulnerables.

5. **No mostrar datos abiertos en la demo**
   - Hay que evidenciar el uso de datos.gov.co.

6. **Sobrecomplicar con deep learning**
   - Para 1 mes, un buen XGBoost explicable puede ganar más que una red neuronal mal validada.

7. **No tener MVP funcional**
   - Mejor una app simple funcionando que una arquitectura ambiciosa incompleta.

---

# Recomendación ejecutiva final

Si yo estuviera en tu equipo, elegiría:

## **SiembraSegura IA / AgroRiesgo360**

Una plataforma que predice rendimiento y riesgo climático por municipio y cultivo, integrando:

- EVA para producción agrícola.
- IDEAM para precipitación, temperatura y humedad.
- UPRA para aptitud y frontera agrícola.
- CNA para uso del suelo.
- Agroinsumos y precios para riesgo económico.

El MVP debe enfocarse en **café, cacao y maíz**, con demo profunda en municipios rurales vulnerables.

Esta idea tiene el mejor balance entre:

- Impacto social.
- Uso fuerte de datos abiertos.
- Viabilidad en 1 mes.
- Rigor técnico.
- Innovación visible.
- Demo convincente para jurados.

---

# STACK TECNOLÓGICO DEFINITIVO DEL EQUIPO

## Lado datos y modelo

| Herramienta | Uso |
|---|---|
| Python + Pandas | Limpieza y construcción de la tabla maestra |
| DuckDB | Queries SQL sobre archivos Parquet sin servidor, para explorar y agregar millones de registros de IDEAM |
| Parquet | Almacenamiento eficiente de datos históricos |
| XGBoost | Modelo de predicción de rendimiento y clasificación de riesgo |
| scikit-learn | Utilidades, métricas y validación temporal |
| SHAP | Explicabilidad de cada predicción |
| FastAPI | API REST que expone las predicciones al frontend |
| PostgreSQL | Base de datos de la app con predicciones ya calculadas |
| Docker + Docker Compose | Entorno unificado para todo el equipo. Evita el clásico “en mi máquina sí funciona” |

## Lado frontend y asistente IA

| Herramienta | Uso |
|---|---|
| Next.js | Framework principal del frontend |
| react-leaflet | Mapa de Colombia coloreado por nivel de riesgo |
| react-plotly.js | Gráficas de rendimiento, tendencia y SHAP |
| shadcn/ui | Componentes UI: selectores, tarjetas, semáforo |
| fetch / axios | Comunicación con FastAPI |
| LLM + RAG | Asistente que responde preguntas usando los resultados del modelo como contexto |

---

# 9. METODOLOGÍA DE DESARROLLO — SPEC-DRIVEN + TASK DECOMPOSITION

## Aclaración sobre el enfoque

Lo que se aplica aquí **no es DDD (Domain-Driven Design) como patrón de arquitectura de software**, sino una combinación de dos metodologías de desarrollo asistido por IA:

- **Spec-Driven Development (SDD):** cada módulo del sistema se define primero como una especificación estructurada (spec) con requisitos, inputs, outputs esperados y criterios de aceptación. El agente de IA lee esa spec antes de escribir código, lo que elimina ambigüedad y reduce iteraciones.

- **Task Decomposition por dominio funcional:** el trabajo total se descompone en tareas atómicas agrupadas por capa (datos, modelo, API, frontend). Cada tarea es lo suficientemente pequeña para que un agente especializado la ejecute de forma autónoma sin necesitar contexto de otras capas.

La combinación permite:
- Que cada agente de IA tenga una responsabilidad única y contexto acotado.
- Que el equipo humano valide specs antes de que la IA ejecute, evitando retrabajos.
- Que las tareas se puedan paralelizar entre miembros del equipo.
- Que se puedan agregar nuevos cultivos o municipios simplemente actualizando la spec correspondiente.

---

## Capas funcionales del sistema

El trabajo se organiza en 5 capas. Cada capa tiene sus propias specs y sus propias tareas atómicas. Un agente de IA especializado trabaja dentro de una capa sin necesitar contexto de las otras.

| Capa | Responsabilidad | Agente de IA asignado |
|------|----------------|----------------------|
| **Capa de Datos** | Ingesta, limpieza y construcción de Parquets | Agente de datos (Python/Pandas) |
| **Capa de Modelo** | Features, entrenamiento XGBoost, validación, SHAP | Agente de ML (Python/scikit-learn) |
| **Capa de API** | Endpoints FastAPI, orquestación, lógica de negocio | Agente de backend (Python/FastAPI) |
| **Capa de Frontend** | Dashboard Next.js, mapas, gráficas, semáforo | Agente de frontend (TypeScript/React) |
| **Capa Conversacional** | Asistente LLM + RAG, reportes automáticos | Agente conversacional (LLM + RAG) |

---

## Arquitectura de agentes especializados

Cada capa del sistema se implementa como un módulo autónomo con una interfaz clara. Un **orquestador central** (FastAPI) coordina el flujo entre módulos según el tipo de solicitud.

```
┌─────────────────────────────────────────────────────────────┐
│                    ORQUESTADOR CENTRAL                       │
│              (FastAPI — capa de coordinación)                │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐
  │ Módulo  │ │Módulo  │ │Módulo  │ │Módulo  │ │  Módulo    │
  │Climático│ │Agrícola│ │Territ. │ │Económ. │ │Predictivo  │
  └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └─────┬──────┘
       │          │          │          │             │
       └──────────┴──────────┴──────────┴─────────────┘
                             │
                    ┌────────▼────────┐
                    │ Módulo          │
                    │ Explicabilidad  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Módulo          │
                    │ Conversacional  │
                    └─────────────────┘
```

---

## Descripción de cada módulo

### Módulo Climático
**Responsabilidad:** Proveer variables climáticas agregadas por municipio y año.

- Consume: `hp9r-jxuu` (catálogo), `s54a-sgyg` (precipitación), `sbwg-7ju4` (temperatura), `uext-mhny` (humedad), `57sv-p2fu` (recientes)
- Produce: `SerieClimática(municipio, año, prec_acum, temp_media, hum_media, dias_secos, anomalia_prec, anomalia_temp)`
- Interfaz: `GET /clima/{municipio}/{año}` → JSON con variables agregadas
- Lógica interna: detección de huecos, imputación básica, cálculo de anomalías respecto a media histórica

### Módulo Agrícola
**Responsabilidad:** Proveer rendimiento histórico y área sembrada por municipio y cultivo.

- Consume: `2pnw-mmge` (EVA 2007-2018), `uejq-wxrr` (EVA 2019-2024)
- Produce: `RendimientoHistórico(municipio, cultivo, año, rendimiento, area_sembrada, tendencia_3a)`
- Interfaz: `GET /eva/{municipio}/{cultivo}` → serie temporal de rendimiento
- Lógica interna: normalización de nombres, unificación de columnas entre datasets, cálculo de rezagos

### Módulo Territorial
**Responsabilidad:** Proveer aptitud agroecológica y restricciones de frontera agrícola.

- Consume: `kwvf-nwea` (café), `jdjx-qer4` (cacao), `frjn-92um` + `a5yc-uszt` + `tzga-4zse` (maíz), `fyc7-sbtz` (frontera)
- Produce: `ZonaAptitud(municipio, cultivo, pct_alta, pct_media, pct_baja, pct_condicionada)`
- Interfaz: `GET /aptitud/{municipio}/{cultivo}` → porcentajes de aptitud
- Lógica interna: GROUP BY en SoQL para evitar geometrías, unión de datasets de maíz

### Módulo Económico
**Responsabilidad:** Proveer índice de agroinsumos y señal de riesgo económico.

- Consume: `gwbi-fnzs` (agroinsumos), `gdqq-rry2` (precios RAP Eje Cafetero)
- Produce: `RiesgoEconómico(fecha, indice_fertilizantes, indice_plaguicidas, precio_referencia, señal_riesgo)`
- Interfaz: `GET /economia/{cultivo}/{año}` → índices y señal de riesgo
- Lógica interna: cálculo de percentil del índice respecto a histórico, cruce con precio si disponible

### Módulo Predictivo
**Responsabilidad:** Entrenar y ejecutar los modelos XGBoost de rendimiento y riesgo.

- Consume: salidas de los 4 módulos anteriores (tabla maestra)
- Produce: `Predicción(municipio, cultivo, año, rendimiento_esperado, prob_riesgo_alto, etiqueta_riesgo)`
- Interfaz: `POST /predecir` con payload `{municipio, cultivo, año, escenario}` → predicción + probabilidades
- Lógica interna: validación temporal (train hasta año N-1, test año N), pipeline scikit-learn + XGBoost

### Módulo Explicabilidad
**Responsabilidad:** Calcular valores SHAP y construir narrativa de factores de riesgo.

- Consume: salida del Módulo Predictivo + modelo entrenado
- Produce: `ExplicaciónSHAP(prediccion_id, factores_ordenados, narrativa_texto)`
- Interfaz: `GET /explicar/{prediccion_id}` → factores SHAP + texto explicativo
- Lógica interna: SHAP TreeExplainer sobre XGBoost, plantilla de narrativa por nivel de riesgo

### Módulo Conversacional
**Responsabilidad:** Responder preguntas en lenguaje natural usando resultados del modelo como contexto (RAG).

- Consume: salidas del Módulo Predictivo + Módulo Explicabilidad (como contexto)
- Produce: `RespuestaGenerada(pregunta, contexto_usado, respuesta, reporte_pdf)`
- Interfaz: `POST /chat` con `{pregunta, municipio, cultivo}` → respuesta en lenguaje natural
- Lógica interna: recuperación de contexto relevante (predicciones + SHAP del municipio), prompt al LLM con contexto estructurado, generación de reporte si se solicita

---

## Flujo de orquestación — ejemplo: "¿Cuál es el riesgo para café en Chaparral en 2025?"

```
1. Frontend → POST /predecir {municipio: "Chaparral", cultivo: "Café", año: 2025}

2. Orquestador llama en paralelo:
   ├── Módulo Climático   → SerieClimática(Chaparral, 2024)
   ├── Módulo Agrícola    → RendimientoHistórico(Chaparral, Café, 2007-2024)
   ├── Módulo Territorial → ZonaAptitud(Chaparral, Café)
   └── Módulo Económico   → RiesgoEconómico(Café, 2024)

3. Orquestador ensambla tabla maestra → Módulo Predictivo
   → Predicción: rendimiento 0.82 t/ha, riesgo ALTO (prob 71%)

4. Módulo Explicabilidad
   → "El riesgo alto se explica principalmente por déficit de lluvia
      acumulada (-23% vs media histórica) y aumento del índice de
      fertilizantes (+18% vs año anterior)"

5. Módulo Conversacional (si hay pregunta en chat)
   → Respuesta en lenguaje campesino/institucional + reporte PDF

6. Orquestador → Frontend: JSON con predicción + SHAP + narrativa
```

---

## Estructura de carpetas del proyecto

```
siembrasegura/
├── modules/                         # Módulos funcionales por capa
│   ├── climate/
│   │   ├── ingestion.py             # Descarga y limpieza IDEAM
│   │   ├── aggregation.py           # Agregación por municipio/año
│   │   ├── anomalies.py             # Cálculo de anomalías climáticas
│   │   └── api.py                   # Endpoints FastAPI del módulo
│   │
│   ├── agricultural/
│   │   ├── ingestion.py             # Descarga EVA histórica + reciente
│   │   ├── normalization.py         # Unificación columnas, códigos DANE
│   │   ├── features.py              # Rezagos, tendencias, cambio área
│   │   └── api.py
│   │
│   ├── territorial/
│   │   ├── ingestion.py             # Descarga UPRA (GROUP BY SoQL)
│   │   ├── aptitude.py              # Cálculo porcentajes aptitud
│   │   ├── frontier.py              # Frontera agrícola condicionada
│   │   └── api.py
│   │
│   ├── economic/
│   │   ├── ingestion.py             # Descarga agroinsumos + precios
│   │   ├── risk_score.py            # Percentil histórico, señal riesgo
│   │   └── api.py
│   │
│   ├── predictive/
│   │   ├── feature_builder.py       # Construcción tabla maestra
│   │   ├── train.py                 # Entrenamiento XGBoost + validación temporal
│   │   ├── predict.py               # Inferencia + clasificación riesgo
│   │   ├── scenarios.py             # Simulación escenarios climáticos
│   │   └── api.py
│   │
│   ├── explainability/
│   │   ├── shap_engine.py           # SHAP TreeExplainer
│   │   ├── narratives.py            # Plantillas de narrativa por riesgo
│   │   └── api.py
│   │
│   └── conversational/
│       ├── rag.py                   # Recuperación de contexto
│       ├── prompts.py               # Plantillas de prompt por caso de uso
│       ├── reports.py               # Generación PDF/texto
│       └── api.py
│
├── orchestrator/                    # Orquestador central
│   ├── router.py                    # Enrutamiento de solicitudes
│   ├── pipeline.py                  # Flujo de llamadas entre módulos
│   └── main.py                      # FastAPI app principal
│
├── shared/                          # Código compartido
│   ├── dane_codes.py                # Mapa municipio → código DANE
│   ├── normalization.py             # Normalización de nombres
│   ├── socrata_client.py            # Cliente API Socrata reutilizable
│   └── config.py                    # Variables de entorno, URLs APIs
│
├── data/                            # Datos procesados (Parquet)
│   ├── eva_historica.parquet
│   ├── eva_reciente.parquet
│   ├── clima_agregado.parquet
│   ├── aptitud_cafe.parquet
│   ├── aptitud_cacao.parquet
│   ├── aptitud_maiz.parquet
│   └── agroinsumos.parquet
│
├── models/                          # Modelos entrenados
│   ├── xgb_rendimiento_cafe.pkl
│   ├── xgb_rendimiento_cacao.pkl
│   ├── xgb_rendimiento_maiz.pkl
│   └── xgb_riesgo_*.pkl
│
├── specs/                           # Specs de desarrollo (Spec-Driven)
│   ├── spec_datos.md                # Spec capa de datos
│   ├── spec_modelo.md               # Spec capa de modelo
│   ├── spec_api.md                  # Spec capa de API
│   ├── spec_frontend.md             # Spec capa de frontend
│   └── spec_conversacional.md       # Spec módulo conversacional
│
├── frontend/                        # Next.js
│   └── ...
│
├── docker-compose.yml
└── README.md
```

---

## Specs de desarrollo — estructura de cada spec

Cada spec vive en `specs/` y tiene este formato. El agente de IA la lee antes de escribir cualquier código del módulo correspondiente.

```markdown
# Spec: [Nombre del módulo]

## Objetivo
Qué debe hacer este módulo en una oración.

## Inputs
- Fuente 1: descripción, formato, columnas relevantes
- Fuente 2: ...

## Outputs
- Archivo/endpoint producido: formato, columnas, ejemplo de fila

## Criterios de aceptación
- [ ] El output tiene las columnas X, Y, Z
- [ ] No hay valores nulos en la columna rendimiento
- [ ] El tiempo de ejecución es menor a N segundos
- [ ] Los 15 municipios del MVP están presentes

## Restricciones técnicas
- Usar DuckDB para queries sobre Parquet
- No descargar más de N registros por llamada a la API
- Normalizar nombres de municipios con dane_codes.py

## Dependencias
- Requiere: shared/socrata_client.py, shared/dane_codes.py
- Produce para: módulo predictivo (feature_builder.py)
```

---

## Descomposición de tareas por capa (Task Decomposition)

### Capa de Datos — Semana 1

| ID | Tarea | Subtareas | Agente IA | Entregable |
|----|-------|-----------|-----------|-----------|
| D1 | Pipeline EVA | D1.1 Descargar EVA histórica 2007-2018 para 15 municipios<br>D1.2 Descargar EVA reciente 2019-2024<br>D1.3 Unificar columnas y normalizar nombres<br>D1.4 Guardar `eva_historica.parquet` + `eva_reciente.parquet` | Agente datos | 2 archivos Parquet |
| D2 | Pipeline Clima | D2.1 Obtener estaciones IDEAM para los 15 municipios<br>D2.2 Descargar precipitación agregada por mes/año<br>D2.3 Descargar temperatura agregada por mes/año<br>D2.4 Calcular anomalías respecto a media histórica<br>D2.5 Guardar `clima_agregado.parquet` | Agente datos | 1 archivo Parquet |
| D3 | Pipeline UPRA | D3.1 Descargar aptitud café (GROUP BY SoQL)<br>D3.2 Descargar aptitud cacao<br>D3.3 Descargar aptitud maíz (unión 3 datasets)<br>D3.4 Descargar frontera agrícola<br>D3.5 Guardar 4 archivos Parquet | Agente datos | 4 archivos Parquet |
| D4 | Pipeline Económico | D4.1 Descargar índice de agroinsumos completo<br>D4.2 Calcular percentil histórico por mes<br>D4.3 Guardar `agroinsumos.parquet` | Agente datos | 1 archivo Parquet |
| D5 | Tabla maestra | D5.1 Cruzar EVA + Clima + UPRA + Económico por municipio/cultivo/año<br>D5.2 Calcular features rezagadas<br>D5.3 Validar completitud para los 15 municipios<br>D5.4 Guardar `tabla_maestra.parquet` | Agente datos | 1 archivo Parquet |

### Capa de Modelo — Semana 2

| ID | Tarea | Subtareas | Agente IA | Entregable |
|----|-------|-----------|-----------|-----------|
| M1 | Feature engineering | M1.1 Crear variables climáticas (anomalía, días secos, acumulado)<br>M1.2 Crear variables de rezago (rend t-1, prom 3a, tendencia)<br>M1.3 Crear variables de aptitud (pct_alta, pct_media)<br>M1.4 Crear variable de riesgo económico | Agente ML | Features validadas |
| M2 | Modelo rendimiento | M2.1 Split temporal (train 2007-2022, val 2023, test 2024)<br>M2.2 Entrenar XGBoost Regressor por cultivo<br>M2.3 Calcular MAE, RMSE, R² por cultivo y departamento<br>M2.4 Guardar modelos `.pkl` | Agente ML | 3 modelos .pkl + métricas |
| M3 | Modelo riesgo | M3.1 Definir etiqueta riesgo (caída > 15% vs media histórica)<br>M3.2 Entrenar XGBoost Classifier<br>M3.3 Calcular F1, AUC, calibración<br>M3.4 Guardar modelos `.pkl` | Agente ML | 3 modelos .pkl + métricas |
| M4 | SHAP | M4.1 Calcular SHAP values para conjunto de validación<br>M4.2 Identificar top 5 features por predicción<br>M4.3 Generar plantillas de narrativa por nivel de riesgo | Agente ML | SHAP values + narrativas |
| M5 | Escenarios | M5.1 Implementar simulación año seco (-30% lluvia)<br>M5.2 Implementar simulación año lluvioso (+30% lluvia)<br>M5.3 Implementar simulación subida fertilizantes (+20%) | Agente ML | Función de escenarios |

### Capa de API — Semana 3

| ID | Tarea | Subtareas | Agente IA | Entregable |
|----|-------|-----------|-----------|-----------|
| A1 | Endpoints predicción | A1.1 `POST /predecir` — predicción + riesgo + SHAP<br>A1.2 `GET /municipios` — lista de municipios disponibles<br>A1.3 `GET /cultivos/{municipio}` — cultivos disponibles | Agente backend | Endpoints funcionales |
| A2 | Endpoints históricos | A2.1 `GET /rendimiento/{municipio}/{cultivo}` — serie histórica<br>A2.2 `GET /clima/{municipio}` — serie climática | Agente backend | Endpoints funcionales |
| A3 | Endpoints escenarios | A3.1 `POST /escenario` — predicción bajo escenario climático | Agente backend | Endpoint funcional |
| A4 | Endpoint chat | A4.1 `POST /chat` — pregunta + contexto → respuesta LLM<br>A4.2 `GET /reporte/{municipio}/{cultivo}` — reporte PDF/texto | Agente backend | Endpoints funcionales |

### Capa de Frontend — Semana 3

| ID | Tarea | Subtareas | Agente IA | Entregable |
|----|-------|-----------|-----------|-----------|
| F1 | Mapa de riesgo | F1.1 Mapa Colombia con react-leaflet<br>F1.2 Color por nivel de riesgo (verde/amarillo/rojo)<br>F1.3 Filtro por cultivo<br>F1.4 Click en municipio → ficha | Agente frontend | Pantalla mapa |
| F2 | Ficha municipal | F2.1 Gráfica rendimiento histórico (react-plotly)<br>F2.2 Semáforo de riesgo con probabilidad<br>F2.3 Barras SHAP de factores explicativos<br>F2.4 Recomendación accionable | Agente frontend | Pantalla ficha |
| F3 | Comparador cultivos | F3.1 Selector de 2-3 cultivos<br>F3.2 Tabla comparativa rendimiento/riesgo/aptitud<br>F3.3 Ranking recomendado con justificación | Agente frontend | Pantalla comparador |
| F4 | Asistente IA | F4.1 Chat interface con shadcn/ui<br>F4.2 Integración con endpoint `/chat`<br>F4.3 Botón "Generar reporte" | Agente frontend | Pantalla chat |

### Capa Conversacional — Semana 4

| ID | Tarea | Subtareas | Agente IA | Entregable |
|----|-------|-----------|-----------|-----------|
| C1 | RAG | C1.1 Indexar predicciones + SHAP como contexto recuperable<br>C1.2 Función de recuperación por municipio/cultivo | Agente conversacional | Motor RAG |
| C2 | Prompts | C2.1 Prompt para explicación en lenguaje campesino<br>C2.2 Prompt para reporte institucional (UMATA)<br>C2.3 Prompt para comparación de cultivos | Agente conversacional | Plantillas de prompt |
| C3 | Reportes | C3.1 Plantilla reporte PDF por municipio<br>C3.2 Generación automática con datos del modelo | Agente conversacional | Generador de reportes |

---

## Principios del enfoque Spec-Driven aplicados

| Principio | Aplicación concreta |
|-----------|---------------------|
| **Spec antes de código** | Cada tarea tiene su spec en `specs/` antes de que el agente escriba una línea |
| **Criterios de aceptación verificables** | Cada spec tiene checklist que el agente puede ejecutar para validar su propio output |
| **Contexto acotado por capa** | El agente de datos no necesita saber nada de React; el agente de frontend no necesita saber nada de XGBoost |
| **Contratos de interfaz explícitos** | Cada módulo define exactamente qué produce (columnas, formato, tipos) para que el siguiente módulo no tenga sorpresas |
| **Paralelización** | Las tareas D1-D4 se pueden ejecutar en paralelo; M1-M5 dependen de D5; A1-A4 dependen de M2-M3 |

---

## Municipios del MVP validados con datos reales

Los 15 municipios seleccionados tras cruzar todas las fuentes (ver `municipios_cobertura.md`):

| Municipio | Departamento | Años EVA | Est. IDEAM | Zona PDET |
|-----------|-------------|---------|-----------|-----------|
| Ibagué | Tolima | 18 | 20 | No |
| Chaparral | Tolima | 18 | 13 | ✅ Sí |
| Neiva | Huila | 18 | 10 | No |
| Garzón | Huila | 18 | 9 | No |
| Pitalito | Huila | 18 | 6 | No |
| San Vicente de Chucurí | Santander | 18 | 12 | No |
| Rionegro | Santander | 18 | 19 | No |
| Anorí | Antioquia | 18 | 14 | ✅ Sí |
| Amalfi | Antioquia | 18 | 12 | No |
| Pensilvania | Caldas | 18 | 20 | No |
| Palestina | Caldas | 18 | 13 | No |
| Villavicencio | Meta | 18 | 15 | No |
| El Tambo | Cauca | 18 | 12 | ✅ Sí |
| Miranda | Cauca | 18 | 12 | No |
| Valledupar | Cesar | 18 | 14 | No |

Todos tienen cobertura en las 7 fuentes simultáneamente: EVA + IDEAM (prec+temp+hum) + UPRA (café+cacao+maíz+frontera) + Agroinsumos.
