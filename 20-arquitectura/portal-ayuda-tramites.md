---
tipo: implementacion
fecha: 2026-10-14
responsable: codex
---
# Portal — Ayuda para tus trámites y chatbot

Decisión en [[0006-portal-ayuda-chatbot]]. El usuario solicitó una sección de ChileAtiende que reúna ayuda para trámites, la ruta del MVP y el agente conversacional.

## Referencia utilizada
Únicamente el [portal oficial ChileAtiende](https://www.chileatiende.gob.cl/). Se recuperó su HTML y CSS mediante `Invoke-WebRequest` el 14-10-2026; la herramienta web y Chrome headless recibían 403, pero la petición HTTP directa sí devolvió el sitio. No se usaron portales alternativos como referencia visual.

Estructura observada: logo/encabezado, Red de atención, Mi ChileAtiende, buscador `buscar?query=`, destacados, Lo más buscado, momentos de vida, servicios por temas y contacto institucional. Se reutiliza el [SVG oficial](https://www.chileatiende.gob.cl/bulma/images/logo-cha.svg) en `src/app/assets/`, incluido como package data. Azules observados en el CSS oficial: `#0f69b4`, `#0d4d82`. No se copian noticias ni condiciones de beneficios al MVP.

## Comportamiento
- **Inicio**: destacados de la demo, acceso a Mi ChileAtiende, servicios/momentos de vida y enlaces oficiales.
- **Ayuda para tus trámites** (pestaña inicial): explicación del acompañamiento, invitación/autorización, ruta existente y chatbot al lado. El chat aparece desde la invitación; sin permiso permite orientación general sin consultar perfil ni reenviar historial personal.
- **Mi ruta**: retoma el mismo caso SQLite, con antecedentes, checklist, permisos e historial. Cambiar pestaña no crea otro caso.
- Buscador: selección local de accesos verificados y botón que continúa en el buscador oficial. No afirmar que el catálogo reducido contiene todos los trámites.
- Vistas ejecutivo/campañas/medición y selección de persona/canal siguen en controles de demostración, en la barra lateral colapsada.

## Chatbot y límite del MVP
`src/app/ruta/asistente.py` conserva las plantillas y delega Bedrock a `chatbot.answer`. Este usa `BedrockClient.from_env()` (modelo/credenciales configurables y allowlist), `Agent` y un handler `leer_caso` con el contexto calculado por el motor de la app. El modelo recibe estado, ruta y fuente; no aporta RUN, permiso ni resultados inventados. El permiso viene del flujo real de la app antes de crear el cliente para la ruta personal. Las fuentes del prototipo mantienen su marca de no verificadas.

El modo Bedrock se activa con `BEDROCK_MODEL_ID` del proceso, como en el aporte de Johann; una vez activo, el cliente común también lee `.env`. Sin configuración o ante error sigue funcionando por plantillas. No se verificó una inferencia real en este cambio: el tool use se probó con un cliente falso.

La **ruta personalizada** sigue cubriendo jubilación y PGU. Los accesos generales remiten al portal oficial y no generan evaluaciones o plazos para beneficios no implementados. El layout reproduce la organización del portal y añade la sección solicitada; no es una copia exacta de todos sus componentes/funcionalidades.

## Verificación
`uv run --group app pytest`: **64 tests pasan**. Pruebas nuevas: navegación Inicio/Ayuda/Mi ruta, búsqueda, permisos del chatbot y ejecución de `leer_caso` con el agente compartido. Se mantiene el test de aceptar/autorizar/preguntar/revocar y el script `src/app/verificar.py` sigue con TODO OK sobre 500 perfiles.

Ruff check/format OK en los módulos y test nuevos (`portal.py`, `chatbot.py`, `test_portal.py`); el lint histórico completo de la app sigue pendiente. Chrome headless mostró el layout en 1440 px y 390 px; en móvil el ancho de contenido coincide con el viewport, sin desbordamiento horizontal. No se modifican reglas normativas ni el dataset.

Ejecutar: `uv run --group app streamlit run src/app/app.py --server.address localhost`. Preview local: `http://localhost:8501`.

- 15-10: banner con chat de texto visible sin bot?n previo; t?tulo ?Prueba nuestro asistente de inteligencia artificial? e invitaci?n a preguntas frecuentes. Rotaci?n detenida al mostrar el chat; consulta contin?a en Ayuda. Cuatro pruebas del portal y verificador de 500 perfiles OK. [[portal-ayuda-tramites]].

- 15-10: Banner del asistente con t?tulo principal ?Prueba el asistente de inteligencia artificial?, dise?o neutro centrado, campo de texto redondeado, env?o con flecha y preguntas frecuentes como sugerencias. Cuatro pruebas del portal OK. [[portal-ayuda-tramites]].


## Consultas generales sin repetir el diagnóstico · 15-10

Según [[0015-orientacion-general-sin-perfil]], la definición de PGU/AFP/RSH/SCOMP
se atiende antes de pedir autorización de antecedentes. Con Bedrock configurado,
answer_general envía solo la pregunta actual y hechos públicos con fuentes; no
recibe perfil ni historial. El respaldo explica el tema solicitado. Consultas
personales piden consentimiento; las desconocidas piden aclaración sin repetir fechas.

Verificación: 22 pruebas enfocadas pasan. Llamada real a Sonnet 5 a «¿Qué es la PGU?»
sin autorización devolvió una definición con fuente ChileAtiende y sin nombre ni
fechas personales. Fuente pública consultada: https://www.chileatiende.gob.cl/fichas/102077.
- 15-10: Animaciones suaves de entrada para tarjetas, etapas y chat; transiciones de botones, foco del campo y tarjetas de portada. Movimiento reducido desactiva efectos. Chromium verifica escritorio/movil, limites de tarjetas y prefers-reduced-motion. Retiradas las sugerencias bajo el chat del banner; campo y envio conservados. [[portal-ayuda-tramites]].

- 15-10: Slides del banner cada 2,5 segundos: ciclo CSS completo de 5 segundos para dos paneles. Duracion comprobada en Chromium. [[portal-ayuda-tramites]].

- 15-10: Banner inicia con asistente IA y cambia de slide cada 8 segundos (ciclo de 16 segundos). Orden HTML actualizado tambien para movimiento reducido. Chromium confirma estado inicial y duracion. [[portal-ayuda-tramites]].

- 15-10: Chat publico con bienvenida centrada, encabezado compacto, mensajes de persona a la derecha y entrada fija redondeada; CSS separado y responsive. Reinicio local elimina importacion obsoleta de responder_publico. Prueba de UI de respuesta y nueva conversacion OK; Chromium verifica envio y anchos 1440/390 sin desborde. Referencia america.gov/chat no accesible desde navegador de consulta. [[portal-ayuda-tramites]].
Integración: el chat público separado en /chat usa también el cliente compartido,
sin temperature. Conserva solo su propio historial público. 23 pruebas enfocadas
pasan tras integrar el aporte; el historial personal revocado nunca se reenvía.

### Elegibilidad personal en Mi Gobierno

«puedo tener yo la pgu?» ahora se reconoce como consulta personal, al igual que
«tengo derecho», «podría solicitarla» y «me corresponde». Sin consentimiento se
indica marcar la casilla y pulsar Activar Mi Gobierno, sin afirmar elegibilidad.
Con permiso la pregunta se envía al agente con la evaluación determinista existente.
Las consultas generales con Bedrock ya no dependen de una lista cerrada de frases;
solo se envía la pregunta actual, sin perfil ni historial personal revocado.
Verificación: 31 pruebas enfocadas pasan y script 500 perfiles TODO OK.
- 15-10: Pulido del chat publico: textarea contenido dentro del borde y sin padding que recorta lineas; burbuja de persona con altura suficiente para todo el texto. Chromium verifica banner, dos turnos, enlaces de fuentes y nueva conversacion a 390/900/1440 px. Cinco pruebas enfocadas OK. [[portal-ayuda-tramites]].

- 15-10: `/chat` comparte la temática del banner IA del inicio: fondo #f4f8fc, franja azul/roja, título azul, respuestas blancas con borde azul y campo blanco con envío azul. Se conserva conversación y reinicio. Verificación: 6 pruebas de portal/chat pasan; `git diff --check` sin errores nuevos.

- 15-10: Corregido centrado real de `/chat` limitando los anchos internos de Streamlit. Agregada pestaña «Asistente de IA» junto a «Mi Gobierno», presente también en el chat. Chromium confirma ejes de título/campo en 720 px (1440) y 195 px (390), sin desborde, y navegación Inicio → chat → Mi Gobierno.

- 15-10: Título del asistente movido encima de las pestañas de navegación en `/chat`, visible también durante la conversación. Reducido espacio vacío de bienvenida.

- 15-10: Chat con composición editorial inspirada en america.gov (la URL /chat redirige al inicio), bienvenida serif, consulta central y sugerencias funcionales. Fondo blanco; se conserva el mismo header, buscador y pestañas del inicio sin desplazar su posición. Chromium verifica escritorio/móvil, consulta centrada, envío, respuesta y reinicio. Seis pruebas del portal/chat pasan.

- 15-10: Saludo del chat en Roboto, bloque de conversación más arriba y texto del campo centrado verticalmente. Chromium confirma coincidencia exacta del eje vertical del texto y del campo a 1440/390 px, sin desborde.

- 15-10: Unificado eje horizontal del encabezado de conversación, saludo, entrada y aviso inferior; placeholder centrado con padding simétrico. Chromium confirma ejes 720/195 px en viewport 1440/390.

- 15-10: Chat público con salida progresiva mediante `st.write_stream`: Bedrock ConverseStream entrega deltas reales; modo plantilla muestra palabras progresivamente. Se guardan respuestas completas en historial, se conserva respuesta parcial si se corta el stream y se informa la interrupción. Falla previa al primer fragmento usa plantilla. 21 pruebas enfocadas pasan; Chromium observa longitudes crecientes 8 → 64 → 100 → 142 → 176 → 222 → 224 y reinicio correcto. API consultada: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse_stream.html. Sin llamada real a AWS en validación.

- 15-10: Ampliadas animaciones compartidas en `assets/motion.css`: entradas breves en portada, identidad, beneficios y portal ejecutivo; etapas y estadísticas escalonadas; feedback de botones, campos y documentos; apertura de paneles y diálogos. Movimiento reducido desactiva animaciones y transiciones dentro de la app. Verificación: 15 pruebas de portal, chat, app, Mi Gobierno y ejecutivos pasan. Sin verificación visual en navegador en esta revisión.

## Conversación y voz · 15-10

[[0017-conversacion-y-voz-del-navegador]] agrega estilo conversacional en ambos
adaptadores. No se repite un menú ante frustración o mensajes ambiguos; se pide
una aclaración breve y se responde la pregunta real aunque incluya una grosería.
Mi Gobierno conserva solo turnos públicos en un historial separado cuando no hay
permiso; al cambiar el consentimiento se reinicia ese historial y la lectura en voz alta.

- **Hablar por micrófono**: solicita permiso del navegador, permite dictar, editar,
  descartar y pulsar Enviar mensaje. No envía automáticamente lo reconocido.
- **Leer respuestas en voz alta**: desactivado inicialmente; lee respuestas nuevas
  con voz española. Escuchar respuesta reproduce a pedido y Detener voz cancela.
  Dictar detiene la lectura para evitar que el asistente se escuche a sí mismo.
- Si el navegador no admite dictado o niega el permiso, se indica cómo continuar
  escribiendo. Las voces y el servicio de reconocimiento dependen del navegador.

Verificación: 43 pruebas enfocadas pasan. Tres turnos reales con Sonnet 5 ante
insulto, texto sin sentido y frustración produjeron respuestas distintas y pertinentes.
El script `uv run --with playwright python scripts/verificar_dictado.py` verifica
revisión, edición, envío único, errores de permiso, descarte, compatibilidad,
lectura optativa en español, no reproducción repetida y pausa al dictar con motores
simulados en Chromium. El micrófono físico y el sonido audible requieren prueba
manual en el dispositivo. Capturas locales en /tmp/chat-voice-review.png y
/tmp/chat-voice-app.png. App disponible en http://localhost:8501.

Prueba de interfaz completa: una transcripción simulada se envió una sola vez
mediante el componente Streamlit y recibió respuesta real de Bedrock. Prueba
adicional de Mi Gobierno verifica reinicio de memoria general y lectura al revocar.

Integración final con portal ejecutivo: 235 pruebas correctas, dos omitidas por
dependencias opcionales y ocho evals excluidas. Verificador 500 perfiles TODO OK.
Los cinco fallos históricos de UI quedaron resueltos por el aporte remoto.

Tras la última integración de acceso ejecutivo: 235 pruebas pasan, dos omitidas,
ocho evals excluidas y verificador TODO OK. Chromium vuelve a confirmar el flujo
de dictado simulado → envío único → respuesta real de Bedrock, junto con los controles
de lectura.

- 15-10: Integrados avances remotos de conversación, voz y acceso ejecutivo con el diseño/streaming local. Consulta personal PGU revisa reglas, antecedentes faltantes y progreso guardado; sin sesión/permiso solicita ingreso y consentimiento en Mi Gobierno, con acceso a completar antecedentes. Historial personal separado del modelo público y eliminado al cambiar sesión o consentimiento. Suite completa: 260 pruebas pasan, 2 omitidas por dependencias opcionales y 8 evals excluidas; pruebas adicionales de privacidad y pasos PGU pasan. Ver [[portal-ayuda-tramites]].

- 15-10: Chat público sin botones de preguntas frecuentes. El placeholder alterna ejemplos con escritura y borrado letra a letra; se pausa al enfocar o escribir y usa texto fijo con movimiento reducido. Controlador local `assets/chat-placeholder.html`, sin cambiar el valor del campo.

- 15-10: Control de dictado más discreto: botón de ícono con tooltip, etiqueta accesible y ayuda desplegable «Cómo usar el micrófono». Durante el dictado se muestra «Detener dictado». Se conserva revisión antes del envío.
