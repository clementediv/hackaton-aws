---
tipo: bitacora-integrante
integrante: Clemente
---
# Bitácora de Clemente

Una entrada por avance o commit relevante, la más reciente arriba. Así se puede seguir el historial de cada tarea sin leer todo `git log`.

Formato: `### AAAA-MM-DD HH:MM · T<nn> · <commit corto>` y debajo qué se hizo, qué falta y si algo bloquea a otro integrante.

### 2026-10-15 · Trazabilidad visual de uso · `96abb06`, integración `fb6eea5`
- Cuatro hitos visuales, continuidad diaria, regreso en ventanas completas de 7/30 días y recorrido individual con sesiones/último acceso/vista/intervalos. Auditoría y AWS opcional conservados en desplegable.
- Mi Gobierno registra accesos identificados, vistas tras autorizar y avance declarado disponible; no cuenta recargas, aperturas de correo ni `started` como conversiones. Escenario ficticio solo en base aislada. Sin reintroducir cobro ni afirmar KPI ≥75% cumplido.
- Cierre integrado: 260 pruebas OK, una omitida por trazas opcionales y ocho evals excluidas; verificador de 500 perfiles TODO OK. Chrome 1440/390 sin errores/desborde, gráficos y recorrido individual verificados. Localhost 8505 activo. Diseño y límites en [[trazabilidad-casos]], [[0018-trazabilidad-de-uso]].

### 2026-10-15 · Acotar Mi Gobierno al MVP · commit «Retirar botón de cobro del MVP de Mi Gobierno»
- Retirado «Cobrar beneficio» de la tarjeta PGU elegible, por solicitud de Clemente. Situación, requisitos, calendario y chat conservados; los estados que requieren preparación/antecedentes mantienen sus acciones.
- Prueba de sesión/consentimiento/documentos/revocación actualizada para verificar ausencia del botón y ausencia de pasos completados automáticamente. 24 pruebas de UI/integración y verificador de 500 perfiles OK; localhost 8505 actualizado. [[mi-gobierno]].

### 2026-10-15 · Acceso ficticio de ejecutivos · commit «Agregar acceso ficticio para ejecutivos y asistentes sociales»
- Implementación `dc0e849`. Cierre: 225 pruebas OK, una omitida por dependencia opcional de trazas y ocho evals Bedrock excluidas; lint de archivos cambiados y verificador de 500 perfiles OK. Localhost 8505 actualizado.
- Login con correo y clave para ejecutiva/asistente social ficticios; credenciales visibles en la pantalla para la demo. Misma línea visual del acceso ciudadano. Sesión propia, sin alterar consentimiento ni historial de Mi Gobierno.
- Guardia común antes de leer campañas y herramientas laterales; salida limpia identidad, campos y filtros del ejecutivo sin borrar los casos. Error de credenciales limpia el formulario.
- Pruebas de validación, acceso directo, mapa tras ingresar, salida y aislamiento de sesión ciudadana. Actualizadas pruebas de ficha/Contactos AWS para ingresar primero. Chromium verifica error, ingreso, heatmap, salida y móvil sin desborde; verificador de 500 perfiles TODO OK. [[portal-ejecutivos]].

