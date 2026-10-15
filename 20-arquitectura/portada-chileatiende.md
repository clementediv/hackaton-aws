# Portada basada en ChileAtiende

El banner alterna cada 10 segundos entre Beneficios y Asistente IA mediante un fragmento de Streamlit; solo se actualiza el banner. Las dos opciones se pueden seleccionar manualmente y el control «Rotación automática» permite pausarlo. Elegir una vista o pulsar «Probar el asistente» pausa la rotación para conservar el borrador. La prueba ofrece un campo de consulta y ejemplos; al enviar, la pregunta pasa una sola vez al asistente existente en Ayuda para tus trámites, sin iniciar sesión ni autorizar antecedentes por la persona. Se conserva el alcance/motor del asistente existente, con Bedrock opcional y respuestas locales según configuración.

Se retira el logo de la esquina superior derecha de ambas vistas del banner. Los avisos «Press enter to submit form» se ocultan globalmente en los campos mediante el selector de instrucciones nativo de Streamlit; los formularios y botones conservan su funcionamiento.

El logo IPS se ubica en la esquina superior derecha del banner completo: 100 px en escritorio y 72 px en móvil. El texto mantiene la alineación izquierda y reserva espacio para evitar superposición. La fila superior contiene logo ChileAtiende, buscador y Red de atención; se retira el botón duplicado Mi Gobierno. La navegación principal conserva Inicio, Mi Gobierno y Ayuda para tus trámites. Vista ejecutivo pasa al panel lateral de demostración, con sus herramientas y retorno a las vistas ciudadanas verificados.

El logo IPS se reduce a 160 px en escritorio y 120 px en móvil; queda centrado horizontalmente en su espacio, sin desplazamiento hacia la esquina.

El acceso principal usa ahora «Ver mis beneficios»: azul plano, borde de 4 px de radio, altura de 52 px y tipografía de 17 px, sin degradado ni sombra. El logo IPS se alinea arriba a la derecha, con máximo de 220 px; en móvil conserva adaptación y no desborda.

La invitación vuelve a alinearse a la izquierda y agrega a la derecha el archivo `src/app/assets/IPS.png` proporcionado por el usuario, conservando proporciones y texto alternativo. En móvil el logo se apila debajo. El botón secundario de trámites sigue retirado.

La invitación principal ocupa una sola columna centrada: título, descripción y botón «Descubrir mis beneficios». Se elimina el botón lateral «Ver trámites y beneficios» y la columna que lo contenía.

Se retiran también los tres textos del directorio lateral: «TRÁMITES Y SERVICIOS», «¿Buscas algo en particular?» y su descripción. El enlace al catálogo se conserva.

La invitación principal conserva el mismo recuadro y retira «CONOCE MI GOBIERNO» y «Tus datos · Tus documentos · Tu ruta de beneficios». Título de 44 px y descripción de 19 px, con botón principal de 68 px de alto, texto de 20 px y degradado azul dentro de la paleta. El directorio lateral también amplía tipografía y controles. En móvil se ajusta el título a 32 px y el botón ocupa el ancho disponible. El aviso sobre elegibilidad/resolución y el enlace de fechas ya no se renderizan en las líneas de tiempo.

Las opciones de navegación centran el texto respecto del subrayado activo: se elimina el padding del texto reservado para el control radio oculto. El mismo ajuste se aplica a las subpestañas de Mi Gobierno, conservando su diseño segmentado.

**Diseño vigente:** Inicio conserva el portal público y una invitación a [[mi-gobierno]]. El agente ya no aparece en la portada; el espacio personal reúne identidad, antecedentes y beneficios, y el asistente acompaña dentro de la ruta. Los párrafos siguientes conservan la evolución previa de la portada.

El buscador se ubica en el encabezado entre el logo y los accesos, y se retiró el rótulo «Destacamos» para dar entrada directa al agente. La búsqueda mantiene sus resultados y enlaces oficiales.

La entrada del agente usa un saludo destacado, caja de consulta amplia y tres ejemplos que inician la conversación. El directorio queda como acceso lateral. Se retiró el título general sobre el buscador de Inicio a petición del usuario; las demás vistas conservan sus títulos.

Destacamos incorpora una entrada conversacional inspirada en https://america.gov/: campo para describir una necesidad, envío al asistente existente y acceso a un directorio local de trámites. La pregunta pasa una sola vez al chat sin aceptar ni autorizar por la persona. La selección de trámites permite filtrar y abrir las fichas oficiales. El asistente conserva su alcance de jubilación/PGU y usa plantillas cuando Bedrock no está configurado.

Referencia: https://www.chileatiende.gob.cl/, consultada el 15-10-2026.

La app abre en Inicio. `src/app/assets/official-home.html` conserva una instantánea de las secciones públicas de la portada y su pie, sin scripts. Los enlaces abren el portal oficial; las imágenes y fuentes se incluyen en los recursos locales. `official-home.css` contiene los estilos oficiales dentro de `@scope (.official-home)` para evitar afectar los controles de Streamlit. `portal.css` adapta el encabezado y el buscador nativos.

Ayuda para tus trámites y Mi ruta conservan el acompañamiento y los permisos del MVP. La navegación adicional y los controles de demostración pertenecen al prototipo; no se reproduce el inicio de sesión oficial. La etiqueta del prototipo se conserva en el pie.

Los destacados son una instantánea editorial, no contenido actualizado automáticamente. Para renovarlos se debe revisar el portal oficial y actualizar los recursos locales. Los recursos HTML y CSS están incluidos en el paquete Python.

Validación: 136 pruebas pasan, incluida navegación, búsqueda y aceptación/autorización/revocación. Ver [[portal-ayuda-tramites]].
