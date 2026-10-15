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