### 2026-10-15 · Portal para ejecutivos · `81755d7`, integración `710df25`
- Página nueva con estética del frontend: estados claros, búsqueda/filtros e historial con próximo paso; lectura del mismo snapshot sin cruzar antecedentes privados de otra base.
- Campañas RM con paleta existente y propuesta automática según cantidad de personal. Radios discretos, capacidad de demo explícita, mínimo cinco casos y GeoJSON sin identificadores. Laboratorio técnico conservado.
- Demo aislada persistente y selector para el embudo de la aplicación, sin llamadas ni envíos AWS. KPI ≥75% permanece pendiente de instrumentación; no se equipara contacto/inicio con avance válido en plazo. [[portal-ejecutivos]], [[0016-portal-ejecutivos]].
- Pruebas nuevas de planificación, privacidad, persistencia, filtros, navegación y mapa; verificador de 500 perfiles y recorrido Chromium de escritorio/móvil. Pruebas antiguas adaptadas a las pestañas y chat vigentes.
- Merge conserva chat público independiente, estilos dinámicos y todos los registros remotos; ADR renumerado a 0016 para conservar el 0015 de orientación general. La revisión detectó lectura del dataset sin UTF-8 en la API sobre Windows y un test de evaluación sin invitación aceptada; corregidos sin cambiar permisos. Cambios locales previos y archivos personales preservados.
- Cierre: 224 pruebas OK, una omitida por dependencia opcional de trazas y ocho evals Bedrock excluidas; verificador de 500 perfiles TODO OK. Chrome a 1440/390 px sin errores JavaScript; localhost 8505 activo. Corrección Windows y registro de integración: `e9c9d57`.

### 2026-10-15 · Merge de aportes locales y remotos · `9626cac`
- Actualización `1932574`: el remoto avanzó con ayuda audiovisual y documentos por requisito (`947bacc`). Integrado también; único conflicto en la bitácora resuelto conservando ambas entradas. Repetición completa: 174 tests y verificador TODO OK. El laboratorio versionado también inicia y avanza correctamente, independientemente del cambio local sin commit.
- Integrados los tres commits locales de despliegue/email proactivo con once commits remotos (Mi Gobierno, acceso demo, beneficios e investigación). Merge sin conflictos de texto; cambios locales previos sin commit preservados, incluido `demo_embudo.py`.
- 174 pruebas completas, incluida la suite proactiva con Moto, y verificador de 500 perfiles TODO OK. Revisados consentimiento separado del acceso demo, catálogo educativo sin elegibilidad inventada y detención de contactos proactivos al responder.
- Integración pendiente registrada: aceptación SQLite de Mi Gobierno y contactos DynamoDB proactivos aún no se sincronizan. No se ejecutó deploy ni envío real como parte de esta revisión.

### 2026-10-15 · Conversación y presentación del asistente (Codex)
- Corregida la repetición del resumen ante «hola»: saludos/agradecimientos con respuesta breve y preguntas no reconocidas solicitan aclaración. Mi Gobierno inicia con bienvenida breve y distingue mensajes de persona (burbuja gris a la derecha) y asistente (fondo blanco); conserva campo debajo e historial.
- Siete regresiones nuevas (saludos con/sin autorización y consulta no reconocida). 153 pruebas pasan excluyendo la suite proactiva no versionada, verificador de 500 perfiles OK. Chrome 1440/390 px valida saludo sin duplicación de diagnóstico y sin desbordamiento. [[mi-gobierno]]. Commit «Mejorar la conversación y presentación del asistente».

### 2026-10-15 · Campo debajo de una conversación más corta (Codex)
- Corrección solicitada: entrada debajo del historial; altura del chat en Mi Gobierno de 420 a 240 px para evitar espacio vacío. Retirado el aviso del 101/sucursal del asistente compartido. Verificador de 500 perfiles OK. [[mi-gobierno]]. Commit «Acercar la entrada al chat y retirar aviso de atención».
- 146 pruebas pasan (`pytest tests --ignore=tests/test_proactivo.py`); se excluye únicamente la suite nueva no versionada del aporte proactivo, ajeno a este cambio.

### 2026-10-15 · Campo de consulta arriba (Codex)
- El campo para preguntar queda debajo del título y la descripción del asistente de Mi Gobierno, antes del historial, tanto en Beneficios como en la guía PGU. Se conserva el envío y registro de preguntas. Verificador de 500 perfiles OK. [[mi-gobierno]]. Commit «Subir el campo de consulta del asistente».
- Cuatro pruebas de UI afectadas OK. Suite completa: 163 pasan y una falla en el orden de eventos de `tests/test_proactivo.py::test_no_answer_escalates_email_sms_field` (archivo nuevo no versionado de otro aporte); no se modifica ese módulo.

