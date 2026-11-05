# Desplegar el prototipo AWS

Ejecutar desde una copia completa del repositorio. Requisitos: Python 3.12, uv, Node.js/npm y AWS CLI con credenciales de la cuenta de destino. Los comandos siguientes crean recursos facturables; corresponden al entorno de pruebas de transferencia.

## Preparar y sintetizar

Desde la raíz:

```powershell
uv sync --frozen --group infra
$env:AWS_PROFILE = "perfil-del-equipo"  # omitir cuando se use un rol IAM
$env:AWS_REGION = "us-east-1"
aws sts get-caller-identity
cd infra
npx --yes --package aws-cdk@2.1147.0 cdk synth -c email=casilla-verificada@dominio.cl
```

La casilla se proporciona explícitamente: no hay un destinatario personal predeterminado. La síntesis prepara bundles Linux x86_64 con uv y necesita internet, pero no crea recursos. Las dependencias Python provienen de `uv.lock`.

## Desplegar en la cuenta de destino

```powershell
npx --yes --package aws-cdk@2.1147.0 cdk bootstrap
npx --yes --package aws-cdk@2.1147.0 cdk diff --all -c email=casilla-verificada@dominio.cl
npx --yes --package aws-cdk@2.1147.0 cdk deploy --all -c email=casilla-verificada@dominio.cl
```

Repetir el contexto `email` en cada comando CDK. La región está fijada a `us-east-1` en `app.py`. Los nombres de recursos son fijos (`ca-*`): usar una cuenta/región sin una instalación previa o planificar la actualización del stack existente. CDK incluye ambos stacks incluso al sintetizar uno, por lo que necesita la casilla y las dependencias de ambos.

| Stack | Recursos principales | Salidas |
|---|---|---|
| `ChileAtiendeProactivo` | Cuatro tablas DynamoDB, Streams, Lambda, SES, reglas EventBridge y Function URL | `UrlRespuesta`, nombres de tablas |
| `ChileAtiendeChat` | API Gateway HTTP, autorizador Lambda, Lambda de chat, DynamoDB y Secrets Manager | `Url`, `ApiKeySecret` |

SES enviará un correo de verificación: abrir el enlace. En sandbox, verificar también los destinatarios de prueba. Opciones: `-c remitente=...`, `-c emails_extra=casilla1,casilla2`, `-c espera_email_min=5`, `-c espera_sms_min=5`; repetirlas en cada despliegue que deba conservarlas. El SMS y la asignación a terreno son simulados. `-c lambda_role_arn=...` permite un rol existente, cuyos permisos se deben preparar en destino.

El modelo de Bedrock y los recursos IAM correspondientes están definidos en `chat_stack.py` y en la lista permitida de `src/agent/bedrock.py`. Confirmar su disponibilidad y autorización en la cuenta receptora; no se garantiza acceso a los modelos de la cuenta del evento. Phoenix es opcional (`-c phoenix_endpoint=...`); no activar trazas con datos personales sin definir su tratamiento.

## Cargar y verificar

Volver a la raíz del repositorio:

```powershell
cd ..
uv run python scripts/proactivo.py cargar --solo-demo --email casilla-verificada@dominio.cl
uv run python scripts/proactivo.py resumen
uv run python scripts/verificar_chat_health.py
```

La carga crea siete personas ficticias y el catálogo; puede disparar detección y correo real a la casilla indicada. Omitir `--solo-demo` agrega los 500 perfiles sintéticos. Sin `--email`, la carga usa `demo@example.com`, sin envío real. `verificar_chat_health.py` llama a la API y Bedrock (puede consumir tokens) sin imprimir la API key. La key está en Secrets Manager; no incorporarla al repositorio ni al navegador.

Para conectar la app local al stack proactivo, configurar credenciales y `CA_AWS=1`. No hay hosting de Streamlit en estos stacks: esa parte debe ejecutarse localmente o desplegarse en una plataforma acordada con el equipo receptor, con autenticación y almacenamiento persistente. La UI usa SQLite; la API de chat usa DynamoDB.

## Estado de los datos

Estos stacks conservan las políticas `RemovalPolicy.DESTROY` del prototipo, incluidas tablas y secretos. No usar datos de producción ni ejecutar `cdk destroy` sin respaldos y una decisión explícita de eliminación. Antes de producción se deben definir retención, recuperación, aislamiento por ambiente y protección de las rutas públicas; ver [transferencia](../docs/TRANSFERENCIA.md).
