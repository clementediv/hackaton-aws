---
tipo: adr
estado: aceptada
fecha: 2026-10-14
---
# ADR 0002 — Reto elegido: ChileAtiende a tiempo

## Contexto
Hay ocho retos disponibles (ver _seleccion) y unas 1,5 jornadas efectivas de desarrollo, con cierre el viernes 16 a las 10:15. Criterios de evaluación: innovación técnica 25%, impacto social 25%, factibilidad 20%, escalabilidad 15% y presentación 15%. La cuenta del evento tiene Bedrock con Claude Sonnet 5, Opus 5 y Haiku 4.5.

## Opciones consideradas
Los ocho retos de `10-retos/`.

## Decisión
Trabajar en ChileAtiende-a-tiempo: construir una ruta de beneficios, plazos y pasos a partir de un evento de vida, con continuidad entre canales.

## Consecuencias
- El núcleo es un agente LLM con herramientas, lo que encaja directamente con Bedrock.
- Tiene alto impacto social y la demo es fácil de entender en un pitch.
- Riesgo principal: la calidad del catálogo de beneficios. Mitigación: limitar el alcance y priorizar el evento nacimiento.
- La factibilidad depende de no inventar requisitos ni plazos: reglas en código y fuentes citadas.
