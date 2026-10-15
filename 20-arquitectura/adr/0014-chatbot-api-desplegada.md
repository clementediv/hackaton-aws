---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0014 · API desplegada del chatbot

## Contexto
[[plan-chatbot-desplegado]] lleva el agente local de [[arquitectura-chileatiende]]
a Lambda sin modificar el stack proactivo desplegado.

## Decisión
Crear ChileAtiendeChat con API Gateway HTTP v2, autorizador Lambda por API key
almacenada en Secrets Manager y throttling. Empaquetar wheels Linux mediante uv.
La evaluación determinista vivirá fuera del agente, con leer_caso como única
herramienta; queda pendiente unificar motores con Clemente y Johann.

## Consecuencias
T15 probó primero el despliegue mínimo. T16–T21 completan persistencia,
consentimiento, trazas y evaluaciones. Phoenix queda inerte en Lambda sin endpoint;
la recepción local fue verificada. Tres turnos HTTPS y seis mensajes recargados por
AWS CLI confirman continuidad. La key autentica al integrador demo; x-run no sustituye
una identidad ciudadana verificada.
Las trazas pueden contener prompts, respuestas y RUN sintéticos; si el endpoint
es gestionado, ese contenido sale de AWS hacia un tercero.
El plan reporta que us.anthropic.claude-haiku-4-5 no es un inference profile válido:
el identificador real incluye -20251001-v1:0. Pendiente coordinar el allowlist con
Clemente; este aporte no lo cambia y usa Sonnet 5.
