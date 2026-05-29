# F4 — Chat interface: asistente conversacional + botón "Generar reporte"

## Resumen

Implementa la pantalla de asistente conversacional de SiembraSegura IA en el frontend.
Integra el endpoint `POST /chat` con una interfaz de chat shadcn/ui, permite seleccionar
municipio y cultivo como contexto, y expone el botón "Generar reporte" que descarga el PDF
desde `GET /reporte/{municipio}/{cultivo}?formato=pdf`.

## Contexto del dominio

El backend ya tiene:
- `POST /chat` — recibe `{pregunta, municipio, cultivo, año, tono}`, retorna `{respuesta, fuentes}`
- `GET /reporte/{municipio}/{cultivo}?formato=pdf` — retorna bytes del PDF
- `GET /reporte/{municipio}/{cultivo}?formato=texto` — retorna JSON con `contenido_texto`

El frontend ya tiene F1 (mapa), F2 (ficha municipal) y F3 (comparador). F4 agrega la pantalla
de asistente accesible desde la navegación principal y desde la ficha municipal.

## Subtareas

| ID   | Archivo                                                                          | Qué hace                                                                                                  | Depende de                                                                                  | Estado       |
| ---- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------ |
| F4.1 | [F4.1_pagina_chat.md](F4.1_pagina_chat.md)                                       | Ruta `/asistente` con layout, selector de contexto (municipio/cultivo/tono) y área de chat                | `frontend/src/app/`, shadcn/ui, `NEXT_PUBLIC_API_BASE_URL`                                  | ✅ Completo |
| F4.2 | [F4.2_componente_chat.md](F4.2_componente_chat.md)                               | Componente `ChatAsistente` con historial de mensajes, input, envío a `POST /chat` y estado de carga       | F4.1, `POST /chat`                                                                          | ✅ Completo |
| F4.3 | [F4.3_boton_reporte.md](F4.3_boton_reporte.md)                                   | Botón "Generar reporte PDF" que descarga el PDF desde `GET /reporte/{municipio}/{cultivo}?formato=pdf`    | F4.1, `GET /reporte`                                                                        | ✅ Completo |
| F4.4 | [F4.4_integracion_navegacion.md](F4.4_integracion_navegacion.md)                 | Agrega enlace "Asistente" al header de `page.tsx` y botón "Consultar asistente" en `FichaMunicipal.tsx`   | F4.1, F4.2, F4.3                                                                            | ✅ Completo |

> F4.1 y F4.2 son paralelas. F4.3 depende de F4.1. F4.4 integra todo.

## Outputs finales

| Artefacto                                                    | Descripción                                                                                                    |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| `frontend/src/app/asistente/page.tsx`                        | Ruta `/asistente` con selector de contexto y área de chat                                                      |
| `frontend/src/components/chat/ChatAsistente.tsx`             | Componente de chat con historial, input y envío                                                                 |
| `frontend/src/components/chat/BotonReportePDF.tsx`           | Botón de descarga de PDF con estado de carga                                                                    |
| `frontend/src/components/chat/SelectorContexto.tsx`          | Selector de municipio, cultivo y tono para el chat                                                              |
| `frontend/src/app/page.tsx` (modificado)                     | Enlace "Asistente" en el header                                                                                 |
| `frontend/src/components/FichaMunicipal.tsx` (modificado)    | Botón "Consultar asistente" que navega a `/asistente?municipio=...&cultivo=...`                                 |

## Contrato de la API consumida

### `POST /chat`

```typescript
// Request
{
  pregunta: string,
  municipio?: string,   // nombre display o código DANE
  cultivo?: string,     // 'Café' | 'Cacao' | 'Maíz'
  año?: number,
  tono?: 'campesino' | 'institucional'  // default: 'campesino'
}

// Response
{
  respuesta: string,
  fuentes?: string[]
}
```

### `GET /reporte/{municipio}/{cultivo}?formato=pdf`

Retorna `application/pdf` como bytes. El municipio puede ser nombre display o código DANE.

## Dependencias compartidas

| Módulo / artefacto                          | Uso                                                                                  |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `NEXT_PUBLIC_API_BASE_URL`                  | Base URL del backend (`.env.local`)                                                  |
| `shadcn/ui`                                 | `Button`, `Select`, `Textarea`, `Card`, `Badge`, `Separator`                         |
| `lucide-react`                              | `Send`, `FileDown`, `Bot`, `User`, `Loader2`, `MessageSquare`                        |
| `next/navigation`                           | `useSearchParams` para leer `?municipio=...&cultivo=...` desde la URL                |
| `GET /municipios`                           | Lista de municipios para el selector de contexto                                     |
| `GET /cultivos/{municipio}`                 | Lista de cultivos disponibles para el municipio seleccionado                         |

## Restricciones técnicas comunes

- Usar `"use client"` en todos los componentes interactivos.
- No usar `inplace=True` — no aplica a frontend, pero sí: no mutar el array de mensajes directamente.
- Usar `dynamic` con `ssr: false` solo si hay dependencias de browser (no necesario para chat).
- El historial de mensajes vive en estado local del componente — no persistir en localStorage.
- El tono por defecto es `"campesino"`. El usuario puede cambiarlo a `"institucional"`.
- Si `NEXT_PUBLIC_API_BASE_URL` no está configurado, mostrar banner de advertencia.
- El botón de PDF debe manejar el estado de descarga (loading, error) sin bloquear el chat.
- Accesibilidad: el input de chat debe tener `aria-label`, los mensajes deben tener roles semánticos.

## Produce para

- Usuarios finales: extensionistas, técnicos UMATA que quieren hacer preguntas en lenguaje natural
- Demo del hackathon: pantalla de asistente como diferenciador clave
