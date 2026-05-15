# docs/ — Contexto e investigación del proyecto

Esta carpeta contiene el conocimiento estratégico, técnico y de dominio del proyecto SiembraSegura IA. No es código ejecutable ni specs de implementación — es el contexto que cualquier agente o miembro del equipo debe leer antes de tomar decisiones de diseño o implementación.

## Estructura

```
docs/
├── proyecto/
│   ├── vision_y_estrategia.md   ← qué construimos, por qué y para quién
│   └── arquitectura.md          ← stack, módulos, flujo de orquestación
├── datos/
│   ├── datasets_referencia.md   ← IDs Socrata, columnas reales, advertencias técnicas
│   └── municipios_mvp.md        ← los 15 municipios con cobertura verificada
└── dominio/
    └── glosario_agricola.md     ← términos clave del dominio agrícola colombiano
```

## Cuándo leer cada archivo

| Tarea que vas a hacer | Leer primero |
|-----------------------|-------------|
| Diseñar un módulo nuevo | `proyecto/vision_y_estrategia.md` + `proyecto/arquitectura.md` |
| Implementar un pipeline de datos | `datos/datasets_referencia.md` + `datos/municipios_mvp.md` |
| Escribir una spec | `proyecto/arquitectura.md` + el archivo de datos relevante |
| Implementar el módulo conversacional | `proyecto/vision_y_estrategia.md` + `dominio/glosario_agricola.md` |
| Onboarding de un nuevo integrante | Leer en orden: visión → arquitectura → datasets → municipios |

## Relación con otras carpetas

- `docs/` → contexto e investigación (este directorio)
- `specs/` → especificaciones ejecutables por capa y tarea
- `modules/` → código de implementación
- `shared/` → utilidades compartidas entre módulos
