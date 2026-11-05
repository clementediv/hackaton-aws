---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0012 — Detener escalamiento al confirmar contacto

Clemente aclara que una persona ya contactada por email no debe recibir los siguientes canales. Sustituye la regla anterior de [0007-backend-embudo-simulado](0007-backend-embudo-simulado.md) de continuar mientras no iniciara trámite.

Solo escala `active` (sin respuesta confirmada). Responder/contestar o aceptar la invitación pasa a `contacted`, cancela `next_at` y deriva a acompañamiento. Enviar o abrir sin responder no basta; este criterio se explicitó al usuario al continuar. `started` sigue siendo un resultado aparte y puede registrarse después de `contacted`. Declinar detiene contacto y acompañamiento. No se concede autorización de datos al simular una respuesta.

Las respuestas simuladas conservan las probabilidades por canal, pero ahora producen contacto; un sorteo independiente del 65% ilustra inicio posterior, sin calibración ni garantía de meta. El caso compartido sincroniza aceptación, rechazo e inicio. Una respuesta `answered` histórica detiene futuros intentos; no se reescribe ni borra el historial previo.

Se distinguen personas detectadas, personas con intento por canal, número de intentos, contactos confirmados y trámite iniciado. En el ejemplo sin respuestas hay 92 detectados; 255 son tres llamadas a 85 personas. Los saltos por falta de datos y la cola presencial no son contacto efectivo.

La meta vigente indicada por el usuario es ≥75% al próximo paso válido dentro del plazo, distinta de contacto o inicio. La UI muestra ese KPI «Sin medir», mientras falta instrumentar paso/plazo/evidencia. Inicio/detectados es solo proxy; no se modifican resultados para alcanzar artificialmente la meta.

Guía, ejemplos y evidencia en [backend-embudo-contacto](../backend-embudo-contacto.md). Heatmap/área consumen únicamente pendientes activos sin contacto confirmado; la lógica espacial y la paleta se conservan.