### 2026-10-15 · Sin preguntas frecuentes en Mi Gobierno (Codex)
- Por solicitud del usuario se retiró el desplegable del asistente en Beneficios y guía PGU; quedan la conversación y el campo para escribir. Cuatro pruebas de UI/integración OK. [[mi-gobierno]]. Commit «Quitar preguntas frecuentes de Mi Gobierno».

### 2026-10-15 · Asistente de Mi Gobierno (Codex)
- Panel ampliado al 40% del espacio entre columnas, conversación de 420 px antes de las sugerencias, preguntas frecuentes desplegables con botones en una columna. Beneficios y guía PGU comparten presentación; hasta 1050 px se apila a todo el ancho.
- Chrome 1440/900/390 px sin desbordamiento horizontal; pregunta rápida y acceso a guía OK. 146 pruebas y verificador de 500 perfiles OK. [[mi-gobierno]]. Commit «Ordenar y ampliar el asistente de Mi Gobierno».

### 2026-10-15 · Vista ejecutivo unificada (Codex)
- Una única entrada principal «Vista ejecutivo» reúne mapa/campañas, detección/invitaciones, ficha, atención del caso y medición mediante selector interno. Se reutilizan las vistas existentes y solo se ejecuta la elegida.
- Actualizados los recorridos de UI para acceder a la ficha y recorrer las cinco herramientas; 146 pruebas y verificador de 500 perfiles OK. [[ficha-beneficiario]]. Commit «Unificar herramientas de gestión en Vista ejecutivo».

### 2026-10-15 · Ficha del beneficiario y fuente única de contacto (Claude)
- Mi Gobierno armaba email y teléfono por su cuenta y no coincidía con el colador. Ahora todo lee `ruta.ficha.contact_for`: el contacto del colador si la persona está en la campaña y, si no, la capa sintética. Si falta un canal, se muestra «Sin información».
- Formato legible y ficticio en la capa: `nombre.apellido@example.com` y `+56 9 0000 xxxx`; se mantienen la semilla y los canales vacíos. Se regeneró `data/synthetic/contacto.csv`.
- Nueva vista «Ficha del beneficiario»: alerta, identidad, contacto, consentimiento, evaluación, ruta, documentos (solo con autorización), colador e historial. 145 pruebas y verificador OK. [[ficha-beneficiario]]

### 2026-10-15 · Board: seguimiento por etapa y entrega de emails
- A pedido de Clemente, agregado el flujo completo sin respuesta: email 7 días → hasta tres llamadas en cinco días → trabajo 7 días → cola presencial; saltos por falta de datos y salida al responder/aceptar o declinar.
- Registrados como pendientes los estados reales de entrega/rebote/apertura/respuesta y la política ante rebotes. Se distingue seguimiento de contacto de acompañamiento del trámite; la demo no confirma entregas reales. [[board-clemente]] · [[0012-detener-contacto-confirmado]].

### 2026-10-15 · Detener al confirmar contacto · `0642159`
- Clemente corrige el criterio: responder/aceptar detiene los siguientes canales, sin esperar inicio. Nuevo estado contacted; iniciar/declinar después sigue permitido. Enviar/abrir sin respuesta no confirma. Sin autorizaciones automáticas ni reescritura de historial; respuestas antiguas cancelan futuros intentos.
- Aclaración: 92 personas detectadas, 255 intentos de llamada a 85 personas en la demo sin respuestas. UI diferencia personas/intentados/saltos/respuestas/estados. Ejemplo con respuestas: 66 contactos confirmados (34 inicios, 23 contactados sin inicio, 9 rechazos) y 26 pendientes; todos sintéticos.
- KPI próximo paso válido en plazo, meta actual usuario ≥75%, aparece Sin medir; inicio es solo proxy. Instrumentación pendiente en board. Dos ejemplos locales conservados. AGENTS/diseño/pipeline actualizados para ambos agentes.
- 136 tests (10 nuevos) y ruff/format OK; verificador de 500 perfiles TODO OK. Chrome sin excepciones muestra métricas y gráfico corregidos. [[0012-detener-contacto-confirmado]] · [[backend-embudo-contacto]].

