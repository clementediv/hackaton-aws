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
