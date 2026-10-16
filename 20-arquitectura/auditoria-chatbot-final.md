---
tipo: verificacion
fecha: 2026-10-16
responsable: Jonmor
---
# Auditoría final del chatbot

Jonmor solicita verificar conversación, cortafuegos, alucinaciones y recepción efectiva de trazas en Arize Phoenix. Bedrock real: `us.anthropic.claude-sonnet-5`, perfil `hackaton`, región `us-east-1`. Perfiles exclusivamente sintéticos. Las pruebas no escriben casos en DynamoDB ni envían mensajes a personas.

## Pruebas reales

`scripts/verificar_chat_final.py` ejecuta 20 escenarios y registra respuesta, motor, llamadas reales, tiempo y comprobaciones en JSON. Incluye saludo, insultos/errores de escritura, ruido, fuera de alcance, PGU/AFP, frustración con consulta válida, documentos, enlace FUAS, aprobación forzada, beneficio inexistente, secretos, terceros, falta de consentimiento, revocación, elegible/no elegible/antecedente faltante e inyección en consulta personal autorizada.

```sh
AWS_PROFILE=hackaton AWS_REGION=us-east-1 BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-5 uv run --group app python scripts/verificar_chat_final.py --output /tmp/chat-final-live.json
```

`--only <identificadores>` permite repetir escenarios concretos. Se observa el cliente real para comprobar que los bloqueos no invocan al modelo y que el historial autorizado anterior no se reenvía después de revocar. El script comprueba estructura y aislamiento; las respuestas necesitan revisión semántica adicional.

Resultado tras correcciones iniciales: 20/20 comprobaciones pasan (`/tmp/chat-final-live-verified.json`). Se repiten cuatro consultas personales después de añadir parámetros del motor y control de montos (`/tmp/chat-final-grounded.json`). La protección detectó una respuesta con cifra ajena y la descartó; se mejora su respaldo para conservar el resultado personal. Dos casos personales se repiten después del ajuste (`/tmp/chat-final-guard-verified.json`). Las salidas de /tmp son evidencia local de esta sesión, no archivos versionados.

Evaluación adicional de la API con los ocho escenarios existentes en `tests/evals/test_chat_eval.py` y juez DeepEval/Bedrock: **8/8 pasan**, 146 segundos. Herramientas: 1,00 en todos; fuente: 0,90–1,00; ausencia de aprobación garantizada: 1,00. Esta evaluación no demuestra veracidad universal de todos los hechos ni sustituye validación institucional de los parámetros legales.

## Hallazgos corregidos

1. «Pagada» se interpretaba como «página» por coincidencia aproximada de dos caracteres. La solicitud de enlace ahora exige términos explícitos, conservando errores de escritura habituales.
2. Los rechazos de secretos o datos de terceros podían terminar con una fuente recuperada irrelevante. Ahora esas solicitudes reciben un rechazo determinista antes de recuperación/LLM y enlazan al portal general.
3. Una respuesta personal eligió un tope monetario del snapshot público distinto del motor. Se añaden parámetros monetarios/referencia al contexto autorizado y prioridad explícita del motor. Una comprobación de moneda descarta respuestas con montos fuera del contexto y responde con resultado/motivo/próximo paso del código. No convierte un antecedente faltante en no elegible ni vuelve a pedir un consentimiento ya otorgado. Decisión en [[0020-montos-personales-fundamentados]].
4. Para un beneficio no identificado, se pide nombre oficial/enlace sin completar la respuesta con montos o plazos de beneficios parecidos.

## Phoenix: estado comprobado

**Las conversaciones actuales no se están enviando a Phoenix.**

- Local: no hay `PHOENIX_COLLECTOR_ENDPOINT` configurado en entorno/dotenv; no hay colector escuchando en 6006. Los adaptadores de Streamlit no llaman a `setup_tracing`; el código de instrumentación existente pertenece a la API. El grupo `app` no declara las dependencias de instrumentación Bedrock.
- AWS: lectura real de `get_function_configuration` de Lambda `ca-chat`: `PHOENIX_COLLECTOR_ENDPOINT` vacío; `PHOENIX_API_KEY_SECRET_ARN` referenciado. Tener un secreto referenciado no habilita la exportación.
- `src/api/tracing.py` solo inicializa cuando hay endpoint; sin él devuelve `None`. La API conserva los puntos de instrumentación y `chat.turn`, pero hoy están inactivos. No se imprimen ni modifican secretos.
- La prueba T19 del 15-10 sí confirmó recepción histórica local (ver [[chatbot-desplegado]]). Eso no acredita recepción de las conversaciones de esta sesión.

Activación pendiente: conectar el adaptador de Streamlit si se desea observar la app local; configurar endpoint y dependencias; comprobar recepción por trace ID en el colector. Para Lambda se necesita endpoint accesible desde AWS y configuración correspondiente. No se modifica infraestructura ni se activa un colector/exportación como parte de esta auditoría.

## Alcance de la conclusión

La batería observa rechazos y consentimiento correctos en los casos probados. Los resultados personales se contrastan con el motor; las fuentes públicas son snapshots. No puede afirmarse «cero alucinaciones»: texto libre, fuente desactualizada y uso incorrecto de una cifra que sí esté en el contexto siguen requiriendo controles y evaluación continua. La guardia de moneda no valida todos los hechos ni las condiciones de una ley.

Verificación en Chromium de la app reiniciada: PGU general con fuente clicable, rechazo de secretos y solicitud de autorización sin sesión personal; sin excepciones visibles. Los selectores usan el textarea estable, porque el placeholder cambia con la animación. Captura local: `/tmp/chat-final-browser.png`. Las dos repeticiones finales personales pasaron con Bedrock y montos presentes en el contexto, sin activar respaldo.

Cierre integrado `f049e33` + `01da393`: **360 pruebas offline pasan**, dos omitidas por dependencias opcionales y ocho evals excluidas de esa suite. Las ocho evals se ejecutaron aparte con Bedrock real y pasaron. Verificador de 500 perfiles TODO OK.
