# T15 · Despliegue mínimo

Según [[plan-chatbot-desplegado]]: desplegar únicamente ChileAtiendeChat con tabla
ca-casos/GSI por-run, secreto generado, API Gateway HTTP v2 con autorizador Lambda
por x-api-key y throttle 2/s, ráfaga 4. Health ejecuta Converse sobre Sonnet 5.

El bundle incorpora wheels Linux x86_64/Python 3.12 desde uv.lock, comprobando
pydantic_core y ubicación del dataset. IAM permite el inference profile y sus
foundation models en us-east-1, us-east-2 y us-west-2. No modificar Proactivo.

Verificar: tests/test_api_health.py, ruff, synth y health remoto con/sin key.
