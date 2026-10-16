---
tipo: board
integrante: Clemente
entorno: Claude Code + Codex
---
# Board de Clemente

| | |
|---|---|
| **Entorno** | Claude Code + Codex |
| **Integración** | Commit del aporte → fetch/merge de `origin/main` → resolver y verificar → push |
| **Bitácora** | [[bitacora-clemente]] |
| **Equipo y pipeline** | [[_equipo]] · [[_avance]] |

Lista de pendientes propia, sin tareas asignadas. Ordenada según el pipeline de [[_equipo]].

## En curso
- [ ] Detección proactiva en AWS (DynamoDB Streams + Lambda + SES): desplegada el 15-10 en la cuenta del evento (stack `ChileAtiendeProactivo`), 618 contactos simulados cargados; falta verificar la casilla en SES y probar la demo estrella · [[deteccion-proactiva-aws]] → tarea **M1** del cierre final

## Por hacer
### Cierre final del MVP (16-10) — reparto Codex / Claude
Los puntos 1–4 del cierre anterior ya están en `main` ([[app-aws-conectada]]; los tests del chat los arregló `6bf5ffe`). Quedan 10 tareas: 5 para Codex y 5 para Claude. **Cada agente toca solo sus archivos** (columna «Archivos»); si necesitas uno del otro, déjalo anotado aquí en vez de editarlo. Antes de empezar, marca la tarea con «⏳ en curso»; al terminar, `[x]` con el commit. Flujo de [[AGENTS]]: commit → merge de `origin/main` → `uv run --group app pytest` y `uv run --group app python src/app/verificar.py` → push. **No commitear** `35-roles/_equipo.md` (cambio ajeno), la foto de WhatsApp ni `dataset_A_participantes.zip` (repo público).

#### Para Codex (implementación acotada, tests y guion)
| # | Archivos |
|---|---|
| C1 | `src/app/demo_embudo.py` |
| C2 | `src/tools/profiles.py`, `tests/` |
| C3 | `src/agent/prompts.py`, `tests/` |
| C4 | `src/app/ruta/government.py`, `src/app/ui_government.py` (solo documentos), `src/app/ui_ficha.py` (solo el bloque «Documentos y declaración»), `tests/` |
| C5 | `00-inbox/guion-demo.md` (nuevo) |

- [ ] **C1. (en curso por Codex) `src/app/demo_embudo.py` con cambio local sin commitear** (quita los escenarios precargados del laboratorio del embudo; parece una versión vieja). **Preguntar a Clemente** antes de tocarlo: descartar (`git checkout -- src/app/demo_embudo.py`) o commitear. **Acepta:** `git status` limpio en ese archivo y el laboratorio de :8502 con escenarios.
- [ ] **C2. (en curso por Codex) `normalize_run` acepta RUN sin guion.** `src/tools/profiles.py` hoy exige guion; `src/app/ruta/demo_auth.py` ya acepta `123456785`, `12.345.678-5` y espacios. Igualar el comportamiento (sin duplicar la lógica si se puede importar una de la otra sin ciclos). **Acepta:** test con `123456785`, `12345678-5`, `12.345.678-5` → `12345678-5`; DV inválido y texto vacío siguen fallando; el resto de la suite verde.
- [ ] **C3. (en curso por Codex) Prompt sin evaluación.** En `SYSTEM_PROMPT` (`src/agent/prompts.py`): si no hay una evaluación disponible de las herramientas, no explicar requisitos ni montos de memoria; decir qué falta (perfil, autorización o herramienta) y ofrecer el próximo paso. **Acepta:** test que verifica la regla en el prompt y que los tests de `src/agent` siguen verdes.
- [ ] **C4. (en curso por Codex) Checklist de documentos pendiente → recibido → validado.** Hoy un adjunto queda «pendiente de revisión» y nadie lo valida. (a) `government.py`: columna/estado de revisión (`validated_by`, `validated_at`) con migración que no rompa `casos.db` existentes; `validate_document(run, kind, reviewer)` y `list_documents` devuelve `status` = `recibido` | `validado`. (b) Ficha del beneficiario, bloque «Documentos y declaración»: botón «Marcar validado» por documento (usuario ejecutivo de la sesión). (c) Mi Gobierno: cada documento requerido muestra «Pendiente», «Recibido · en revisión» o «Validado por ChileAtiende». Validar un documento **no** cambia la elegibilidad (lo dice la ficha). **Acepta:** tests de `government` (estados, migración, borrar documento vuelve a pendiente) y una prueba AppTest de la ficha.
- [ ] **C5. (en curso por Codex) Guion de la demo + checklist previo** en `00-inbox/guion-demo.md` (absorbe los ex-6 y 7 y el «Guion de la demo» de la sección Demo). **Guion (~5 min):** (a) Vista ejecutivo → Contactos AWS → «Reiniciar contactos de esta persona» y luego «Simular evento de vida»: Jorge Demo (90000002-2) cumple 65 → llega el email real; (b) clic en «Quiero orientación» del email; (c) ficha del beneficiario con historial AWS y alerta; (d) mapa de calor y campañas; (e) Mi Gobierno con el aviso y documentos; (f) **punto de atención CESFAM con alerta máxima y derivación** (M2–M3, de Claude); (g) Medición con el **KPI de próximo paso ≥75%** (M4, de Claude); (h) Trazabilidad. Por paso: qué hacer, qué decir y tiempo. **Plan B** si AWS falla (la app avisa y sigue con SQLite). **Checklist previo** con comandos copiables: `aws sts get-caller-identity --profile hackaton` (las claves vencen ~6 h), casilla SES verificada, una sola app en :8501 (cerrar copias), `uv run python scripts/proactivo.py cargar --solo-demo` y `... resumen`. Escribir (a)–(e) y (h) ya; (f) y (g) cuando M2–M4 estén en `[x]`. **Acepta:** guion probado una vez de punta a punta en :8501.

