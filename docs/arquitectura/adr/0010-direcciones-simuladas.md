---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0010 — Heatmap desde ubicaciones individuales ficticias

El usuario solicita dispersión realista dentro de la RM en lugar de un foco por comuna, conservando la apariencia de [0009-heatmap-metropolitano](0009-heatmap-metropolitano.md). Autoriza simular direcciones exactas; el dataset del RSH no las contiene.

Generar una ubicación determinista por RUN/semilla, con núcleos barriales y dispersión recortada al polígono BCN de cada comuna. Guardar dirección evidentemente ficticia, coordenadas y procedencia sintética en nuevos contactos. Enriquecer snapshots antiguos sin reescribirlos. No consultar calles, viviendas o personas reales; la coordenada no certifica un domicilio.

Calcular el calor con peso 1 por caso activo admitido, mantener supresión comunal de cinco, retirar inicios/rechazos y omitir coordenadas inválidas con aviso. Reemplazar círculos comunales por calor distribuido, con puntos ficticios y etiquetas agregadas opcionales. Mantener fondo/paleta y ranking exacto. La leyenda explica intensidad relativa.

Esta capacidad individual se restringe a contactos con procedencia sintética. No amplía acceso a datos personales RSH ni es solución de autorización para producción. Ver implementación y evidencia en [heatmap-campanas-simulado](../heatmap-campanas-simulado.md).
