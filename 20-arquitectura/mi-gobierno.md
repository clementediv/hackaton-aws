# Mi Gobierno

Texto progresivo sin cursor: ambos chats usan `chat_feedback.render_text_stream` sobre el placeholder existente. Evita el símbolo automático de `write_stream` sin tocar caracteres del contenido ni las fuentes. Pausa artificial compartida de 25 ms por palabra (antes 80 ms); no modifica la latencia de Bedrock. Prueba de preservación exacta del texto y observador de cursor durante la prueba Chromium. Nueve pruebas enfocadas pasan; otra prueba existente de streaming discrepa en la URL de fuente PGU (ChileAtiende frente a Ventanilla Única).

Verificación posterior del servidor real: el proceso local 8501 seguía usando el módulo anterior con Markdown; se reinició con el código vigente. `python scripts/verificar_detalles_pantalla.py` recorre acceso, consentimiento y detalles de todos los beneficios en la aplicación completa: exige `stHtml`, comprueba centrado del texto y captura pantalla a 390/900/1440 px. Así detecta también procesos que no recargaron el módulo actualizado.

Los detalles y Resultado de la revisión usan `st.html` en el componente común: Markdown reducía 16 px el alto efectivo del recuadro interior sin borde y desplazaba el centro vertical 8 px. Contenedores con border-box y ancho contenido; el padding de acciones se aplica solo si hay popovers. `scripts/verificar_detalles_beneficios.py` mide texto y rectángulo reales en Streamlit a 390/900/1440 px, con centrado horizontal y vertical exacto en resumen y requisitos cumplidos/pendientes.

Las entradas visuales usan `government-enter`: opacidad y desplazamiento de 12 px durante 560 ms con desaceleración suave, tarjetas separadas por 70 ms y etapas por 70 ms. Se animan superficies individuales al montarse, sin transformar la página ni la columna sticky; el transform se libera al terminar. Cambiar contenido de un bloque existente no reinicia la entrada. `prefers-reduced-motion` desactiva los efectos. Comprobación Chromium del CSS: `scripts/verificar_animaciones_gobierno.py`, 390/1440 px, secuencia, final, actualización y movimiento reducido. Cuatro pruebas funcionales de Mi Gobierno pasan.

Alcance MVP ajustado por Clemente: se retira el botón «Cobrar beneficio» de la tarjeta PGU cuando el resultado orientativo es elegible. La tarjeta conserva situación, monto estimado, calendario, requisitos y chat; no ofrece una acción de cobro. Las acciones de preparación y antecedentes de otros estados permanecen disponibles. Verificación del flujo de sesión, consentimiento, documentos y revocación en `tests/test_government.py`.

El bloque introductorio del acceso se sube otros 18 px (padding superior de 12 px). El campo se etiqueta «ClaveÚnica» y su placeholder es «Ingresa tu clave»; el desplegable «Probar con otro perfil ficticio» permanece debajo. El mecanismo de acceso sigue usando las credenciales sintéticas existentes.

El formulario de acceso retira el subtítulo de demostración, el recuadro «Prueba el portal» con RUN/clave y su nota inferior. Los campos centran verticalmente texto y placeholder en 48 px. El campo de clave conserva su nombre de demostración y el selector de perfiles de prueba sigue en el desplegable separado.

Se elimina el rótulo superior «MI GOBIERNO» del acceso. El título «Tus beneficios, con tu información» y el encabezado del formulario comparten el mismo inicio, sin márgenes superiores en los títulos.

El acceso al portal alinea arriba sus dos columnas. La introducción «Tus beneficios, con tu información» usa 30 px de margen interior superior para acompañar la altura del encabezado del formulario; en móvil se elimina ese margen y se mantiene el apilado.

El asistente lateral incorpora un desplegable «Preguntas frecuentes» con accesos de un clic a qué es la PGU, monto, documentos, fechas, canales y requisitos. Cada botón usa el mismo motor, contexto, consentimiento e historial que escribir la pregunta. Antes de autorizar se muestran las dos preguntas generales del asistente. El desplegable mantiene compacto el panel cuando no se usa.

