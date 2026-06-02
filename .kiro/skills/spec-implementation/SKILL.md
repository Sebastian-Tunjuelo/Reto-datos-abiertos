---
name: spec-implementation
description: "Implementar especificaciones (specs) del proyecto y mantener la documentación sincronizada. Usar siempre que se implemente una spec, se completen criterios de aceptación o se actualice el contexto/docs por cambios de alcance, rendimiento o correcciones."
argument-hint: "ID de spec o ruta de archivo (ej.: D1.1 o specs/D1_pipeline_eva/D1.1_historica.md)"
---

# Implementación y sincronización de specs

## Cuándo usar

- Implementar cualquier tarea que haga referencia a una spec o criterios de aceptación.
- Actualizar una spec luego de cambios en código, o mantener el contexto/docs alineados.
- Ajustar alcance (MVP, rendimiento, correcciones) que afecte la spec o sus outputs.

## Entradas necesarias

- Archivo de la spec o ID.
- Módulo/función objetivo y outputs esperados.
- Restricciones (alcance MVP, performance, fechas límite).

Si falta o hay ambigüedad en cualquiera, preguntar antes de implementar.

## Flujo de trabajo

### 1) Leer y mapear la spec

- Abrir la spec y extraer: objetivo, entradas/salidas, pasos de transformación, interfaz y criterios de aceptación.
- Identificar archivos de código y funciones señaladas en la metadata.
- Anotar specs o docs relacionadas que dependan de este output.

### 2) Planificar la implementación

- Mapear cada paso de la spec a cambios de código concretos.
- Enumerar dependencias externas (datasets, variables de entorno, helpers).
- Señalar pasos poco claros o faltantes.

### 3) Resolver ambigüedades (obligatorio)

- Si la spec es ambigua o contradice el código/datos, preguntar al autor.
- Proponer 1 opción recomendada con breve justificación.
- No asumir comportamientos que cambien contratos o outputs sin aprobación.

### 4) Implementar según la spec (sin extras)

- Seguir la spec exactamente; no añadir lógica no especificada.
- Mantener los cambios localizados en el módulo/función indicado salvo que la spec exija lo contrario.

### 5) Verificar contra los criterios de aceptación

- Comprobar cada ítem de aceptación frente a la implementación.
- Marcar un ítem como completado solo si hay evidencia suficiente.
- Si un ítem no puede verificarse, dejarlo sin marcar y explicar por qué.

### 6) Actualizar la spec

- Actualizar el campo "Estado" en la metadata para reflejar el avance.
- Actualizar la checklist de aceptación: marcar [x] solo cuando esté verificado.
- Si se cambiaron alcance o lógica:
  - Preferir una sección existente llamada "Decisiones" o "Notas"; si no existe, crear "Decisiones".
  - Incluir fecha, motivo, decisión y su impacto.
  - Ajustar pasos, esquema y criterios de aceptación para mantener coherencia.

### 7) Actualizar contexto del proyecto y documentación

- Actualizar `.agents/contexto_proyecto.md`:
  - La tabla de estado de specs para la spec modificada.
  - La tabla de estado de código si cambió la implementación del módulo.
- Actualizar `docs/` solo si el cambio afecta documentación de dominio o usuario.

### 8) Reportar resultados

- Resumir cambios de código, actualizaciones en la spec y ajustes en contexto/docs.
- Listar preguntas abiertas, supuestos y verificaciones pendientes.

## Checklist de calidad

- Todos los pasos de la spec mapeados a cambios de código.
- Criterios de aceptación actualizados honestamente.
- Metadata de la spec refleja el estado real.
- Contexto y docs sincronizados con los cambios.

## Ejemplos de prompts

- "Implementar D2.2 exactamente como indica la spec y actualizar la checklist"
- "Terminar D5.3 y reflejar el estado en contexto_proyecto"
- "Reducir alcance de D3.2 para el MVP; actualizar la spec e implementarla"