### 2026-10-15 · Área de campaña según concentración · `66dbea8`
- Área automática desde las mismas ubicaciones del heatmap: máxima cobertura para radio fijo, contorno amarillo, capacidad/jornadas y descargas JSON/GeoJSON. Radio UI 500–3000 m; cola presencial exclusivamente. Conserva fondo/paleta y ranking comunal.
- Escenario actual: radio 1,5 km cubre 10/84 casos (11,9%) en San Bernardo; dos funcionarios × ocho atenciones/día → una jornada. Propuesta geométrica aproximada, sin sede habilitada, agenda ni despacho.
- 126 tests pasan (13 nuevos), ruff/format y verificador de 500 perfiles OK. Chrome muestra contorno/etiqueta sin excepciones. [[0011-area-campana-segun-heatmap]] · [[heatmap-campanas-simulado]].

### 2026-10-15 · Direcciones individuales simuladas · `643a888`
- A pedido del usuario: calor desde una ubicación ficticia por persona, con núcleos y dispersión dentro del polígono comunal. Misma paleta/fondo RM; desaparecen los círculos comunales ponderados. Puntos inspeccionables, etiquetas comunales opcionales y detalle Barrios/Sectores amplios.
- Dirección rotulada SIMULADA, coordenadas a seis decimales y procedencia sintética; no son domicilios RSH ni calles verificadas. Nuevos contactos persisten ubicación; snapshots anteriores se enriquecen determinísticamente sin reescribir casos. Umbral comunal de cinco conservado.
- 113 tests pasan (14 nuevos), ruff y verificador TODO OK. Chrome muestra calor y puntos con 84 ubicaciones para los 84 casos publicables, sin excepciones ni solicitudes de mapa fallidas. [[0010-direcciones-simuladas]] · [[heatmap-campanas-simulado]].

### 2026-10-15 · Rediseño metropolitano · `475100e`
- A pedido del usuario: solo Región Metropolitana, calles vectoriales oscuras CARTO/OSM, contornos de 52 comunas BCN, calor 2048, etiquetas exactas y colores fijos por conteo. Ocho comunas sintéticas en nuevas inicializaciones, sin alterar canales ni casos previos. Base independiente `funnel-demo-rm.db`.
- Ranking y propuesta por comuna; umbral mínimo de 5 ahora comunal. Escenario precargado sin respuestas: 92 casos, 84 publicables en seis comunas. Los restantes grupos se omiten, sin inventar personas ni domicilios. Fondo urbano requiere internet.
- 99 tests pasan (9 nuevos), ruff check/format OK y verificador de 500 perfiles TODO OK. Chrome comprobado a doble densidad en 1440/1024 px, sin excepciones; todos los focos y etiquetas entran en pantalla. [[heatmap-campanas-simulado]] · [[0009-heatmap-metropolitano]].

### 2026-10-15 · Heatmap y campañas simuladas · `b4d517f`
- Mapa para ejecutivos en laboratorio localhost:8502 y Detectar e invitar; cola presencial, diagnóstico de activos, filtro regional, ranking determinista y propuesta de jornadas por capacidad. Grupos menores de 5 se suprimen antes de frontend y exportación. No hay agenda ni despacho.
- RSH del evento sin comuna/provincia; usa seis territorios de la capa sintética. Contornos Natural Earth locales, sin solicitudes remotas de mapa verificadas en Chrome. No son domicilios ni centroides oficiales.
- 90 tests pasan, ruff OK y verificador de 500 perfiles TODO OK. [[heatmap-campanas-simulado]] · [[0008-heatmap-campanas-sinteticas]]. Siguen pendientes datos autorizados, campañas reales, alertas/CESFAM y acompañamiento.