La línea de tiempo muestra solo los nombres de las etapas, fechas y estados. A pedido del usuario se retiran las explicaciones bajo cada punto y el pie con advertencia/enlace a fechas oficiales; las fuentes del calendario permanecen documentadas aquí.

Cada beneficio incorpora una línea de tiempo antes de desplegar requisitos: Postulación, En revisión y Resultado, con fechas, estados escritos y marcadores numerados. Horizontal en escritorio y vertical hasta 700 px. Verde indica antecedentes listos; amarillo, faltantes; gris, etapas futuras. No se infieren envíos ni resoluciones por completar pasos locales o subir archivos. Si el registro sintético indica PGU vigente, el resultado lo refleja sin inventar una fecha de resolución.

Las fechas de educación corresponden al primer periodo FUAS 2027: postulación del 1 al 22 de octubre de 2026, nivel socioeconómico el 17 de diciembre, preselección el 15 de enero de 2027 y asignación el 10 de marzo. [Calendario oficial Mineduc consultado el 15-10-2026](https://postulacion.beneficiosestudiantiles.cl/fuas/index.php). Fuera de la ventana se indica que cerró y se remite a nuevas fechas; no se reutiliza como calendario de otro año. PGU muestra disponibilidad anual o apertura personal calculada, y fechas de revisión/resolución por confirmar. [Fuente oficial PGU](https://www.ventanillaunicasocial.gob.cl/ficha/95/pension-garantizada-universal). No hay integración de seguimiento oficial de solicitudes; los hitos futuros se muestran pendientes.

El chat lateral comienza alineado con la tarjeta PGU (52 px después del encabezado del listado). En escritorio acompaña el desplazamiento con posición sticky y se mantiene centrado verticalmente mientras queda contenido de Beneficios. La tarjeta tiene esquinas de 24 px. En pantallas de hasta 1050 px se desactiva el seguimiento y se conserva la distribución apilada. Verificado en Chrome: alineación inicial, centro al desplazar, borde y móvil sin desbordamiento.

## Acceso de demostración

Al entrar desde Descubrir mis beneficios, el encabezado o la navegación, se solicita RUN y **ClaveÚnica de demostración**. El usuario confirmó expresamente que el acceso es ficticio. La clave de prueba es `demo2026`; la pantalla muestra un RUN de ejemplo y permite consultar otros perfiles sintéticos.

`ruta/demo_auth.py` normaliza RUN con/sin puntos, valida el dígito y exige que exista entre los perfiles vivos de la demo. La sesión guarda el identificador del perfil, no la clave; el valor del campo contraseña se retira del estado al enviar el formulario, también si hay error. Cerrar sesión limpia el estado personal y el chat, sin borrar documentos persistidos. No se permite cambiar de persona desde el selector lateral: para otro perfil se vuelve a ingresar.

Este acceso no se conecta a ClaveÚnica ni consulta datos reales. No equivale al consentimiento para usar antecedentes: la autorización sigue siendo explícita y revocable. La autenticación real futura debe usar el flujo de redirección oficial y una integración registrada, no pedir la contraseña real dentro de la app. Referencia: [integración institucional de ClaveÚnica](https://www.claveunica.gob.cl/instituciones).

Mi Gobierno conserva el diseño segmentado con dos subpestañas: Beneficios y Datos personales. Se elimina Chatbot porque el asistente ya está a la derecha de Beneficios: proporción 2,15:1, contenido sin límite de ancho y márgenes laterales de 32 px. Se restaura el diseño del chat anterior a su separación en una pestaña (referencia `46f0c76`): tarjeta blanca con borde discreto, burbujas grises para la persona e historial compacto de 240 px con entrada debajo. Se retiran el fondo azul, el borde superior y la sombra añadidos después. Hasta 1050 px se apila bajo los beneficios; en móvil los márgenes bajan a 16 px. La guía PGU sigue sin chat lateral.

Los requisitos pendientes incluyen las acciones dentro de su recuadro amarillo: «Ver ayuda» y «Adjuntar documento». Se complementa únicamente información faltante respecto de los antecedentes compartidos; los archivos existentes aparecen disponibles para reutilización. PGU permite complementar RSH o residencia cuando el motor marca información faltante; edad o incumplimiento conocido ofrecen ayuda y no sugieren que subir un archivo cambie el resultado. Cada requisito educativo relaciona sus documentos de apoyo mediante un catálogo explícito. La carga respeta consentimiento, límites, formatos y repositorio compartido; no confirma elegibilidad.

La ayuda abre instrucciones, enlace oficial, video incrustado y enlace alternativo a YouTube. Recursos consultados: [orientación PGU](https://www.youtube.com/watch?v=SZ6gcANAzsQ) y [tutorial FUAS de Mineduc, 2022](https://www.youtube.com/watch?v=IRZnHopEGRU). Se identifican como orientación general de una edición anterior y se remite a la fuente oficial para fechas/requisitos vigentes; no se presentan como tutoriales específicos de cada certificado.

Cada requisito desplegado se muestra en un recuadro verde si el motor lo marca cumplido y amarillo si falta información, no se cumple o está pendiente; el texto distingue estos estados. La revisión global de PGU también tiene un recuadro. FUAS, gratuidad y becas siguen pendientes de verificación, sin inventar elegibilidad. Los adjuntos compartidos usan verde para «Documento adjunto» y amarillo para «Falta adjuntar»; adjuntar un archivo no valida el requisito ni concede el beneficio. Navegación, estados y ausencia de desbordamiento verificados en Chrome a 1440 y 390 px.

**Navegación vigente:** Mi Gobierno abre en Beneficios. Datos personales es una vista separada con las cinco secciones y todos los tipos de adjuntos. Cada beneficio despliega sus requisitos y permite adjuntar los documentos de apoyo faltantes allí mismo.

El chat diferencia los mensajes de la persona con una burbuja gris alineada a la derecha y mantiene las respuestas del asistente sobre fondo blanco. La bienvenida autorizada es breve y no repite el diagnóstico que ya muestra Beneficios. En modo plantillas, «hola» y variantes reciben un saludo conversacional; agradecimientos tienen respuesta propia y preguntas no reconocidas piden aclaración en lugar de repetir el resumen. Bedrock sigue siendo opcional: estas respuestas locales no equivalen a conversación generativa libre. Siete regresiones nuevas; 153 pruebas pasan excluyendo el aporte proactivo no versionado, verificador de 500 perfiles OK y Chrome 1440/390 px valida «hola» sin duplicar diagnóstico ni desbordar.

Los archivos se guardan una sola vez por persona y tipo de documento, independientemente del lugar de carga. PGU, FUAS, gratuidad y becas consultan ese repositorio compartido: el archivo existente aparece disponible, sin pedir otra subida. Reemplazar o eliminar afecta a todos los beneficios que lo usan. Se agregaron comprobante FUAS, matrícula, antecedentes académicos y certificado de residencia al catálogo de documentos personales. La disponibilidad del archivo no equivale a validación ni altera la elegibilidad.

Tus datos se organiza en 01 Identidad personal, 02 Domicilio y contacto, 03 Documentos, 04 Información laboral y 05 Previsión y salud. Se conservan el carnet y controles de privacidad; los adjuntos quedan en Documentos. Profesión, ocupación y actividad económica se guardan como declaraciones. Previsión y salud exige consentimiento y una acción de mostrar datos; no se inventa sistema de salud cuando no existe en el dataset.

El resumen junto al carnet muestra domicilio, comuna, región, correo, teléfono y estado civil en lugar de estados de cédula/licencia. Domicilio, comuna, región, email y teléfono salen de la **misma fuente que el colador** (`ruta.ficha.contact_for`): el contacto que usó la campaña si la persona está en ella, y si no, la capa sintética. Si falta un canal, se muestra «Sin información». Antes el email se armaba con el nombre y el teléfono era fijo, lo que no coincidía con el colador. Ver [[ficha-beneficiario]].

Para completar la maqueta, nacionalidad se muestra como CHILENA; emisión y vencimiento ausentes usan las fechas ficticias 15 OCT 2025 y 15 OCT 2035. La firma de ejemplo se compone tipográficamente del nombre y apellido sintéticos. Se conserva la etiqueta DEMO; estos valores no alimentan validaciones documentales.

El perfil de demostración muestra nacionalidad Chilena por solicitud del usuario. Se retiró la leyenda inferior y se conserva DEMO en la esquina. RUN (también en el resumen), número de documento y nacimiento aparecen como `****`, con controles de ojo accesibles para revelar/ocultar cada campo. Es una ocultación visual del lado del navegador, no cifrado ni control de autorización; no modifica el consentimiento ni el motor de beneficios.

El carnet incluye todos los campos de la referencia: apellidos, nombres, nacionalidad, sexo, fecha de nacimiento, número de documento, fecha de emisión, fecha de vencimiento, firma del titular y RUN. Los campos ausentes del dataset se muestran como «Sin información»; no se inventan fechas, nacionalidad ni firmas.

El carnet minimalista toma distribución y paleta del ejemplo `assets/El_ejemplo_de_Cedula_identidad_Chile_2013.jpg`: retrato a la izquierda, datos a la derecha, encabezado azul y fondo celeste suave. Es HTML/CSS con datos dinámicos, silueta ilustrativa y marca de documento ficticio; no copia fotografía, firma, sellos ni mecanismos de seguridad del ejemplo. El número de documento no consultado se indica expresamente.

La acción superior derecha es ahora un botón directo «Revocar autorización». Abre un solo diálogo modal de confirmación, sin un menú «Mis permisos» previo. Cancelar o cerrar el diálogo conserva los datos; solo la confirmación elimina los adjuntos y revoca el consentimiento.

Mis permisos se abre desde la esquina superior derecha de Tus datos. Revocar requiere dos acciones: solicitar revocación y confirmar expresamente la eliminación. La confirmación advierte que se borran documentos y declaración económica y que habrá que adjuntarlos otra vez. Cancelar conserva datos y autorización.

En Tus datos, los adjuntos se presentan como cinco casillas independientes: cédula, licencia, RSH, comprobante de ingresos y antecedentes. Cada una permite adjuntar, reemplazar y eliminar su archivo sin seleccionar el tipo en un formulario general. La situación económica se edita en el mismo bloque, antes del listado de beneficios.

El listado apila PGU, FUAS, gratuidad y becas de educación superior. Las tres entradas educativas muestran «Faltan datos para verificar» y permiten abrir sus antecedentes por confirmar y fuente Mineduc. FUAS se identifica como formulario, no pago. No se infiere elegibilidad estudiantil del perfil previsional; el catálogo se amplía con `EDUCATION_OPTIONS` y exige reglas oficiales antes de habilitar solicitudes personalizadas.

**Presentación vigente:** primero Tus datos con el carnet ficticio y después una lista compacta de beneficios. Se retiraron bienvenida, etiqueta de cuenta, tarjetas de montos/resumen y pestañas. Datos editables, adjuntos, otros apoyos y permisos quedan en desplegables; requisitos y detalle se consultan desde cada beneficio.

La identidad se muestra como un carnet de demostración con nombres, apellidos, RUN, fecha de nacimiento y sexo del perfil seleccionado. Usa una silueta y marca visible «DOCUMENTO FICTICIO · SIN VALIDEZ»; no incorpora sellos, firma ni códigos de verificación oficiales.

La portada pública sigue siendo ChileAtiende. El encabezado y la invitación de Inicio llevan a **Mi Gobierno**, un espacio personal de demostración. El agente ya no aparece en Inicio; acompaña la ruta de un beneficio.

## Recorrido disponible

1. Elegir un perfil sintético en la barra lateral (sin integración con ClaveÚnica).
2. Aceptar explícitamente el acompañamiento y autorizar la consulta de antecedentes. Sin permiso no se muestran RSH, pensiones ni resultados personalizados.
3. Consultar Mis beneficios, Mi información y Mis documentos. Identidad viene del dataset; vigencia de cédula y licencia no se inventan.
4. Guardar situación laboral, ingresos, integrantes y antecedentes declarados. Adjuntar PDF/JPG/PNG de hasta 10 MB por tipo de documento. Adjuntos y declaración quedan en SQLite local, nunca versionados ni enviados al LLM.
5. Abrir «Cobrar beneficio» únicamente con PGU elegible según el motor existente. Faltantes abren «Completar antecedentes», edad próxima abre preparación y los incumplimientos bloquean el cobro. Se explican los requisitos que originaron el resultado.
6. Seguir una ruta con las dependencias de PGU y sus antecedentes, manteniendo los IDs/historial existentes. La persona confirma sus pasos; resolución y pago requieren al organismo. No hay envío de solicitudes, pago real ni agente que opere portales externos.

La declaración de ingresos, el tramo CSE y el archivo RSH no se convierten automáticamente en PFP ni en evidencia validada. Adjuntar un archivo no concede el beneficio. El botón abre la guía para la solicitud, no acredita un pago aprobado. El monto mostrado es orientativo y usa la fecha de referencia/parámetros del prototipo.

## Alcance del catálogo

La evaluación personalizada integra PGU, no todos los beneficios chilenos. Becas y otros apoyos aparecen como **sin evaluar**, con enlaces al catálogo oficial; no se presentan como beneficios concedidos. Un catálogo futuro necesita fuentes oficiales, reglas versionadas por vigencia y cobertura de requisitos, además del scraping de fichas. No basta con una lista producida por un LLM.

Referencias consultadas el 15-10-2026:
- [PGU, ChileAtiende](https://www.chileatiende.gob.cl/fichas/102077).
- [Ventanilla Única Social](https://www.ventanillaunicasocial.gob.cl/).
- [Becas de arancel, Mineduc](https://portal.beneficiosestudiantiles.cl/becas/becas-de-arancel).

## Persistencia y verificación

`ruta/government.py` agrega tablas de declaraciones y documentos en `config.DB_PATH`. Los archivos se validan por extensión, firma y tamaño; se guardan como BLOB local con hash y nombre saneado. Es una demo sin autenticación real, no un repositorio de documentos de producción. La revocación desde Mi Gobierno elimina esos adjuntos/declaraciones; la lectura y escritura siempre exigen el consentimiento actual. Reiniciar la demo elimina ambas tablas personales.

139 pruebas y verificador de 500 perfiles pasan. Se cubren todos los estados PGU, dependencias de ruta, consentimiento, carga inválida/tamaño, declaraciones sin alterar elegibilidad, navegación, pasos y revocación. Ver [[0013-mi-gobierno]] y [[portada-chileatiende]]. El proceso de contacto conserva el backend existente; su siguiente integración de experiencia queda aparte.

- 15-10: L?nea de tiempo compacta: menos padding, marcadores de 30 px y texto reducido; tarjetas con box-sizing border-box para contener su ancho. Chromium verific? el componente a 390/900/1440 px sin desborde. Test actualizado a st.html; tres pruebas pasan, prueba integral falla despu?s en expectativa de chat tras revocar (fuera del CSS). [[mi-gobierno]].

- 15-10: Corregido desborde real de etapas: stHtml recibia 875 px dentro de 833 px disponibles por el padding de la tarjeta. Se limita el bloque HTML al 100% del ancho interior. Chromium sobre Mi Gobierno completo confirma cuatro tarjetas contenidas a 1440, 900 y 390 px. [[mi-gobierno]].

- 15-10: Recuadros de requisitos: icono y bloque de texto centrados verticalmente, ancho con padding incluido y texto contenido. Chromium en Mi Gobierno completo confirma 16 recuadros alineados a 1440 y 390 px. [[mi-gobierno]].

- 15-10: Textos del resultado y requisitos centrados horizontalmente respecto de todo el recuadro, con padding simetrico e icono independiente a la izquierda. Chromium en pantalla real verifica 16 recuadros centrados y contenidos a 1440, 900 y 390 px. [[mi-gobierno]].

- 15-10: Retirados encabezado introductorio y descripcion de acompanamiento encima del listado de beneficios, a solicitud del usuario. [[mi-gobierno]].

- 15-10: PGU sin marco exterior: contenedor Streamlit sin borde y CSS sin fondo/padding exterior; se conserva un solo recuadro para etapas. Chromium confirma borde exterior 0 px, interior 1 px y sin desborde a 1440/390 px. [[mi-gobierno]].

- 15-10: Recuadro de etapas PGU mas amplio: borde azul de 2 px, padding 24 px en escritorio y 18 px en movil, titulo de 17 px. Marco exterior sigue retirado. Chromium verifica borde, padding y contencion a 1440/390 px. [[mi-gobierno]].

- 15-10: Corregida interpretacion del marco PGU: un borde visible de 2 px envuelve titulo, monto, etapas y desplegable de requisitos; la linea de tiempo queda sin borde ni fondo propio. Chromium confirma contencion completa y sin doble marco a 1440/390 px. [[mi-gobierno]].

- 15-10: FUAS, gratuidad y becas usan el mismo marco unico de PGU: borde exterior de 2 px, padding amplio y etapas sin marco propio; eliminado borde nativo adicional. Chromium verifica cuatro beneficios contenidos y sin doble marco a 1440/390 px. [[mi-gobierno]].

- 15-10: Tarjetas de beneficios con separacion de 36 px y borde suave de 1 px gris azulado; sombra reducida. Chromium verifica las cuatro tarjetas en escritorio y movil (1440/390 px). [[mi-gobierno]].

- 15-10: Bordes de beneficios en azul suave #bfd6ec, manteniendo grosor de 1 px y separacion actual. Revision del diff OK. [[mi-gobierno]].

- 15-10: Azul de bordes de beneficios mas visible (#82add3), conservando 1 px y separacion actual. Diff verificado. [[mi-gobierno]].

- 15-10: Asistente IA alineado con titulo PGU: encabezado general antes de ambas columnas, retirado padding fijo de 52 px y decoracion superior del asistente. Marco azul #82add3 de 1 px igual a beneficios y padding equivalente, sin borde duplicado. Chromium confirma diferencia vertical 0 px al inicio y movil sin desborde; cuatro pruebas Mi Gobierno pasan. [[mi-gobierno]].

- 15-10: Respuesta del asistente personal alineada por arriba con avatar: flex-start, contenido sin padding/margen superior y primer bloque sin margen superior. Chromium sobre respuesta real confirma coordenada superior identica de avatar, contenido y primer parrafo. [[mi-gobierno]].


La respuesta nueva reemplaza directamente el indicador mediante `response.write_stream`, sin contenedor intermedio. El componente invisible de scroll queda fuera del mensaje del asistente para no participar en su distribuci?n vertical. Mismo ajuste aplicado al chat p?blico. Verificaci?n: `python scripts/verificar_chat_scroll.py --alignment-only` mide avatar y primer p?rrafo en dos turnos nuevos por chat y ancho (390/1440 px).

- 15-10: Restaurado el s?mbolo original azul y rojo sobre Asistente de IA, retirando la regla CSS que lo ocultaba. Verificaci?n est?tica de visibilidad, dimensiones y colores OK; navegador no disponible (sin uv ni playwright). [[mi-gobierno]]. Commit ?Restaurar s?mbolo del asistente de Mi Gobierno?.

- 15-10: Saludo inicial de Mi Gobierno mas arriba: margen superior de 20 a 0 px y padding superior de 18 a 0 px. Chromium verifica ambos espacios en 0 a 390/1440 px. [[mi-gobierno]]. Commit: Acercar saludo al titulo del asistente.

- 15-10: Corregido el asistente de Mi Gobierno: pregunta alineada a la derecha durante la espera y scroll limitado al historial sin arrastrar la pagina. Verificacion de navegador con respuesta demorada y nueve pruebas funcionales. [[mi-gobierno]].

- 15-10: Datos personales unificado con el estilo minimalista de Mi Gobierno: Roboto/Roboto Slab, identidad neutra, campos legibles, secciones con separadores y documentos con un solo marco. Consentimiento, adjuntos y formularios conservados. Cinco pruebas funcionales, Ruff y Chromium a 390/900/1440 px OK. Verificación reproducible: `python scripts/verificar_datos_personales.py`. [[mi-gobierno]]. Commit: Unificar el estilo de Datos personales.
