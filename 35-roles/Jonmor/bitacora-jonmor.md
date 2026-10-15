---
tipo: bitacora-integrante
integrante: Jonmor
---
# Bitácora de Jonmor

Una entrada por avance o commit relevante, la más reciente arriba.

Formato: `### AAAA-MM-DD HH:MM · <tema> · <commit corto>` y debajo qué se hizo, qué falta y si algo bloquea a otro integrante.

### 2026-10-15 · Conversación y voz del asistente · 7ba7c2f

Estilo natural ante insultos, ruido y frustración, con memoria pública separada en Mi Gobierno y reinicio al cambiar permisos. Dictado editable con envío explícito y voz sintética opcional en español, escuchar/detener, pausa al dictar y prevención de duplicados. 43 pruebas enfocadas, tres turnos reales Sonnet 5 y controles Chromium simulados OK. Tras integrar el portal ejecutivo: 234 pruebas pasan, dos omitidas por dependencias opcionales y ocho evals excluidas; verificador TODO OK. [[0017-conversacion-y-voz-del-navegador]].

### 2026-10-15 · Elegibilidad personal del chat · 78bfcf6

Corregida la frase exacta «puedo tener yo la pgu?» y variantes; sin permiso indica casilla y Activar Mi Gobierno, con permiso usa el agente y datos calculados. Consultas generales sin lista cerrada de palabras. 31 pruebas enfocadas y verificador TODO OK. [[portal-ayuda-tramites]].

### 2026-10-15 · Consultas generales del chatbot · 33eed79

Corregido resumen repetido sin permiso: información general por Bedrock con solo pregunta y fuentes públicas; consultas personales requieren autorización. Respaldo pertinente y sin historial revocado. 23 pruebas enfocadas y llamada real Sonnet 5 OK. Integración d8bde76 conserva /chat y su historial público, usando cliente compartido sin temperature. [[0015-orientacion-general-sin-perfil]].

### 2026-10-15 18:54 · T21 · a54d5df

Stack completo desplegado en UPDATE_COMPLETE. Tres turnos HTTPS recuerdan Rosa/teléfono y AWS CLI confirma seis mensajes. Auth 401/403/200, 188 pruebas offline, verificador 500 perfiles TODO OK, synth y assertions CDK OK. Phoenix Lambda cableado e inerte; endpoint remoto no configurado. [[chatbot-desplegado]] y [[0014-chatbot-api-desplegada]].

Integración final: cinco fallos UI reproducidos en snapshot limpio de origin/main 9486b88 (navegación/banner). No provienen de este aporte; se documentan sin modificar la UI. Throttle real 2/s y burst 4 comprobados por API Gateway.

### 2026-10-15 18:50 · T20 · 64b09ca

Ocho escenarios con DeepEval y juez Sonnet 5 real verificados: herramientas 1,00 en todos; fuente/no aprobación ≥0,90. Seis pasan en ronda completa y dos expectativas de herramienta corregidas pasan en repetición seleccionada. Fuente de respaldo incorporada a la respuesta persistida. Scorecard en [[chatbot-desplegado]]. Marker eval excluido por defecto; telemetría desactivada.

### 2026-10-15 18:02 · T19 · 03d99f0

Phoenix 12.35 local verificado en Chrome: proyecto ca-chat, una traza chat.turn y dos bedrock.converse hijos confirmados por API del colector. Trace ID 07ede8f4a30670148475cb21d5bf3d22, leer_caso OK, latencia 17,8 s. Sin endpoint queda inerte; exportador caído no rompe respuesta. Tres pruebas offline pasan. Instalación aislada con restricciones de dependencias documentada en [[chatbot-desplegado]].

### 2026-10-15 17:56 · T18 · 25140a2

Rutas HTTP v2 con validación, ámbito por RUN y consentimiento explícito. Pruebas sintéticas: 400/403/404, aceptación antes de permiso, revocación al declinar y ocultación de errores internos. x-run es ámbito de integración demo, no identidad ciudadana verificada. [[chatbot-desplegado]].

### 2026-10-15 17:55 · T17 · c7599d7

Turnos guardados en DynamoDB con leer_caso como única herramienta y evaluación determinista separada del contrato compartido. Tres pruebas offline demuestran continuidad de dos turnos, denegación de evaluación sin permiso y persistencia al agotar iteraciones. [[chatbot-desplegado]].

### 2026-10-15 17:55 · T16 · 65224cf

Repositorio DynamoDB con mensajes append-only, GSI por RUN y paginación. Dos pruebas moto verifican Case completo, consentimiento/revocación, orden estable, DV y caso ausente. [[chatbot-desplegado]].

### 2026-10-15 17:53 · T15 · f9e7f6d

Stack ChileAtiendeChat desplegado: health 200 con Converse real, 401 sin key y 403 con key inválida. Bundle Linux y síntesis OK; 177 tests y verificador TODO OK. [[chatbot-desplegado]].
