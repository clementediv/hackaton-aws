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

## Respuesta estándar de orientación · 15-10

Por instrucción del usuario, el cortafuegos usa BOUNDARY_REPLY, un texto único,
educado y orientativo que explica beneficios/trámites, requisitos, documentos,
próximos pasos y consentimiento para revisar antecedentes. Se aplica antes de
Bedrock a insultos sin consulta, ruido reconocible y solicitudes ajenas al propósito,
en ambos chats y con o sin autorización. Se conserva la ayuda para consultas reales
aunque incluyan una grosería. El prompt solicita el mismo texto para otros casos
fuera de alcance reconocidos por el modelo.

Esta instrucción reemplaza la variación de respuestas del cortafuegos de
[[0017-conversacion-y-voz-del-navegador]]; la conversación legítima conserva su estilo
natural. 49 pruebas enfocadas verifican texto idéntico entre turnos y chats, ausencia
de llamadas al modelo para el cortafuegos y consultas legítimas sin bloqueo.

Las referencias del chat se presentan como «Si quieres saber más, puedes revisar…»,
con enlaces clicables, en respuestas del modelo y respaldos locales. Se conservan
las aclaraciones de información no verificada. El formato también se normaliza
si el modelo devuelve «Fuente» o «Fuente de orientación del MVP». 57 pruebas
enfocadas pasan, incluyendo preservación de enlaces y normalización idempotente.

## Desplazamiento y espera del chat · 15-10

Ambos chats muestran la pregunta antes de invocar al agente. Durante la espera,
la burbuja del asistente muestra tres puntos azules con desfase de animación en ola,
etiquetados para lectores de pantalla. Movimiento reducido deja los puntos estáticos.
Al enviar y recibir se desplazan los contenedores de conversación hasta el final;
la observación del layout se desconecta tras asentarse para permitir leer mensajes
anteriores. Dictado, preguntas rápidas y preguntas que vienen de portada comparten
el mismo recorrido. Se conservan el historial y las reglas de consentimiento.

Verificación reproducible sin AWS: `uv run --with playwright python scripts/verificar_chat_scroll.py`.
El script levanta una app aislada con respuesta demorada y comprueba envío inmediato,
puntos escalonados, retirada del indicador y scroll de envío/respuesta en ambos chats
a 390 y 1440 px, además de permitir desplazamiento manual posterior.

## Cómo retomar · cierre 15-10

Cambios del chatbot guardados en `main`: conversación, consentimiento, referencias
naturales, cortafuegos estándar, dictado revisable, voz opcional, desplazamiento y
espera animada. Último cambio funcional: `df392ec`; registro: `bb0dd37`.
Streamlit usa Bedrock real mediante el adaptador local; estas mejoras de interfaz
no suponen un nuevo despliegue de la API.

Desde la raíz del repo, si la app ya no está corriendo:

```sh
AWS_PROFILE=hackaton AWS_REGION=us-east-1 BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-5 uv run --group app streamlit run src/app/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

Mac: http://localhost:8501. Teléfono en la misma Wi-Fi: http://10.42.64.244:8501
al cierre de esta sesión. La IP puede cambiar: consultar `ipconfig getifaddr en0`.
El servidor debe estar ejecutándose en el Mac. El micrófono en el teléfono puede
requerir HTTPS; la verificación del reconocimiento con micrófono físico queda manual.
Si vencen las credenciales AWS, renovar la sesión del perfil `hackaton` antes de
probar el agente. No hay credenciales guardadas en estas notas.

Verificación de cierre: 256 pruebas pasan, dos omitidas por dependencias opcionales
y ocho evals excluidas; verificador de 500 perfiles TODO OK. Chromium validó ambos
chats a 390/1440 px. Pendientes de alcance mayor en [[board-jonmor]]: integrar UI
con la API desplegada y configurar Phoenix remoto si se habilita.

Cierre tras integrar trazabilidad del equipo (`9603cae`): 259 pruebas pasan,
dos omitidas y ocho evals excluidas; verificador TODO OK. Servidor reiniciado
con acceso Wi-Fi y comprobación HTTP de salud OK.