#### Para Claude (AWS en vivo, diseño y features nuevas)
| # | Archivos |
|---|---|
| M1 | AWS (sin cambios de código salvo fix) |
| M2–M3 | `20-arquitectura/cesfam-derivacion.md` (nuevo), `src/app/ruta/derivaciones.py` (nuevo), `src/app/ui_cesfam.py` (nuevo), `src/app/app.py`, `src/app/portal.py` |
| M4 | `src/app/app.py` (`vista_kpis`), `src/app/ruta/` (módulo nuevo de KPI) |
| M5 | `20-arquitectura/arquitectura-chileatiende.md`, board y bitácoras |

- [x] **M1. Demo estrella en vivo contra AWS** (16-10, 13:16): casilla SES `Success`; reinicio de Jorge → evento «cumple 65» → detectado en ~1 s → email real (SES `010001a144dba29b…`) → abierto → clic «Quiero orientación» HTTP 200 → contacto `aceptado` con próximo paso; el escalamiento se detiene. Jorge quedó **aceptado**: reiniciarlo antes del ensayo.
- [x] **M2. Punto de atención CESFAM simulado:** Vista ejecutivo → **Punto CESFAM**. Ingresa el RUN y solo muestra «Derivar a ChileAtiende» o «Sin avisos»; alerta máxima = colador en etapa 4 sin respuesta o contacto AWS en `terreno`. Para la demo muestra RUNs de ejemplo (p. ej. con contactos AWS en terreno) · [[cesfam-derivacion]].
- [x] **M3. Derivación al ejecutivo con resumen del caso:** `src/app/ruta/derivaciones.py`; en **Atención del caso**, «Derivaciones pendientes» con el resumen (persona, alerta, PGU, invitación, colador, autorización, documentos con consentimiento, próximo paso, AWS) y «Atender» abre el caso. Eventos `derivacion` y `derivacion_atendida` en el historial. 7 tests (`tests/test_derivaciones.py`) · [[cesfam-derivacion]].
- [ ] **M4. KPI de próximo paso válido dentro del plazo (meta ≥75%):** definir evidencia, paso y plazo; contacto e inicio no lo sustituyen; mostrarlo en Medición.
- [ ] **M5. Cierre de documentación:** arquitectura (componentes 13–14), próximos pasos y board.

