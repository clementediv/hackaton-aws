---
tipo: implementacion
fecha: 2026-10-15
estado: implementado
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

T15–T21 implementadas: repositorio, evaluación/turnos, rutas HTTP, Phoenix, DeepEval
y continuidad verificada en AWS. Streamlit conserva su adaptador local; su migración
a esta API queda fuera del alcance de este plan.

La revisión global de ruff detecta 183 errores heredados fuera de este aporte;
los archivos Python nuevos/modificados pasan lint y formato. No se reformatea
código ajeno como parte de T15.

T15 remoto confirmado: health sin key 401, key inválida 403 y key válida 200
con texto de Bedrock. CloudFormation CREATE_COMPLETE.

T16: repositorio CaseRepository con paginación, lecturas consistentes de caso e
historial, escritura append-only y consulta por RUN normalizado. Dos pruebas moto
pasan con Case completo y consentimiento/revocación serializados.

T17: evaluación determinista persistida en un ítem separado `evaluacion`, evitando
forzar estados divergentes en PguResult. La herramienta vuelve a verificar permiso
antes de consultar datos. Tres pruebas offline demuestran dos turnos con memoria,
error de herramienta sin permiso y persistencia al agotar seis iteraciones.

T18: rutas de creación, invitación, consentimiento, consulta y chat implementadas.
La key autentica al integrador; x-run acota el caso solicitado para la demo, pero
no prueba identidad ciudadana. Producción requiere integrar una identidad
verificada antes de exponer datos reales. Declinar revoca autorización.

T19: instrumentación opcional de Bedrock antes de construir el cliente, span
chat.turn y flush en finally. Prueba real Sonnet 5: leer_caso OK, dos spans
bedrock.converse anidados en chat.turn. Un colector caído no rompió el turno.
Prueba offline adicional con Stubber confirma el identificador exacto del modelo.

Phoenix local se instala aislado para evitar conflictos con la app:

```sh
uv tool run --python 3.12 --from 'arize-phoenix>=12,<13' \
  --with 'arize-phoenix-evals>=2.8,<3' --with 'graphql-core==3.2.6' \
  --with 'fastapi==0.115.12' --with 'starlette==0.46.2' phoenix serve
AWS_PROFILE=hackaton PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006 \
  uv run --group api python scripts/verificar_chat_tracing.py
```

Los límites extra corrigen incompatibilidades transitivas observadas al iniciar
Phoenix 12 (evals 3, graphql-core y cambio de firma TemplateResponse).

Recepción T19 confirmada en Phoenix 12.35: UI Chrome muestra proyecto ca-chat y
chat.turn (17,8 s); API del colector devuelve ese span y dos bedrock.converse hijos.
Trace ID: 07ede8f4a30670148475cb21d5bf3d22. Captura local /tmp/chat-phoenix.png.

## T20 · Scorecard real

| Escenario | Herramientas | Fuente | Sin aprobación |
|---|---|---|---|
| elegible | 1.00 | 0.90 | 0.90 |
| no_elegible | 1.00 | 0.90 | 1.00 |
| hito | 1.00 | 1.00 | 1.00 |
| sin_registro | 1.00 | 1.00 | 1.00 |
| sin_permiso | 1.00 | 0.90 | 1.00 |
| fuera_alcance | 1.00 | 0.90 | 1.00 |
| injection | 1.00 | 1.00 | 1.00 |
| documentos | 1.00 | 1.00 | 1.00 |

Seis escenarios pasan en la ronda completa; los dos casos ajustados de expectativas
de leer_caso pasan en una segunda ejecución seleccionada (2/2). Se verifica además
que sin autorización no se guarda evaluación y ninguna llamada de herramienta es exitosa.
El juez valida JSON por Pydantic; Sonnet 5 rechaza temperature y se omite ese parámetro.

## T21 · Verificación final

ChileAtiendeChat en UPDATE_COMPLETE. `scripts/chat.py --run 100000010-4 --verify`
creó caso, aceptó invitación, autorizó fuentes y completó tres turnos vía HTTPS.
El tercero recordó Rosa y atención telefónica del primero. AWS CLI, con lectura
consistente de ca-casos, confirmó seis mensajes del caso
6f00091d-3f8d-4649-8fa6-f5633a926478. Health: 401 sin key, 403 inválida, 200 con Bedrock.

188 pruebas offline pasan, ocho evals excluidas. Verificador 500 perfiles TODO OK.
Un timeout inicial de Streamlit pasó al repetir la prueba individual (1,05 s) y
la suite completa (188/188). Assertions CDK y synth pasan; lint/formato de los 23
archivos Python del aporte pasan. El lint global conserva errores heredados.

Phoenix en Lambda queda **cableado e inerte**, sin endpoint Cloud configurado.
Para activarlo, reemplazar el valor de ca-chat-phoenix-key por la key real y desplegar
con `-c phoenix_endpoint=https://...`; no se debe exportar datos reales sin resolver
identidad y tratamiento de datos. La recepción local de trazas se comprobó en T19.

Cliente interactivo: `uv run python scripts/chat.py --run 100000010-4`.
Prueba de continuidad: agregar `--verify`. El cliente usa el perfil hackaton y recupera
la API key desde Secrets Manager sin imprimirla. No publicar esta key en el frontend.
La identidad ciudadana verificada, transportes de contacto y estado institucional de
solicitudes quedan fuera de esta API de integración demo.

## Integración remota final

Tras incorporar origin/main 9486b88, cinco tests UI fallan por cambios remotos de
navegación y banner (pestaña Ayuda retirada y monotonic eliminado). Se reprodujeron
los mismos cinco fallos en un snapshot limpio de origin/main: cinco fallos y once
pruebas correctas en los archivos de UI afectados. No se modifican esos archivos.
Antes de ese merge pasaron 188/188; la integración final conserva las pruebas del
chat correctas. El verificador de perfiles sigue TODO OK.

Se comprobó también la configuración real de API Gateway: autorización CUSTOM en
todas las rutas, rate 2/s y burst 4, consultando get_routes/get_stages.

Resultado final integrado: **193 pruebas correctas, cinco fallos UI heredados y ocho evals excluidas**. Verificador TODO OK. T15–T21 en origin/main mediante df99c3b. Último merge adicional solo añadió CSS y specs de detección, sin cambiar el bundle desplegado.
