# Spec: F3 Comparador de cultivos

## Contexto

El "Comparador de cultivos" tiene como objetivo traducir los resultados de nuestros modelos y cálculos en una herramienta visual de decisión. Dado un municipio, el usuario debe saber fácilmente, entre los cultivos MVP (Café, Cacao, Maíz), cuál le conviene más sembrar atendiendo rendimiento, riesgo climático y factores socioeconómicos/UPRA.

## Subtareas

| ID   | Archivo                       | Qué hace                                                                   | Depende de                                       | Estado       |
| ---- | ----------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------ | ------------ |
| F3.1 | `F3.1_pantalla_comparador.md` | Especifica la vista de ranking y tabla de comparación de los tres cultivos | F2 (Componentes base), A1 (Rutas API para score) | 📝 Pendiente |

## Dependencias

- Componentes de [shadcn/ui](../skills/shadcn-ui).
- Rutas de las APIs predictivas construidas en [A1_api_mvp](../A1_api_mvp).

## Produce para

- Productores agropecuarios, UMATAs y extensionistas rurales.