Fuera del MVP (después de la demo): lint de `src/app`, unificar motores y datos (SQLite/DynamoDB), contratos nuevos y estados reales de entrega de email.

### Validar con los mentores
- [ ] ¿Hay un dataset con email, teléfono, empleador y provincia (¿dataset B?)?
- [ ] Base legal para la alerta en CESFAM y para el contacto a través del trabajo
- [ ] Uso de la marca e identidad visual de ChileAtiende en el portal
- [ ] Hora exacta de entrega y formato de evaluación

### Colador de contacto ([[contacto-y-campanas]])
- Backend del embudo y demo visual implementados; envíos y campañas presenciales reales quedan fuera de la simulación. Ver [[backend-embudo-contacto]].

**Seguimiento por etapa vigente** ([[0012-detener-contacto-confirmado]]):

| Situación | Siguiente acción |
|---|---|
| Email sin respuesta, aunque se haya abierto | Tras 7 días simulados, pasa a llamada |
| Llamadas sin respuesta | Hasta 3 intentos en 5 días; luego pasa a contacto laboral |
| Contacto laboral sin respuesta | Tras 7 días simulados, queda pendiente de campaña presencial |
| Falta email, teléfono o empleador | Se salta ese canal y se registra el motivo |
| Responde o acepta en cualquier etapa | Se detienen los canales posteriores y pasa a acompañamiento del trámite |
| Declina | Se detiene todo; no se insiste por otros canales |

Los plazos son propuestas de demo, no plazos institucionales. El acompañamiento posterior al contacto debe guiar el próximo paso del trámite y registrar su avance; no debe reactivar la búsqueda por otros canales porque la persona siga pendiente de iniciar.

**Pendientes para envíos reales:**
- [ ] Registrar estados diferenciados de email: intento/envío, entregado, rebotado, abierto, respuesta y aceptación/rechazo. Hoy solo hay intentos simulados; no se confirma entrega real.
- [ ] Definir y probar el siguiente canal según el resultado: entregado sin respuesta espera el plazo; rebote/dato inválido requiere una política explícita de recuperación o cambio de canal. No equiparar envío/apertura con contacto confirmado ni inventar que la persona ignoró un mensaje que quizá no recibió.

### Heatmap y alerta de beneficio
- [x] Nivel de alerta por RUN y «nivel máximo» en la ficha del ejecutivo: ya existe como `ficha.alert_level` (`src/app/ruta/ficha.py`)
- → Vista simulada del punto de atención CESFAM: tarea **M2** del cierre final

### Acompañamiento y back-office
- → Checklist de documentos (pendiente, recibido, validado): tarea **C4** del cierre final
- → Derivación al ejecutivo con un resumen del caso: tarea **M3** del cierre final

### Unificación y calidad
- [x] Sincronizar aceptación/rechazo de la app con contactos proactivos (DynamoDB): hecho el 16-10 ([[app-aws-conectada]]); el resto del estado de casos sigue en SQLite
- → Instrumentar KPI de próximo paso válido dentro del plazo (meta usuario ≥75%): tarea **M4** del cierre final
- [ ] Unificar los dos motores (app de Johann y contratos/agente): estados `futuro` y `excluido`, repositorio e historial ([[revision-aporte-johann]]). Coordinar con Johann
- [ ] Contratos: canales de contacto, `ContactAttempt`, `AlertLevel`, `DocumentItem`, `RequestStatus`
- → Prompt: sin una evaluación disponible, no explicar requisitos de memoria: tarea **C3** del cierre final
- → `normalize_run`: aceptar RUN sin guion: tarea **C2** del cierre final
- [ ] Lint de `src/app` (190 observaciones pendientes): después de la demo

### Demo
- → Guion de la demo: tarea **C5** del cierre final

## Bloqueos
- Datos reales de contacto/provincia siguen pendientes de los mentores. La capa sintética desbloquea el colador de demo y puede alimentar el futuro heatmap; no representa domicilios reales.

