---
tipo: implementacion
fecha: 2026-10-15
estado: en curso
---
# Chatbot desplegado

Implementación progresiva de [[plan-chatbot-desplegado]], etapa de acompañamiento
de [[arquitectura-chileatiende]]. T15 incorpora ChileAtiendeChat sin modificar
ChileAtiendeProactivo. La API HTTP v2 valida x-api-key mediante autorizador Lambda
contra Secrets Manager antes de invocar el handler; el handler vuelve a validarla.
Throttle: 2 solicitudes/s y ráfaga 4. GET /health ejecuta Converse con Sonnet 5.

El bundle utiliza dependencias congeladas de uv.lock con wheels Linux x86_64 de
Python 3.12. Se comprueba pydantic_core y la ruta del dataset dentro del bundle.
IAM permite el inference profile y los foundation models destino en tres regiones.

Verificación local: 177 tests OK, script de 500 perfiles TODO OK, ruff de archivos
nuevos y síntesis CDK OK. Comprobación del template: autorización CUSTOM, throttle
y GSI por-run. Verificación remota: `uv run python scripts/verificar_chat_health.py`.
El script recupera la key sin imprimirla y prueba solicitudes sin key, inválida y válida.

T16–T21 pendientes: repositorio, evaluación/turnos, rutas HTTP, Phoenix, DeepEval
y verificación de continuidad. Health no constituye todavía un chat persistente.

La revisión global de ruff detecta 183 errores heredados fuera de este aporte;
los archivos Python nuevos/modificados pasan lint y formato. No se reformatea
código ajeno como parte de T15.

T15 remoto confirmado: health sin key 401, key inválida 403 y key válida 200
con texto de Bedrock. CloudFormation CREATE_COMPLETE.

T16: repositorio CaseRepository con paginación, lecturas consistentes de caso e
historial, escritura append-only y consulta por RUN normalizado. Dos pruebas moto
pasan con Case completo y consentimiento/revocación serializados.