### 2026-10-15 · Backend del embudo · `7d1d8e0`
- Revisados los pendientes actuales y [[contacto-y-campanas]]. Implementados contactos sintéticos, backend persistente con reloj, simulación reproducible y embudo visual. Escala solo si no inició trámite; declinar detiene todo. No hay envíos/calls/visitas reales.
- CLI `scripts/colador_backend.py`, laboratorio `src/app/demo_embudo.py` en localhost:8502 y componente compartido en Detectar e invitar. La demo usa una base separada y permite conservar escenarios.
- 84 tests pasan (20 nuevos), ruff de módulos nuevos OK y verificador de 500 perfiles TODO OK. Chrome muestra gráfico/tablas sin excepciones. Guía [[backend-embudo-contacto]] y [[0007-backend-embudo-simulado]].
- Quedan heatmap, alerta/CESFAM, envíos reales y acompañamiento ampliado, sin marcarlos como implementados.

### 2026-10-14 · T04 · rama `clemente/T04-agente`
- Agente con Converse + tool use: límite de iteraciones, formato común de errores, contexto del caso en el prompt e historial entre canales. Ruta y checklist deterministas. CLI `uv run agente --run <RUN>`. Guía en [[T04-agente]].
- 57 tests (11 nuevos) y ruff OK. Prueba real con Bedrock Sonnet 5 y el RUN `100000010-4`: consulta el perfil, cita el dataset y no adjudica la PGU.
- Falta: conectar T11 y T12 de Johann (se registran solas desde `src/rules`). Ajustar el prompt, porque sin `evaluar_pgu` el modelo igual explica requisitos de memoria.

### 2026-10-14 · T07 · merge de T03 y T05 a `main` (`36cd846`)
- Revisión (Claude): aprobadas. 46 tests, `ruff check` y `ruff format --check` OK. El DV módulo 11 es correcto, la autorización se valida antes de leer el archivo y no se puede consultar otro RUN que el del caso.
- Pendientes para T04, no bloqueantes:
  - `guardar_caso` no tiene parámetros: T04 debe definir qué guarda (ruta, checklist) y validarlo contra `RouteStep` y `ChecklistItem`.
  - El prompt no incluye el contexto dinámico del caso (estado de la autorización, canal, fecha de referencia): T04 lo inyecta en cada turno.
  - `normalize_run` rechaza un RUN sin guion (`1000000015`), que es habitual al escribirlo. Conviene aceptarlo.

### 2026-10-14 · T05 · rama `codex/T05`
- Prompt ejecutable y [[agente-pgu]]: orientación preliminar, fuentes, consentimiento registrado por la aplicación, conservación de estados y separación entre hitos/vencimientos.
- Especificaciones Converse para adaptadores del caso actual; solo se exponen handlers registrados. Casos/perfiles/fechas vienen del servidor, no del LLM. Los handlers de otros frentes siguen pendientes; no se anuncian como implementados.
- Suite: 46 tests pasan, ruff check y format OK. Lista para revisión/integración T07. Commit `T05: definir prompt PGU y especificaciones de herramientas` registra esta entrada.

### 2026-10-14 · T03 · `6ea8da0` (rama `codex/T03`)
- Consulta por RUN con/sin puntos, DV validado y retorno `Profile`; `None` si no existe. Permisos mediante `Case.can_read_profile` y coincidencia del RUN antes de leer el archivo.
- Dataset cargado una vez por repositorio y respuestas copiadas; conserva RSH ausente. Suite: 40 tests pasan, 19 nuevos. Guía [[T03-consultar-perfil]].
- Lista para revisión/integración T07. El commit usa `T03: consultar perfiles con autorización y RUN normalizado` y registra esta entrada.

