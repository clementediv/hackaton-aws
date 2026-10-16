---
tipo: adr
estado: aceptado-para-rama
fecha: 2026-10-16
---
# 0019 — Reportería institucional agregada y PDF local

Jonmor solicita una rama para reportería destinada a municipalidades y ministerios, con una presentación estética y PDF descargable desde la página.

Se incorpora al portal de ejecutivos una sección que reutiliza campaña y trazabilidad existentes; un agregado sin identificadores alimenta pantalla y PDF. El destinatario y las comunas son configurables. La generación es automática, determinista y local con ReportLab, sin LLM ni servicios nuevos. La descarga usa `application/pdf` y no envía el informe a instituciones.

Se conservan las definiciones de [[0018-trazabilidad-de-uso]]: contacto, inicio, avance declarado y decisión administrativa son distintos. No se inventa cumplimiento del KPI en plazo. La simulación está marcada y aislada; no se mezclan sus eventos con casos de la aplicación. Fuentes y fecha de corte viajan en el PDF.

La primera entrega no implementa permisos municipales/ministeriales ni despacho automatizado. Se mantiene el acceso del ejecutivo y se comparte un documento agregado. Rama `codex/reporteria-institucional`; integración a `main` pendiente de revisión del usuario. Detalles y pruebas en [[reporteria-institucional]].
