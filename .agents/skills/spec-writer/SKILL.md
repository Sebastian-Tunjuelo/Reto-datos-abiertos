---
name: spec-writer
description: Crear specs claros, atómicos y verificables a partir de una idea, un borrador o dos documentos de referencia. Usa esta skill siempre que el usuario pida redactar, estructurar, normalizar, revisar o convertir requerimientos en una especificación lista para implementar.
---

# Spec Writer

Esta skill define una forma estándar de redactar specs que combina lo mejor de una tarea atómica y de una especificación técnica verificable.

## Cuándo usarla

Usa esta skill cuando el usuario quiera:

- redactar un spec desde cero
- transformar notas, ideas o tickets en una especificación formal
- unificar varios documentos en una sola estructura de spec
- revisar si un spec tiene alcance, inputs, validaciones y criterios de aceptación suficientes
- dividir una petición grande en varias specs más pequeñas y verificables

## Principios

- Un spec debe describir un solo propósito principal.
- Si hay más de un objetivo principal, primero divide la solicitud.
- Si algo no está claro, pregunta antes de asumir.
- El spec debe poder validarse de forma objetiva.
- El alcance debe ser explícito: qué incluye y qué no incluye.
- La redacción debe favorecer claridad operativa, no solo intención general.
- La estructura preferida es modular: un README de overview + N subtareas.
- La cantidad de subtareas no es fija; se divide según complejidad y dependencias.

## Proceso de redacción

1. Identifica el objetivo único del spec.
2. Recupera el contexto mínimo necesario: estado inicial, dependencias, archivos, entradas, restricciones y salida esperada.
3. Decide si el spec debe dividirse en partes (README + subtareas).
4. Define el rol del agente o responsable si el spec lo requiere.
5. Especifica el alcance con límites claros.
6. Describe los inputs esperados y sus condiciones.
7. Explica el proceso o lógica sugerida paso a paso.
8. Define la salida esperada de forma verificable.
9. Incluye manejo de errores, validaciones y advertencias cuando aplique.
10. Cierra con criterios de aceptación y calidad que permitan validar el resultado.

## Estructura ideal de un spec

Usa esta secuencia como base y adáptala según el caso:

```markdown
# [Nombre del spec]

## Metadatos

- ID:
- Módulo o área:
- Depende de:
- Produce para:
- Estado:

## Agente

- role:
- goal:
- backstory:

## Objetivo

- Un único resultado de negocio o técnico que se debe lograr.

## Alcance

### Incluye

- Qué sí se hará.

### No incluye

- Qué queda fuera del alcance.

## Entradas

- Información de entrada, archivos, parámetros, dependencias y estado inicial.

## Inputs esperados

- Lista de fuentes, claves, archivos, endpoints o artefactos de entrada.
- Para cada input, especifica columnas, campos, tipos o reglas mínimas cuando aplique.

## Lógica / Proceso sugerido

1. Paso a paso, en orden claro.
2. Incluir decisiones y ramas relevantes.
3. Indicar qué hacer si falta información o si falla una validación.

## Interfaz o contrato

- Función, comando, endpoint, archivo, formato o salida que debe producirse.

## Manejo de errores

- Qué falla de forma explícita.
- Qué se registra como warning.
- Qué mensajes de error deben quedar visibles.

## Salida esperada

- Entregable concreto y verificable.
- Formato de salida si aplica.

## Caso feliz

- Dado una entrada válida
- Cuando se ejecuta la tarea
- Entonces se obtiene la salida esperada

## Validación

- Dado una entrada inválida o incompleta
- Cuando se ejecuta la tarea
- Entonces se rechaza con un error claro y accionable

## Criterios de aceptación

- Claridad
- Atomicidad
- Trazabilidad
- Verificabilidad

## Regla de división

- Si el spec tiene más de un objetivo principal, divídelo.
- Si requiere múltiples entregables no acoplados, divídelo.
- Si no puede validarse en una sola revisión razonable, divídelo.
- No fijar un número de subtareas: dividir según complejidad y dependencias.
```

## Criterios de calidad para redactar

- Preferir frases cortas y directas.
- Usar tablas cuando haya entradas, dependencias o reglas repetitivas.
- Dar mensajes de error explícitos y accionables.
- No inventar columnas, campos o archivos si no están confirmados.
- Incluir ejemplos solo cuando aclaren un comportamiento ambiguo.

## Patrón de salida recomendado

Cuando el usuario pida un spec, entrega uno de estos dos formatos:

1. Un spec completo listo para pegar en el repositorio.
2. Una estructura base con preguntas puntuales si faltan datos críticos.

## Estructura modular recomendada (README + subtareas)

Cuando el trabajo tenga varios pasos o entregables, escribe el spec en partes:

### 1) README de overview

Debe incluir:

- Resumen corto
- Contexto del dominio
- Tabla de subtareas (ID, archivo, qué hace, depende de, estado)
- Outputs finales
- Esquema o contrato global si aplica
- Dependencias compartidas
- Restricciones técnicas comunes
- Produce para

### 2) Subtareas (N archivos)

Cada subtarea sigue la estructura ideal del spec y cubre un objetivo único.
La cantidad N es flexible y debe ajustarse al alcance real.

### 3) Reglas de división

- Divide por etapas lógicas (ingesta, transformación, validación, guardado).
- Acepta dependencias lineales o paralelas según corresponda.
- Si una subtarea tiene más de un objetivo, vuelve a dividirla.

## Checklist final

Antes de cerrar un spec, confirma que tenga:

- un objetivo único
- alcance explícito
- entradas bien definidas
- proceso o lógica accionable
- salida esperada verificable
- manejo de errores o validaciones
- criterios de aceptación
