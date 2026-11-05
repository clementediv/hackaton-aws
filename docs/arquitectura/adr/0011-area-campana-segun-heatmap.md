---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0011 — Proponer un área de campaña desde la concentración espacial

El usuario pide marcar un área de despliegue en función del heatmap de [0010-direcciones-simuladas](0010-direcciones-simuladas.md). La propuesta se calcula desde las mismas ubicaciones publicables, sin usar colores de pantalla ni un centro comunal fijo.

`ruta/despliegue.py` busca un círculo de radio configurable que cubra el mayor número de personas: prueba cada ubicación y los dos centros posibles de círculos que pasan por cada par a distancia ≤ 2 radios. Usa una proyección plana local de la RM en metros; los desempates favorecen compactación y coordenadas para reproducibilidad. Se muestra solo si cubre al menos cinco casos. El centro puede ajustarse a la media de los cubiertos cuando preserva la cobertura.

La UI dibuja contorno amarillo y relleno tenue sobre el calor, muestra casos, porcentaje sobre las ubicaciones del mapa y jornadas según capacidad. Radio por defecto 1,5 km, ajustable 0,5–3 km. Exporta resumen JSON y geometría GeoJSON sin direcciones ni identificadores. Solo se habilita con la cola presencial; seguimiento activo sigue siendo diagnóstico.

Es una propuesta geométrica con datos ficticios, no una sede habilitada, agenda ni ruta vial. El círculo puede cruzar comunas y no se recorta al límite administrativo. La capacidad cambia jornadas, no quién está dentro del radio. El responsable valida acceso y lugar. Se conservan fondo y paleta. Implementación y evidencia: [heatmap-campanas-simulado](../heatmap-campanas-simulado.md).
