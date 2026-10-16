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
- [ ] Detección proactiva en AWS (DynamoDB Streams + Lambda + SES): desplegada el 15-10 en la cuenta del evento (stack `ChileAtiendeProactivo`), 618 contactos simulados cargados; falta verificar la casilla en SES y probar la demo estrella · [[deteccion-proactiva-aws]]

## Por hacer
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
- [ ] `src/app/ruta/alertas.py`: nivel de alerta por RUN; "nivel máximo" en la ficha del ejecutivo
- [ ] Vista simulada del punto de atención CESFAM, con mensaje mínimo ("derivar a ChileAtiende")

### Acompañamiento y back-office
- [ ] Checklist de documentos (pendiente, recibido, validado) guiado por el asistente
- [ ] Derivación al ejecutivo con un resumen del caso

### Unificación y calidad
- [ ] Sincronizar aceptación/rechazo de Mi Gobierno (SQLite) con contactos proactivos (DynamoDB): no son todavía el mismo estado compartido; preservar fin de escalamiento al responder
- [ ] Instrumentar KPI de próximo paso válido dentro del plazo (meta usuario ≥75%): definir evidencia/paso/plazo; contacto e inicio no lo sustituyen
- [ ] Unificar los dos motores (app de Johann y contratos/agente): estados `futuro` y `excluido`, repositorio e historial ([[revision-aporte-johann]]). Coordinar con Johann
- [ ] Contratos: canales de contacto, `ContactAttempt`, `AlertLevel`, `DocumentItem`, `RequestStatus`
- [ ] Prompt: sin una evaluación disponible, no explicar requisitos de memoria
- [ ] `normalize_run`: aceptar RUN sin guion
- [ ] Lint de `src/app` (190 observaciones pendientes)

### Demo
- [ ] Guion de la demo: embudo del colador → heatmap → persona que llega con alerta → acompañamiento → ejecutivo

## Bloqueos
- Datos reales de contacto/provincia siguen pendientes de los mentores. La capa sintética desbloquea el colador de demo y puede alimentar el futuro heatmap; no representa domicilios reales.

## Hecho
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
