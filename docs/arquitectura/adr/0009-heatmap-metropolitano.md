---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0009 — Concentración comunal en la Región Metropolitana

El usuario pide reemplazar el mapa nacional por uno más vistoso, detallado y claro, solo de la RM. Se sustituye la vista de [0008-heatmap-campanas-sinteticas](0008-heatmap-campanas-sinteticas.md) con encuadre urbano, calles vectoriales CARTO/OSM, límites comunales BCN locales, halos de resolución 2048, etiquetas y colores por volumen. El fondo urbano requiere internet; se abandona el requisito interno de contornos nacionales sin proveedor remoto.

La demo genera nuevas ubicaciones sintéticas en ocho comunas metropolitanas, con pesos ilustrativos y sin cambiar contactabilidad, personas ni reglas de elegibilidad. Los escenarios persistidos se conservan; el laboratorio abre una base RM separada. La UI agrega por comuna y suprime grupos menores de cinco antes de mapa, ranking y exportación. Las funciones nacionales previas permanecen compatibles para otros consumidores.

El mapa no pretende localizar viviendas: usa un punto de referencia comunal y halos cualitativos. Los círculos y las etiquetas dan cantidades exactas, con escala fija; el ranking ordena por volumen y desempata por puntaje. No se infiere distribución real del RSH. Detalle, fuentes y verificación en [heatmap-campanas-simulado](../heatmap-campanas-simulado.md).
