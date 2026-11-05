---
tipo: adr
estado: aceptada
fecha: 2026-10-14
---
# ADR 0003 — Orquestación del agente: Bedrock Converse + tool use propio

## Contexto
[arquitectura-base](../arquitectura-base.md) dejaba abierta la elección entre Bedrock Agents y LangGraph. Para ChileAtiende-a-tiempo, el agente necesita 4 o 5 herramientas deterministas, memoria de caso en DynamoDB y tests locales rápidos.

## Opciones consideradas
1. **Bedrock Agents**: es gestionado, pero requiere action groups, Lambdas y esquemas OpenAPI. Iterar y depurar es más lento, y es difícil ejecutarlo local.
2. **LangGraph**: da más control, pero suma una dependencia y una curva de aprendizaje que no aportan con un grafo de este tamaño.
3. **Bucle propio con la API Converse de Bedrock (tool use)**: unas 100 líneas de Python. Corre local, se testea con herramientas falsas y no requiere infraestructura extra.

## Decisión
Opción 3. Si sobra tiempo, el mismo set de herramientas se puede exponer como action group de Bedrock Agents para mostrarlo en el pitch.

## Consecuencias
- Las herramientas son funciones Python puras, así que Codex puede implementarlas y testearlas en paralelo.
- El historial de conversación y el caso los maneja nuestro código (DynamoDB).
- Hay que limitar las iteraciones del bucle y manejar los errores de las herramientas.
