---
tipo: adr
estado: aceptada
fecha: 2026-10-14
---
# ADR 0006 — Ayuda para trámites dentro de una estructura ChileAtiende

## Contexto
El usuario pidió usar exclusivamente `https://www.chileatiende.gob.cl/` como referencia y presentar el MVP como una pestaña de ayuda para trámites con la ruta existente y el agente como chatbot. Se conserva el aporte Streamlit de Johann y el enfoque de [0005-asistente-contacto-escalonado](0005-asistente-contacto-escalonado.md).

## Decisión
- Mantener Streamlit para la demo e incorporar encabezado, navegación, buscador, destacados, momentos de vida, servicios por temas y pie de contacto inspirados en la estructura del HTML oficial recuperado el 14-10-2026.
- Abrir por defecto **Ayuda para tus trámites**, con la ruta y el chatbot lado a lado. Inicio ofrece accesos al portal oficial; Mi ruta retoma el mismo caso.
- Reutilizar `src.agent.loop.Agent`, prompt y cliente Bedrock compartidos para el chat configurado. Adaptador `src/app/ruta/chatbot.py`: `leer_caso` entrega el contexto determinista y autorizado de la app; no hay un segundo motor de elegibilidad.
- Mantener respuestas por plantillas cuando Bedrock no esté configurado/no disponible y ante falta de consentimiento. La ruta personalizada de la demo cubre jubilación/PGU; los demás trámites se consultan mediante enlaces/buscador del portal oficial.

## Consecuencias
No se reconstruye todo ChileAtiende ni se implementa su login. La navegación oficial abre destinos reales; la nueva ayuda es un prototipo rotulado. La integración de chat no unifica todavía SQLite con el repositorio del agente ni resuelve las diferencias normativas del motor, documentadas en revision-aporte-johann. Fuentes y verificación en [portal-ayuda-tramites](../portal-ayuda-tramites.md).
