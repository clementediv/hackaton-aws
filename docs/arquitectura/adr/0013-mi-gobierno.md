# 0013 · Separar el portal público de Mi Gobierno

Fecha: 2026-10-15. Estado: aceptado por instrucción del usuario.

La página principal sigue siendo ChileAtiende. Mi Gobierno concentra identidad, documentos, situación económica, evaluación de beneficios y rutas. El asistente acompaña el trámite; no ocupa la portada.

Se reutilizan diagnóstico PGU, consentimiento, SQLite, pasos e historial. Se conserva una separación entre antecedentes declarados, documentos adjuntos y datos evaluados; no se transforma un archivo sin revisar en elegibilidad. No se atribuye cobro aprobado a una solicitud guiada.

El primer beneficio evaluable es PGU. Becas y catálogos externos se muestran sin evaluación automática. El siguiente paso de producto es integrar contacto y ampliar el catálogo con reglas verificables, no inferir beneficios mediante un LLM. Implementación y pruebas en [mi-gobierno](../mi-gobierno.md).
