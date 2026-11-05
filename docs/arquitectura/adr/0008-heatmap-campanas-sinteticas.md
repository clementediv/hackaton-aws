---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0008 — Heatmap agregado para campañas simuladas

## Contexto
El usuario pide visualizar despliegue territorial en la simulación. [contacto-y-campanas](../contacto-y-campanas.md) exige provincias con al menos cinco personas. El dataset RSH entregado no contiene ubicación.

## Decisión
Consumir snapshot y capa sintética existentes, con cola presencial por defecto, agregación región/provincia y supresión previa de grupos pequeños. Ranking determinista con pesos ilustrativos documentados y propuesta descargable de capacidad, sin despacho ni agenda. Mapa pydeck con contornos locales Natural Earth y puntos aproximados de ciudades, sin domicilios ni geocodificación. Seguimiento activo como diagnóstico separado de la planificación presencial.

## Consecuencias
Demo sin AWS ni claves. No finge acceso a un RSH real, centroides oficiales o cobertura nacional. No cambia elegibilidad. No implementa autenticación institucional ni garantiza anonimato frente a diferencias entre consultas. Campañas reales requieren validación territorial, capacidades, agenda y acceso autorizado. Detalle y pruebas en [heatmap-campanas-simulado](../heatmap-campanas-simulado.md).
