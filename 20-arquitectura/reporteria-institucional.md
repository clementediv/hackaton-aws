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
