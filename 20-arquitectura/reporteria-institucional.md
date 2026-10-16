---
tipo: implementacion
fecha: 2026-10-16
responsable: Jonmor
estado: implementado-en-rama
---
# Reportería institucional

Solicitud de Jonmor: compartir con municipalidades y ministerios una lectura territorial de la información del ejecutivo mediante un PDF automático descargable. Decisión en [[0019-reporteria-institucional-agregada]]. Implementación aislada en `codex/reporteria-institucional`; pendiente de revisión antes de integrar a `main`.

## Cómo probar

1. `uv sync --group app` y ejecutar la app como indica [[portal-ayuda-tramites]].
2. Abrir **Para ejecutivos**, ingresar con las cuentas ficticias que muestra el formulario.
3. Abrir **Reportería institucional**. Elegir Municipalidad o Ministerio, escribir opcionalmente el nombre y seleccionar comunas.
4. El resumen y el documento se actualizan automáticamente. Pulsar **Descargar reporte PDF**.

No requiere Bedrock ni consultas AWS. ReportLab genera el documento en memoria; no se guardan PDFs ni archivos temporales en el servidor. La descarga no envía documentos a terceros.

## Qué contiene

- Destinatario, territorio, fecha real de generación y corte de datos (reloj de la simulación para la campaña de demostración).
- Personas únicas de la campaña, pendientes de contacto, espera de orientación y avances declarados.
- Lectura ejecutiva determinista: concentración territorial, acompañamiento y respeto de quienes declinaron.
- Recorrido de alertas con fecha → ingreso → autorización → avance declarado, calculado con [[trazabilidad-casos]].
- Tabla por comuna: personas, pendientes, orientación, inicio en el colador, avance y declinación.
- Fuentes, alcance y distinción entre simulación, registro local y resultado administrativo no confirmado.

El mismo agregado alimenta pantalla y PDF. Los datos de campaña y los eventos SQLite existentes son las únicas fuentes. La demostración usa la misma siembra idempotente y aislada que Trazabilidad; abrir casos de la aplicación nunca agrega actividad ficticia.

## Límites explícitos

Los territorios/contactos del MVP son sintéticos. No se incluyen eventos AWS, nombres, RUN, teléfonos ni correos. Un estado de inicio del colador no sustituye el evento de avance; sin secuencia temporal válida no se infiere conversión. El avance es declarado y requiere validación del organismo. No se presenta el KPI ≥75% como medido ni se atribuyen obligaciones/incentivos legales a instituciones.

La elección de destinatario personaliza el documento, no configura atribuciones territoriales de acceso ni un directorio institucional. No hay envío programado, notificaciones, identidad municipal o ministerial ni sincronización con sus sistemas.

## Implementación y verificación

`ruta/institutional_reports.py`: agregado sin identificadores, filtros y hallazgos. `ruta/institutional_pdf.py`: PDF vectorial A4 con paginación y encabezados de tabla repetidos. `ui_institutional_reports.py` y su CSS: nueva sección del ejecutivo; conserva el acceso con sesión ficticia existente.

`uv run --group app pytest tests/test_institutional_reports.py tests/test_executives.py`: conteos únicos, filtros, secuencia de eventos, ausencia de evidencia, futuro excluido, datos vacíos, extracción de texto PDF, ausencia de identificadores, caracteres especiales, paginación de 80 comunas y recorrido UI con descarga. Revisión visual del PDF y descarga real en Chromium; vista responsive a 390/1440 px.

Cierre de implementación `7887a1e`, integración del equipo `f4e0e37`: **322 pruebas pasan**, dos omitidas por dependencias opcionales y ocho evals Bedrock excluidas. Verificador de 500 perfiles TODO OK. Se limpia la caché Streamlit entre pruebas para aislar las comprobaciones AWS de moto. Descarga real de PDF y revisión visual a 390/1440 px verificadas.

## Heatmap y plantilla editorial · 16-10

El PDF usa una portada azul oscuro con acento turquesa, fondos y cabeceras de
continuidad. Distribución habitual: portada/resumen, inteligencia territorial y
detalle/fuentes. Tablas extensas continúan en páginas adicionales con cabecera
repetida. No depende de una plantilla ni de imágenes de terceros en ejecución.

La página territorial incorpora un heatmap PNG de alta resolución, generado sin
red con Matplotlib/Agg y cartografía local BCN `comunas2017` (referencia de 2017).
Reutiliza `metropolitan_ranking` y `metropolitan_locations` del ejecutivo: solo
pendientes activos de etapa 4 y comunas con al menos cinco casos, tras aplicar
el filtro de comunas del reporte. No inventa ni modifica ubicaciones reales.
La intensidad es densidad suavizada relativa, no conteo por color ni tasa de población.
Solo se muestran coordenadas de origen sintético validadas por el motor existente;
no se incorporan nombres, RUN ni direcciones al mapa del informe.

En la campaña actual de demostración hay 13 ubicaciones publicables de La Florida
y Puente Alto. El resto de pendientes no se fuerza al mapa si no cumple las reglas
de publicación. Sin grupos válidos, muestra ausencia de grupos publicables; el
documento conserva sus cifras y el significado de los ceros.

El mismo mapa aparece en la vista web y en el PDF. La imagen se genera en memoria
y se reutiliza para iguales puntos/filtros. `ruta/report_heatmap.py` implementa la
selección y el render. Se añade Matplotlib al grupo `app`. Pruebas verifican filtros,
umbral, exclusión de casos terminales, ausencia de identificadores y mapa incrustado
en el PDF. Revisión visual de las tres páginas y descarga real en Chromium.

Cierre del rediseño `1350606`, integración `51d74c0`: **330 pruebas pasan**, dos omitidas y ocho evals excluidas; verificador de 500 perfiles TODO OK. PDF descargado desde Chromium con tres páginas, mapa incrustado, revisión visual y vista móvil/escritorio sin desborde. La rama sigue sin integrarse a `main`.

## Mapa web compartido y lenguaje institucional · 16-10

La vista web reemplaza la imagen estática por el mismo `campaign_map` de
«Campañas en terreno»: PyDeck, CARTO Dark Matter, capas, parámetros de calor,
zoom y propuesta amarilla idénticos. Ambos consumen `campaign_context` con
los mismos casos y personal disponible. Sin filtros territoriales adicionales,
el JSON completo del mapa es idéntico entre ambas pestañas (prueba UI).
La reportería aplica sus comunas seleccionadas; el control de personal se
conserva al cambiar entre las dos vistas. El fondo de calles requiere internet.

El PDF conserva el mapa estático offline, basado en las mismas posiciones y reglas;
no es una captura de los tiles remotos. La vista web atribuye CARTO/OpenStreetMap y BCN.

Por solicitud del usuario, la redacción del documento pasa a institucional:
sin «MVP», «prototipo», «escenario simulado» ni detalles de SQLite. Se mantienen
fuentes, corte, alcance y límites del avance declarado. Una nota discreta
«Datos de ejemplo» en el pie identifica el origen ficticio de los datos, sin
presentarlos como registros de personas reales. También se simplifican los
rótulos del mapa estático y de la vista de reportería. No cambia el origen de
la campaña ni se elimina su aislamiento de la aplicación.
