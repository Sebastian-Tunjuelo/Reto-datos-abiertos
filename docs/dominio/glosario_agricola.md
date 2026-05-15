# Glosario agrícola — SiembraSegura IA

Términos clave del dominio agrícola colombiano. Leer antes de implementar el módulo conversacional, escribir prompts o generar narrativas de riesgo. Evita que la IA confunda conceptos o use terminología incorrecta con productores e instituciones.

---

## Términos de producción agrícola

### Rendimiento (t/ha)
Producción obtenida por unidad de área. Se calcula como `producción_total / área_cosechada`. Es la **variable objetivo** del modelo predictivo.
- No confundir con **producción** (toneladas totales) ni con **área sembrada**.
- Un rendimiento bajo puede deberse a clima adverso, plagas, baja aptitud del suelo o malas prácticas.
- Unidad: toneladas por hectárea (t/ha).

### Área sembrada vs área cosechada
- **Área sembrada**: hectáreas donde se plantó el cultivo en un periodo.
- **Área cosechada**: hectáreas efectivamente recolectadas. Siempre ≤ área sembrada.
- La diferencia entre ambas indica pérdidas por clima, plagas o abandono.
- ⚠️ No usar área cosechada del mismo periodo como variable predictora — causa fuga de información.

### Producción (toneladas)
Total de producto recolectado en un municipio, cultivo y periodo. Se deriva de `rendimiento × área_cosechada`. No es una variable independiente del rendimiento.

### Ciclo de cultivo
- **PERMANENTE**: cultivos que producen durante varios años sin resembrar (café, cacao, plátano). La cosecha puede ser semestral o anual.
- **TRANSITORIO**: cultivos que se siembran y cosechan en un solo ciclo (maíz, arroz, papa). Tienen periodos A (primer semestre) y B (segundo semestre).

### Periodo agrícola
- **Año único** (ej. `'2015'`): cultivos permanentes con reporte anual.
- **Semestre A** (ej. `'2015A'`): primer semestre, generalmente enero–junio.
- **Semestre B** (ej. `'2015B'`): segundo semestre, generalmente julio–diciembre.
- El maíz tecnificado tiene datos por semestre; el café y cacao suelen ser anuales.

---

## Cultivos del MVP

### Café
- Cultivo permanente, ciclo productivo de 20–30 años.
- Colombia produce principalmente café arábica lavado.
- Sensible a temperatura (óptimo 18–24°C) y precipitación (1.800–2.800 mm/año).
- Zonas principales: Huila, Nariño, Cauca, Tolima, Antioquia, Caldas, Risaralda, Quindío.
- Rendimiento típico Colombia: 0.5–2.0 t/ha. Café especial puede superar 2.0 t/ha.
- Amenazas climáticas: déficit hídrico en floración, exceso de lluvia en cosecha, temperaturas extremas.

### Cacao
- Cultivo permanente, inicia producción a los 3–4 años.
- Relevante en zonas de sustitución de cultivos ilícitos (PDET).
- Sensible a humedad relativa alta (favorece enfermedades como monilia y escoba de bruja).
- Zonas principales: Santander, Norte de Santander, Arauca, Meta, Antioquia, Nariño.
- Rendimiento típico Colombia: 0.3–2.0 t/ha. Productores tecnificados pueden superar 1.5 t/ha.
- Amenazas climáticas: exceso de humedad, déficit hídrico en cuajado de frutos.

### Maíz
- Cultivo transitorio, ciclo de 90–120 días.
- Dos tipos: **tradicional** (0.5–3.0 t/ha) y **tecnificado** (3.0–9.0 t/ha).
- Seguridad alimentaria y materia prima para industria.
- Zonas principales: Meta, Córdoba, Tolima, Cesar, Bolívar, Huila.
- Muy sensible a déficit hídrico en floración y llenado de grano.
- Alta variabilidad de rendimiento (CV 30–78%) → buena señal para el modelo.

---

## Instituciones y actores

