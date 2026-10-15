---
tipo: bitacora-integrante
integrante: Jp
---
# Bitácora de Jp

Una entrada por avance o commit relevante, la más reciente arriba.

Formato: `### AAAA-MM-DD HH:MM · <tema> · <commit corto>` y debajo qué se hizo, qué falta y si algo bloquea a otro integrante.


- 15-10: `/chat` comparte la temática del banner IA del inicio: fondo #f4f8fc, franja azul/roja, título azul, respuestas blancas con borde azul y campo blanco con envío azul. Se conserva conversación y reinicio. Verificación: 6 pruebas de portal/chat pasan; `git diff --check` sin errores nuevos.

- 15-10: Corregido centrado real de `/chat` limitando los anchos internos de Streamlit. Agregada pestaña «Asistente de IA» junto a «Mi Gobierno», presente también en el chat. Chromium confirma ejes de título/campo en 720 px (1440) y 195 px (390), sin desborde, y navegación Inicio → chat → Mi Gobierno.

- 15-10: Título del asistente movido encima de las pestañas de navegación en `/chat`, visible también durante la conversación. Reducido espacio vacío de bienvenida.

- 15-10: Chat con composición editorial inspirada en america.gov (la URL /chat redirige al inicio), bienvenida serif, consulta central y sugerencias funcionales. Fondo blanco; se conserva el mismo header, buscador y pestañas del inicio sin desplazar su posición. Chromium verifica escritorio/móvil, consulta centrada, envío, respuesta y reinicio. Seis pruebas del portal/chat pasan.

- 15-10: Saludo del chat en Roboto, bloque de conversación más arriba y texto del campo centrado verticalmente. Chromium confirma coincidencia exacta del eje vertical del texto y del campo a 1440/390 px, sin desborde.

- 15-10: Unificado eje horizontal del encabezado de conversación, saludo, entrada y aviso inferior; placeholder centrado con padding simétrico. Chromium confirma ejes 720/195 px en viewport 1440/390.

- 15-10: Chat público con salida progresiva mediante `st.write_stream`: Bedrock ConverseStream entrega deltas reales; modo plantilla muestra palabras progresivamente. Se guardan respuestas completas en historial, se conserva respuesta parcial si se corta el stream y se informa la interrupción. Falla previa al primer fragmento usa plantilla. 21 pruebas enfocadas pasan; Chromium observa longitudes crecientes 8 → 64 → 100 → 142 → 176 → 222 → 224 y reinicio correcto. API consultada: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse_stream.html. Sin llamada real a AWS en validación.

- 15-10: Ampliadas animaciones compartidas en `assets/motion.css`: entradas breves en portada, identidad, beneficios y portal ejecutivo; etapas y estadísticas escalonadas; feedback de botones, campos y documentos; apertura de paneles y diálogos. Movimiento reducido desactiva animaciones y transiciones dentro de la app. Verificación: 15 pruebas de portal, chat, app, Mi Gobierno y ejecutivos pasan. Sin verificación visual en navegador en esta revisión.

- 15-10: Reducida velocidad del texto progresivo a pausas de 80 ms en plantilla y en fragmentos de Bedrock. Cuatro pruebas de streaming/UI pasan.

- 15-10: El chat público reconoce identidad/capacidades y se presenta como asistente IA de ChileAtiende: guía de trámites, requisitos y documentos faltantes. Indica consentimiento en Mi Gobierno para revisión preliminar de PGU y decisión final del organismo. Instrucciones Bedrock coherentes con las plantillas. 23 pruebas enfocadas pasan. Ver [[portal-ayuda-tramites]].

- 15-10: Integrados avances remotos de conversación, voz y acceso ejecutivo con el diseño/streaming local. Consulta personal PGU revisa reglas, antecedentes faltantes y progreso guardado; sin sesión/permiso solicita ingreso y consentimiento en Mi Gobierno, con acceso a completar antecedentes. Historial personal separado del modelo público y eliminado al cambiar sesión o consentimiento. Suite completa: 260 pruebas pasan, 2 omitidas por dependencias opcionales y 8 evals excluidas; pruebas adicionales de privacidad y pasos PGU pasan. Ver [[portal-ayuda-tramites]].

- 15-10: Chat público sin botones de preguntas frecuentes. El placeholder alterna ejemplos con escritura y borrado letra a letra; se pausa al enfocar o escribir y usa texto fijo con movimiento reducido. Controlador local `assets/chat-placeholder.html`, sin cambiar el valor del campo.

- 15-10: Control de dictado más discreto: botón de ícono con tooltip, etiqueta accesible y ayuda desplegable «Cómo usar el micrófono». Durante el dictado se muestra «Detener dictado». Se conserva revisión antes del envío.

- 15-10: Micrófono compacto junto a enviar en el campo del chat público, sin botón de texto ni interruptor separado. Dictado conserva revisión y descarte; modo estándar de Mi Gobierno conserva lectura optativa. Chromium verifica posición 1440/390 y dictado simulado → revisión → descarte. Siete pruebas de chat/voz pasan.

- 15-10: Banner del asistente adaptado al chat actual: fondo blanco, Roboto, texto introductorio, respuesta con avatar, consulta redondeada y envío con icono. Conserva ejemplos animados con aparición progresiva de palabras y alternativa sin movimiento. Cinco pruebas del portal pasan; Chromium verifica 1440/390 sin desborde y centrado del campo.