## Hecho
- [x] Cierre del MVP 1–3: simular evento de vida desde la Vista ejecutivo (la Lambda detecta y envía), aviso AWS en Mi Gobierno con respuesta por beneficio, y aceptar/declinar en la app detiene el escalamiento en AWS. Tests con moto y AppTest; `CA_AWS=0` en los tests. Commit «Conectar la app con la detección proactiva en AWS» · [[app-aws-conectada]].
- [x] Enlace de respuesta incompleto devuelve 400 y no 502; desplegado en AWS — `8a6c26b` · [[deteccion-proactiva-aws]].
- [x] Animaciones del home: entrada escalonada, revelado al hacer scroll y tarjetas con hover suave. Cinco pruebas, Ruff y Chromium 390/1440 px normal/reducido OK. [[portal-ayuda-tramites]]. Commit: Pulir animaciones del home.
- [x] Texto de ambos chats más rápido (25 ms por palabra) y sin cursor automático; placeholder actualizado directamente, preservando formato y alineación. Nueve pruebas enfocadas y Chromium 390/1440 px OK; discrepancia previa de URL fuente PGU documentada. Commit «Acelerar el texto y quitar el cursor del chat». [[mi-gobierno]].
- [x] Alineación validada en pantalla completa: servidor 8501 conservaba módulo anterior (Markdown). Reiniciado con código vigente; verificador exige HTML nuevo y centra los 16 detalles en tres anchos. Commit «Verificar detalles en la aplicación completa». [[mi-gobierno]].
- [x] Detalles de beneficios centrados como Resultado de la revisión: HTML nativo evita recorte inferior de Markdown; anchos contenidos y padding adicional solo con acciones. Chromium 390/900/1440 px confirma desviación horizontal/vertical de 0 px. Commit «Alinear los recuadros de detalles de beneficios». [[mi-gobierno]].
- [x] Datos personales minimalista y fuentes del portal; identidad, documentos, contacto, trabajo y salud unificados. Cinco pruebas, Ruff y Chromium 390/900/1440 px OK. Commit: Unificar el estilo de Datos personales. [[mi-gobierno]].
- [x] Entradas de Mi Gobierno suaves y escalonadas: beneficios, asistente, identidad y secciones; sin transform persistente y con movimiento reducido. Chromium 390/1440 px y cuatro pruebas OK. Commit «Pulir entradas animadas de Mi Gobierno». [[mi-gobierno]].
- [x] Respuestas nuevas alineadas con el robot: placeholder reutilizado directamente y scroll fuera del mensaje en ambos chats. Nueve pruebas funcionales y Chromium a 390/1440 px con dos turnos por chat OK. Commit «Alinear respuestas nuevas con el robot». [[mi-gobierno]].
- [x] Subir saludo inicial del asistente; Chromium 390/1440 px OK. [[mi-gobierno]]. Commit: Acercar saludo al titulo del asistente.
- [x] Restaurado s?mbolo original azul y rojo sobre Asistente de IA; verificaci?n CSS OK. [[mi-gobierno]]. Commit ?Restaurar s?mbolo del asistente de Mi Gobierno?.
- [x] Respuesta del asistente personal alineada por arriba con avatar: flex-start, contenido sin padding/margen superior y primer bloque sin margen superior. Chromium sobre respuesta real confirma coordenada superior identica de avatar, contenido y primer parrafo. [[mi-gobierno]]. Commit ?Alinear respuestas con el avatar del asistente?.
- [x] Asistente IA alineado con titulo PGU: encabezado general antes de ambas columnas, retirado padding fijo de 52 px y decoracion superior del asistente. Marco azul #82add3 de 1 px igual a beneficios y padding equivalente, sin borde duplicado. Chromium confirma diferencia vertical 0 px al inicio y movil sin desborde; cuatro pruebas Mi Gobierno pasan. [[mi-gobierno]]. Commit ?Alinear y enmarcar el asistente de Mi Gobierno?.
- [x] Azul de bordes de beneficios mas visible (#82add3), manteniendo grosor y separacion; diff verificado ? commit ?Marcar mas el azul de los bordes de beneficios? ? [[mi-gobierno]].
- [x] Bordes de beneficios en azul suave #bfd6ec, conservando 1 px y separacion; revision del diff OK ? commit ?Usar azul suave en los bordes de beneficios? ? [[mi-gobierno]].
- [x] Tarjetas de beneficios con separacion de 36 px y borde suave de 1 px gris azulado; sombra reducida. Chromium verifica las cuatro tarjetas en escritorio y movil (1440/390 px). [[mi-gobierno]]. Commit ?Separar tarjetas de beneficios y suavizar bordes?.
- [x] FUAS, gratuidad y becas usan el mismo marco unico de PGU: borde exterior de 2 px, padding amplio y etapas sin marco propio; eliminado borde nativo adicional. Chromium verifica cuatro beneficios contenidos y sin doble marco a 1440/390 px. [[mi-gobierno]]. Commit ?Unificar el marco de todas las tarjetas de beneficios?.
- [x] Corregida interpretacion del marco PGU: un borde visible de 2 px envuelve titulo, monto, etapas y desplegable de requisitos; la linea de tiempo queda sin borde ni fondo propio. Chromium confirma contencion completa y sin doble marco a 1440/390 px. [[mi-gobierno]]. Commit ?Enmarcar PGU completa sin recuadro interior?.
- [x] Recuadro de etapas PGU mas amplio: borde azul de 2 px, padding 24 px en escritorio y 18 px en movil, titulo de 17 px. Marco exterior sigue retirado. Chromium verifica borde, padding y contencion a 1440/390 px. [[mi-gobierno]]. Commit ?Ampliar y destacar el recuadro de etapas PGU?.
- [x] PGU sin marco exterior: contenedor Streamlit sin borde y CSS sin fondo/padding exterior; se conserva un solo recuadro para etapas. Chromium confirma borde exterior 0 px, interior 1 px y sin desborde a 1440/390 px. [[mi-gobierno]]. Commit ?Quitar marco exterior de la tarjeta PGU?.
- [x] Retirados rotulo ilustrativo y nota inferior del banner PGU a pedido del usuario. Checklist con separacion de 1,1 s, entrada de 0,8 s y checks de 1,12 s. Indices definidos con nth-child en CSS porque el renderizador elimina atributos style del HTML. Chromium verifica retrasos y finalizacion; cinco pruebas del portal OK. [[portal-ayuda-tramites]]. Commit ?Ralentizar checklist PGU y simplificar el banner?.
- [x] Ejemplo del banner PGU en afirmativo: requisitos cumplidos y beneficio listo para cobrar. Etiqueta ilustrativa visible sobre el titulo; revision personal y confirmacion IPS indicadas al pie. Checklist animado conservado. Cinco pruebas del portal OK. [[portal-ayuda-tramites]]. Commit ?Presentar en afirmativo el ejemplo del banner PGU?.
- [x] Banner de beneficios reemplazado por pregunta sobre requisitos PGU, cuatro puntos ilustrativos de revision y checks secuenciales descendentes sincronizados con el ciclo de 16 segundos. CTA a revision personal en Mi Gobierno; no se afirma elegibilidad sin perfil. Chromium 1440/390 px y movimiento reducido OK; cinco pruebas del portal pasan. [[portal-ayuda-tramites]]. Commit ?Mostrar checklist animado de PGU en el banner?.
- [x] Trazabilidad visual posalerta, sesiones, condiciones, avance declarado, continuidad 7/30 días y tiempos entre accesos. Registro de uso en Mi Gobierno; demo aislada e identificada. 260 pruebas y Chrome escritorio/móvil OK · `96abb06`, integración `fb6eea5` · [[trazabilidad-casos]].
- [x] Retirado botón «Cobrar beneficio» de Mi Gobierno para acotar el MVP; 24 pruebas de UI/integración y verificador de 500 perfiles OK · commit «Retirar botón de cobro del MVP de Mi Gobierno» · [[mi-gobierno]].
- [x] Inicio/cierre de sesión del ejecutivo con dos cuentas ficticias, diseño del portal y sesión separada de Mi Gobierno; acceso requerido también en herramientas laterales. Pruebas y Chrome escritorio/móvil OK · commit «Agregar acceso ficticio para ejecutivos y asistentes sociales» · [[portal-ejecutivos]].
- [x] Portal para ejecutivos con estética ChileAtiende, seguimiento, filtros y mapa RM con propuesta automática según personal. Pruebas funcionales y revisión Chrome escritorio/móvil. Implementación `81755d7`, integración `710df25` · [[portal-ejecutivos]].
- [x] Pulido del chat publico: textarea contenido dentro del borde y sin padding que recorta lineas; burbuja de persona con altura suficiente para todo el texto. Chromium verifica banner, dos turnos, enlaces de fuentes y nueva conversacion a 390/900/1440 px. Cinco pruebas enfocadas OK. [[portal-ayuda-tramites]]. Commit ?Ajustar campo y burbujas del chat en movil?.
- [x] Chat publico con bienvenida centrada, encabezado compacto, mensajes de persona a la derecha y entrada fija redondeada; CSS separado y responsive. Reinicio local elimina importacion obsoleta de responder_publico. Prueba de UI de respuesta y nueva conversacion OK; Chromium verifica envio y anchos 1440/390 sin desborde. Referencia america.gov/chat no accesible desde navegador de consulta. [[portal-ayuda-tramites]]. Commit ?Pulir la interfaz del chat publico?.
- [x] Retirados encabezado introductorio y descripcion de acompanamiento encima del listado de beneficios, a solicitud del usuario. [[mi-gobierno]]. Commit ?Quitar introduccion del listado de beneficios?.
- [x] Banner inicia con asistente IA y cambia de slide cada 8 segundos (ciclo de 16 segundos). Orden HTML actualizado tambien para movimiento reducido. Chromium confirma estado inicial y duracion. [[portal-ayuda-tramites]]. Commit ?Iniciar banner con asistente y rotar cada 8 segundos?.
- [x] Slides del banner cada 2,5 segundos: ciclo CSS completo de 5 segundos para dos paneles. Duracion comprobada en Chromium. [[portal-ayuda-tramites]]. Commit ?Rotar slides del banner cada 2,5 segundos?.
- [x] Animaciones suaves de entrada para tarjetas, etapas y chat; transiciones de botones, foco del campo y tarjetas de portada. Movimiento reducido desactiva efectos. Chromium verifica escritorio/movil, limites de tarjetas y prefers-reduced-motion. Retiradas las sugerencias bajo el chat del banner; campo y envio conservados. [[portal-ayuda-tramites]]. Commit ?Animar la interfaz y simplificar el chat del banner?.
- [x] Textos del resultado y requisitos centrados horizontalmente respecto de todo el recuadro, con padding simetrico e icono independiente a la izquierda. Chromium en pantalla real verifica 16 recuadros centrados y contenidos a 1440, 900 y 390 px. [[mi-gobierno]]. Commit ?Centrar textos dentro de los recuadros de requisitos?.
- [x] Recuadros de requisitos: icono y bloque de texto centrados verticalmente, ancho con padding incluido y texto contenido. Chromium en Mi Gobierno completo confirma 16 recuadros alineados a 1440 y 390 px. [[mi-gobierno]]. Commit ?Alinear contenido de tarjetas de requisitos?.
- [x] Ancho del bloque HTML de etapas corregido y verificado en pantalla completa; commit ?Contener el HTML de etapas dentro de la tarjeta? ? [[mi-gobierno]].
- [x] Compactar l?nea de tiempo y contener tarjeta; verificaci?n Chromium en tres anchos OK ? commit ?Compactar etapas del beneficio y contener su ancho? ? [[mi-gobierno]].
- [x] Banner del asistente con t?tulo principal ?Prueba el asistente de inteligencia artificial?, dise?o neutro centrado, campo de texto redondeado, env?o con flecha y preguntas frecuentes como sugerencias. Cuatro pruebas del portal OK. [[portal-ayuda-tramites]]. Commit ?Dar estilo conversacional al banner del asistente?.
- [x] Chat de texto directo y t?tulo ?Prueba nuestro asistente de inteligencia artificial?, con preguntas frecuentes; cuatro pruebas del portal OK ? commit ?Mostrar chat directo en el banner del asistente? ? [[portal-ayuda-tramites]].
- [x] Merge de detección proactiva local y aportes remotos de Mi Gobierno, acceso demo y beneficios — `9626cac`; sin conflictos de texto, 174 pruebas y verificador de 500 perfiles OK; cambios locales sin commit conservados
- [x] Integrado también el último aporte de ayuda audiovisual/documentos por requisito — `1932574`; conflicto de bitácora resuelto conservando ambos registros, 174 pruebas completas y verificador OK
- [x] Chat con bienvenida breve, burbujas de persona diferenciadas y saludos sin repetir diagnóstico; preguntas no reconocidas piden aclaración. 153 pruebas, verificador y Chrome OK · commit «Mejorar la conversación y presentación del asistente» · [[mi-gobierno]].
- [x] Campo para preguntar debajo del chat de Mi Gobierno, con historial reducido a 240 px y sin aviso del 101/sucursal · commit «Acercar la entrada al chat y retirar aviso de atención» · [[mi-gobierno]].
- [x] Campo para preguntar justo debajo del encabezado del asistente de Mi Gobierno, antes del historial · commit «Subir el campo de consulta del asistente» · [[mi-gobierno]].
- [x] Retirar las preguntas frecuentes del asistente de Mi Gobierno; conversación y campo de escritura conservados. Cuatro pruebas de UI/integración OK · commit «Quitar preguntas frecuentes de Mi Gobierno» · [[mi-gobierno]].
- [x] Asistente de Mi Gobierno más amplio, conversación primero y preguntas frecuentes desplegables; apilado en pantallas estrechas. Chrome 1440/900/390 px, 146 pruebas y verificador OK · commit «Ordenar y ampliar el asistente de Mi Gobierno» · [[mi-gobierno]].
- [x] Reunir mapa, detección, ficha, atención y medición bajo «Vista ejecutivo», con selector interno y verificación de UI · commit «Unificar herramientas de gestión en Vista ejecutivo» · [[ficha-beneficiario]].
- [x] Ficha del beneficiario en la app y fuente única de contacto para Mi Gobierno, colador y ficha · [[ficha-beneficiario]]
- [x] Contacto confirmado detiene canales posteriores; responded/accepted separados de inicio, barra por personas y tabla de intentos, ejemplos con/sin respuestas y meta 75% sin falsos resultados — `0642159`, 136 tests · [[0012-detener-contacto-confirmado]]
- [x] Área propuesta sobre el heatmap por máxima cobertura espacial, radio ajustable, jornadas por capacidad y descargas JSON/GeoJSON — `66dbea8`, 126 tests · [[heatmap-campanas-simulado]]
- [x] Calor distribuido por persona, direcciones/coordenadas ficticias dentro de su comuna, puntos inspeccionables y compatibilidad con escenarios anteriores — `643a888`, 113 tests · [[heatmap-campanas-simulado]]
- [x] Rediseño RM: calles detalladas, 52 límites comunales BCN, concentración con conteos, escala fija, escenario sintético RM y vista de región completa — `475100e`, 99 tests; Chrome 1440/1024 px a doble densidad · [[heatmap-campanas-simulado]]
- [x] Heatmap de campañas por provincia sintética, ranking con umbral de 5 y propuesta descargable de despliegue según personal/capacidad — `b4d517f`, 90 tests · [[heatmap-campanas-simulado]]
- [x] Capa de contacto sintética rotulada (500 filas) — `7d1d8e0` · [[backend-embudo-contacto]]
- [x] Backend `src/app/ruta/colador.py` y CLI por lotes: reloj, saltos, tres llamadas en cinco días, inicio/rechazo y persistencia — `7d1d8e0`
- [x] Respuestas simuladas con semilla fija y efecto ilustrativo de edad; sin LLM ni envíos — `7d1d8e0`
- [x] Embudo en Detectar e invitar y laboratorio independiente en localhost:8502 — `7d1d8e0`, 84 tests pasan · [[backend-embudo-contacto]]
- [x] Base Python, contratos compartidos, consulta autorizada del perfil, prompt y herramientas, y agente con Bedrock Converse (T01–T05, ver [[bitacora-clemente]])
- [x] Reestructuración de la idea central: [[0005-asistente-contacto-escalonado]] y [[contacto-y-campanas]]
