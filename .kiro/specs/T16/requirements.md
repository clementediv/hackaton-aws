# T16 · Repositorio de casos

[[plan-chatbot-desplegado]]: Case ↔ DynamoDB, pk=case_id/sk=caso, mensajes
append-only, GSI por-run. Validar DV al crear/buscar, conservar consentimiento y
orden de mensajes. Paginar queries. No modificar contratos.

Verificación: moto, round-trip completo, mensajes con timestamp repetido,
consulta por RUN y permisos antes/después de serializar.