### 2026-10-14 · T02 · rama `clemente/T02-contratos`
- Contratos compartidos en `src/contracts/` (perfil, evaluación PGU, hitos, caso con invitación, autorización, ruta, checklist y mensajes). Se agrega `pydantic` como dependencia.
- `uv run pytest`: 21 tests (10 nuevos); `ruff check` sin errores. Los 500 perfiles de `perfiles.json` cargan con `Profile.model_validate`.
- Desbloquea T03 (Codex), T11 y T12 (Johann), T15, T16 y T21 (Jonmor), y los mocks de Bruno. Guía en [[T02-contratos]].

### 2026-10-14 · T07 · merge de `codex/T01` a `main`
- Revisión de T01 (Claude): OK. `uv run pytest` 11 tests y `ruff check` sin errores en `main`.
- Nota para T32: `BedrockClient` no permite cambiar el modelo por llamada; el simulador con Haiku debe crear su propio cliente con `BedrockSettings(model_id="us.anthropic.claude-haiku-4-5")`.

### 2026-10-14 · T01 · `125f8f8`
- T01 implementada por Codex: configuración Python, estructura inicial y cliente Bedrock. `uv run pytest`: 11 tests pasan; ruff check y format OK. Documentación en [[T01-scaffold-python]].

- 15-10: banner con chat de texto visible sin bot?n previo; t?tulo ?Prueba nuestro asistente de inteligencia artificial? e invitaci?n a preguntas frecuentes. Rotaci?n detenida al mostrar el chat; consulta contin?a en Ayuda. Cuatro pruebas del portal y verificador de 500 perfiles OK. [[portal-ayuda-tramites]].

- 15-10: Banner del asistente con t?tulo principal ?Prueba el asistente de inteligencia artificial?, dise?o neutro centrado, campo de texto redondeado, env?o con flecha y preguntas frecuentes como sugerencias. Cuatro pruebas del portal OK. [[portal-ayuda-tramites]].

- 15-10: L?nea de tiempo compacta: menos padding, marcadores de 30 px y texto reducido; tarjetas con box-sizing border-box para contener su ancho. Chromium verific? el componente a 390/900/1440 px sin desborde. Test actualizado a st.html; tres pruebas pasan, prueba integral falla despu?s en expectativa de chat tras revocar (fuera del CSS). [[mi-gobierno]].

- 15-10: Corregido desborde real de etapas: stHtml recibia 875 px dentro de 833 px disponibles por el padding de la tarjeta. Se limita el bloque HTML al 100% del ancho interior. Chromium sobre Mi Gobierno completo confirma cuatro tarjetas contenidas a 1440, 900 y 390 px. [[mi-gobierno]].

- 15-10: Recuadros de requisitos: icono y bloque de texto centrados verticalmente, ancho con padding incluido y texto contenido. Chromium en Mi Gobierno completo confirma 16 recuadros alineados a 1440 y 390 px. [[mi-gobierno]].

- 15-10: Textos del resultado y requisitos centrados horizontalmente respecto de todo el recuadro, con padding simetrico e icono independiente a la izquierda. Chromium en pantalla real verifica 16 recuadros centrados y contenidos a 1440, 900 y 390 px. [[mi-gobierno]].

- 15-10: Animaciones suaves de entrada para tarjetas, etapas y chat; transiciones de botones, foco del campo y tarjetas de portada. Movimiento reducido desactiva efectos. Chromium verifica escritorio/movil, limites de tarjetas y prefers-reduced-motion. Retiradas las sugerencias bajo el chat del banner; campo y envio conservados. [[portal-ayuda-tramites]].

- 15-10: Slides del banner cada 2,5 segundos: ciclo CSS completo de 5 segundos para dos paneles. Duracion comprobada en Chromium. [[portal-ayuda-tramites]].

- 15-10: Banner inicia con asistente IA y cambia de slide cada 8 segundos (ciclo de 16 segundos). Orden HTML actualizado tambien para movimiento reducido. Chromium confirma estado inicial y duracion. [[portal-ayuda-tramites]].