### UMATA
Unidad Municipal de Asistencia Técnica Agropecuaria. Entidad municipal que brinda asistencia técnica a pequeños productores. Es el **usuario institucional primario** de SiembraSegura IA. Los reportes y recomendaciones deben estar en lenguaje accesible para técnicos de UMATA.

### Extensionista
Técnico o profesional que visita fincas y asesora a productores sobre prácticas agrícolas. Intermediario entre la información técnica y el productor.

### UPRA
Unidad de Planificación Rural Agropecuaria. Entidad del Ministerio de Agricultura que produce los mapas de aptitud agroecológica y frontera agrícola. Sus datos son la fuente de aptitud del modelo.

### IDEAM
Instituto de Hidrología, Meteorología y Estudios Ambientales. Fuente oficial de datos climáticos en Colombia. Opera la red de estaciones meteorológicas.

### PDET
Programas de Desarrollo con Enfoque Territorial. Zonas priorizadas para la paz y el desarrollo rural en Colombia. Tres municipios del MVP son PDET: Chaparral, Anorí, El Tambo.

---

## Conceptos climáticos aplicados al agro

### Anomalía climática
Desviación del valor observado respecto a la media histórica del mismo mes/periodo. Una anomalía de precipitación de -30% significa que llovió 30% menos de lo normal.

### Déficit hídrico
Situación donde la precipitación es insuficiente para las necesidades del cultivo. Crítico en floración y llenado de frutos.

### Días secos consecutivos
Número de días sin lluvia significativa (< 1 mm). Indicador de estrés hídrico acumulado.

### Estrés térmico
Condición donde la temperatura supera el umbral óptimo del cultivo. Para café: temperaturas > 30°C afectan la fotosíntesis y la calidad del grano.

### Fenómeno El Niño / La Niña
- **El Niño**: reduce precipitaciones en la región andina colombiana → déficit hídrico → caída de rendimiento en café y cacao.
- **La Niña**: aumenta precipitaciones → exceso de humedad → favorece enfermedades en cacao, dificulta cosecha de café.

---

## Conceptos del modelo y la plataforma

### Semáforo de riesgo
Clasificación del riesgo de caída de rendimiento en tres niveles:
- 🟢 **Bajo**: rendimiento esperado dentro del rango histórico normal (caída < 10%)
- 🟡 **Medio**: caída esperada entre 10% y 20% vs promedio histórico municipal
- 🔴 **Alto**: caída esperada > 20% vs promedio histórico municipal

### Aptitud agroecológica
Clasificación del territorio según su idoneidad para un cultivo específico, basada en suelo, clima y topografía. Categorías UPRA: Alta, Media, Baja, No apta.

### Frontera agrícola
Límite establecido por el Estado colombiano que delimita las áreas donde se permite la actividad agropecuaria. Áreas fuera de la frontera no deben recibir recomendaciones de siembra.

### Fuga de información (data leakage)
Error de modelado donde se usan como variables predictoras datos que no estarían disponibles al momento de hacer la predicción. En este proyecto: usar `producción` o `área_cosechada` del mismo año que se quiere predecir es fuga de información, porque el rendimiento se calcula a partir de esas variables.

### Validación temporal
Método correcto para evaluar modelos de series de tiempo agrícolas: entrenar con años pasados, validar con años futuros. **Nunca** hacer split aleatorio en datos temporales.

---

## Términos que NO deben confundirse

| Término A | Término B | Diferencia |
|-----------|-----------|------------|
| Rendimiento (t/ha) | Producción (t) | Rendimiento es por hectárea; producción es el total |
| Área sembrada | Área cosechada | Sembrada ≥ cosechada; la diferencia son pérdidas |
| Precio al productor | Precio mayorista | El productor recibe menos que el precio de mercado |
| Predicción | Pronóstico | Predicción usa datos históricos; pronóstico requiere datos futuros de clima |
| Aptitud alta | Rendimiento alto | Un municipio puede tener aptitud alta pero rendimiento bajo por otros factores |
| Periodo A | Primer semestre | Equivalentes para cultivos transitorios; los permanentes no tienen periodo A/B |
