---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0015 — Portal de ejecutivos y propuesta automática de operativo

Clemente pide trasladar el backend visual a una página nueva con la estética del frontend, comprensible para asistentes sociales, con menos texto y una propuesta territorial automática que permita ajustar el personal.

Se reutilizan el motor del colador, sus estados, las ubicaciones sintéticas publicables, el mapa y la búsqueda geométrica de [[0011-area-campana-segun-heatmap]]. No se crea otro motor ni se cambian reglas de contacto o elegibilidad. La página separa seguimiento y campañas; el laboratorio conserva sus controles técnicos.

El planificador prueba radios discretos de 750 a 3000 m y elige el menor que cubra una jornada estimada del equipo (8 atenciones por persona). Si no alcanza, muestra el área de mayor cobertura disponible. El personal sí puede cambiar el área propuesta, porque cambia el objetivo; dentro de cada radio, la geometría sigue dependiendo solo de las ubicaciones. Se mantiene el mínimo de cinco casos y la exportación sin datos personales.

La campaña de demostración usa SQLite separado; el selector de casos de la aplicación lee únicamente su embudo. El detalle usa el mismo snapshot y no obtiene antecedentes privados desde otra base. Sincronizar DynamoDB con SQLite sigue pendiente. La nueva UI no afirma cumplir el KPI ≥75%, todavía sin evidencia del próximo paso dentro del plazo.

Consecuencia: acceso directo para gestión cotidiana y datos coherentes entre tarjetas, lista y mapa, con menos controles. Son propuestas de una demo, sin despacho, permisos institucionales ni autenticación profesional de producción. Implementación, límites y ejecución: [[portal-ejecutivos]].