- 15-10: Retirados encabezado introductorio y descripcion de acompanamiento encima del listado de beneficios, a solicitud del usuario. [[mi-gobierno]].

- 15-10: Chat publico con bienvenida centrada, encabezado compacto, mensajes de persona a la derecha y entrada fija redondeada; CSS separado y responsive. Reinicio local elimina importacion obsoleta de responder_publico. Prueba de UI de respuesta y nueva conversacion OK; Chromium verifica envio y anchos 1440/390 sin desborde. Referencia america.gov/chat no accesible desde navegador de consulta. [[portal-ayuda-tramites]].

- 15-10: Pulido del chat publico: textarea contenido dentro del borde y sin padding que recorta lineas; burbuja de persona con altura suficiente para todo el texto. Chromium verifica banner, dos turnos, enlaces de fuentes y nueva conversacion a 390/900/1440 px. Cinco pruebas enfocadas OK. [[portal-ayuda-tramites]].

- 15-10: Banner de beneficios reemplazado por pregunta sobre requisitos PGU, cuatro puntos ilustrativos de revision y checks secuenciales descendentes sincronizados con el ciclo de 16 segundos. CTA a revision personal en Mi Gobierno; no se afirma elegibilidad sin perfil. Chromium 1440/390 px y movimiento reducido OK; cinco pruebas del portal pasan. [[portal-ayuda-tramites]].

- 15-10: Ejemplo del banner PGU en afirmativo: requisitos cumplidos y beneficio listo para cobrar. Etiqueta ilustrativa visible sobre el titulo; revision personal y confirmacion IPS indicadas al pie. Checklist animado conservado. Cinco pruebas del portal OK. [[portal-ayuda-tramites]].

- 15-10: Retirados rotulo ilustrativo y nota inferior del banner PGU a pedido del usuario. Checklist con separacion de 1,1 s, entrada de 0,8 s y checks de 1,12 s. Indices definidos con nth-child en CSS porque el renderizador elimina atributos style del HTML. Chromium verifica retrasos y finalizacion; cinco pruebas del portal OK. [[portal-ayuda-tramites]].

- 15-10: PGU sin marco exterior: contenedor Streamlit sin borde y CSS sin fondo/padding exterior; se conserva un solo recuadro para etapas. Chromium confirma borde exterior 0 px, interior 1 px y sin desborde a 1440/390 px. [[mi-gobierno]].

- 15-10: Recuadro de etapas PGU mas amplio: borde azul de 2 px, padding 24 px en escritorio y 18 px en movil, titulo de 17 px. Marco exterior sigue retirado. Chromium verifica borde, padding y contencion a 1440/390 px. [[mi-gobierno]].

- 15-10: Corregida interpretacion del marco PGU: un borde visible de 2 px envuelve titulo, monto, etapas y desplegable de requisitos; la linea de tiempo queda sin borde ni fondo propio. Chromium confirma contencion completa y sin doble marco a 1440/390 px. [[mi-gobierno]].

- 15-10: FUAS, gratuidad y becas usan el mismo marco unico de PGU: borde exterior de 2 px, padding amplio y etapas sin marco propio; eliminado borde nativo adicional. Chromium verifica cuatro beneficios contenidos y sin doble marco a 1440/390 px. [[mi-gobierno]].

- 15-10: Tarjetas de beneficios con separacion de 36 px y borde suave de 1 px gris azulado; sombra reducida. Chromium verifica las cuatro tarjetas en escritorio y movil (1440/390 px). [[mi-gobierno]].

- 15-10: Bordes de beneficios en azul suave #bfd6ec, manteniendo grosor de 1 px y separacion actual. Revision del diff OK. [[mi-gobierno]].

- 15-10: Azul de bordes de beneficios mas visible (#82add3), conservando 1 px y separacion actual. Diff verificado. [[mi-gobierno]].
