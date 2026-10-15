# T20 · DeepEval

[[plan-chatbot-desplegado]]: ocho escenarios sintéticos, ToolCorrectnessMetric
sin available_tools y GEval para fuente/no aprobación. Juez reutiliza BedrockClient
Sonnet 5 y valida respuestas JSON con Pydantic y reintentos acotados. Marker eval excluido por defecto,
telemetría opt-out antes de importar DeepEval. Ejecutar y registrar scorecard real.
