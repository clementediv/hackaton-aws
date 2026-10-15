---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0017 · Conversación natural y voz en los chats

## Contexto
El usuario reportó respuestas repetidas ante insultos y mensajes ambiguos, y pidió
micrófono y una voz sintética que leyera las respuestas. [[0015-orientacion-general-sin-perfil]].

## Decisión
Agregar instrucciones de conversación a los adaptadores públicos y personales,
sin cambiar las reglas ni el agente compartido. La conversación general de Mi Gobierno
conserva un historial propio, separado del personal y reiniciado al cambiar permisos.
No se copian saludos con datos personales a ese historial: solo turnos del modo público
Bedrock. El respaldo distingue frustración, ruido, insultos y preguntas sustantivas.

Usar Web Speech del navegador en un componente Streamlit: dictado es-CL, revisión
editable, envío explícito y protección contra reenvío al rerender. La voz utiliza
speechSynthesis, prefiere español, permite escuchar/detener y ofrece lectura automática
optativa. Al iniciar dictado se cancela la voz; al revocar permisos se desactiva lectura.
Los controles aparecen en Mi Gobierno y en el chat público.

## Consecuencias
No hace falta configurar Amazon Transcribe ni Polly para esta demo local. La app
recibe solo el texto enviado, sin guardar audio; el motor de dictado del navegador
puede utilizar un servicio remoto. Compatibilidad, permiso de micrófono, voces
instaladas y políticas de reproducción dependen del navegador. Si falla, se conserva
la escritura. La voz omite URLs largas y formato Markdown, manteniendo el texto visible.
La lectura no cambia el consentimiento para consultar datos ni afirma aprobaciones.

Referencias: [SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition),
[SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis),
[cancel](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/cancel).
