---
tipo: bitacora-integrante
integrante: Jonmor
---
# Bitácora de Jonmor

Una entrada por avance o commit relevante, la más reciente arriba.

Formato: `### AAAA-MM-DD HH:MM · <tema> · <commit corto>` y debajo qué se hizo, qué falta y si algo bloquea a otro integrante.


### 2026-10-15 · T15 · ver commit T15

Stack ChileAtiendeChat desplegado: health 200 con Converse real, 401 sin key y 403 con key inválida. Bundle Linux y síntesis OK; 177 tests y verificador TODO OK. [[chatbot-desplegado]].

### 2026-10-15 · T16 · ver commit T16

Repositorio DynamoDB con mensajes append-only, GSI por RUN y paginación. Dos pruebas moto verifican Case completo, consentimiento/revocación, orden estable, DV y caso ausente. [[chatbot-desplegado]].

### 2026-10-15 · T17 · ver commit T17

Turnos guardados en DynamoDB con leer_caso como única herramienta y evaluación determinista separada del contrato compartido. Tres pruebas offline demuestran continuidad de dos turnos, denegación de evaluación sin permiso y persistencia al agotar iteraciones. [[chatbot-desplegado]].

### 2026-10-15 · T18 · ver commit T18

Rutas HTTP v2 con validación, ámbito por RUN y consentimiento explícito. Pruebas sintéticas: 400/403/404, aceptación antes de permiso, revocación al declinar y ocultación de errores internos. x-run es ámbito de integración demo, no identidad ciudadana verificada. [[chatbot-desplegado]].

### 2026-10-15 · T19 · ver commit T19

Phoenix 12.35 local verificado en Chrome: proyecto ca-chat, una traza chat.turn y dos bedrock.converse hijos confirmados por API del colector. Trace ID 07ede8f4a30670148475cb21d5bf3d22, leer_caso OK, latencia 17,8 s. Sin endpoint queda inerte; exportador caído no rompe respuesta. Tres pruebas offline pasan. Instalación aislada con restricciones de dependencias documentada en [[chatbot-desplegado]].
