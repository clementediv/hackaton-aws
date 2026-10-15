# Preflight · chatbot-desplegado · 2026-10-15

Worktree: `/Users/sebastiancarrasco/hackaton-aws/.worktrees/chatbot-desplegado`

## Resumen

| Check | Estado |
|---|---|
| Credenciales AWS perfil `hackaton` | **FALLO** (token expirado) |
| Modelos Bedrock en `us-east-1` | **FALLO** (no se pudo listar, bloqueado por credenciales) |
| Dataset `perfiles.json` | OK · 1.7 MB · cabe en el bundle |

## 1. `scripts/check-env.sh`

Herramientas:

- ✓ git 2.50.1
- ✓ uv 0.12.3
- ✓ python3 3.9.6 (ojo: `.python-version` del repo pide 3.12; el `python3` del PATH es el del sistema. `uv` resuelve el 3.12 del proyecto, así que no bloquea.)
- ✓ node v26.0.0
- ✓ aws-cli 2.38.0
- ✗ `cdk` no instalado globalmente → **no hace falta instalarlo.** El flujo
  documentado en `infra/README.md` es `npx cdk ...`, que resuelve el paquete en
  el momento. No correr `npm i -g aws-cdk`.
- ✗ `claude` no instalado (opcional)
- ✗ `codex` no instalado (opcional)

AWS: ✗ sin credenciales válidas.

## 2. Credenciales y Bedrock

```
$ aws sts get-caller-identity --profile hackaton
An error occurred (ExpiredToken) when calling the GetCallerIdentity operation:
The security token included in the request is expired
```

```
$ aws bedrock list-foundation-models --region us-east-1 --profile hackaton
An error occurred (ExpiredTokenException) when calling the ListFoundationModels operation:
The security token included in the request is expired
```

No se pudo verificar la disponibilidad de los modelos requeridos
(`us.anthropic.claude-sonnet-5`, `us.anthropic.claude-opus-5`,
`us.anthropic.claude-haiku-4-5`).

### Diagnóstico

El perfil `hackaton` usa credenciales estáticas temporales en
`~/.aws/credentials` (access key + secret + `aws_session_token`), con
`region = us-east-1` en `~/.aws/config`. No hay configuración SSO para ese
perfil, por lo que **no se puede refrescar automáticamente** con
`aws sso login`. Hay un directorio `~/.aws/sso/` pero el perfil no lo
referencia.

### Acción requerida del usuario

Volver a pegar credenciales frescas de la cuenta de la hackatón en el bloque
`[hackaton]` de `~/.aws/credentials` (las tres claves, incluido
`aws_session_token`), o bien configurar el perfil vía SSO. Después repetir:

```bash
aws sts get-caller-identity --profile hackaton
aws bedrock list-foundation-models --region us-east-1 --profile hackaton \
  --query "modelSummaries[?contains(modelId,'claude')].modelId" --output table
```

## 3. Dataset

```
data/raw/dataset_A_participantes/perfiles.json → 1 699 557 bytes (~1.7 MB)
data/raw/ completo                             → 2.0 MB
```

**Cabe en el bundle sin problema.** Muy por debajo del límite de Lambda
(50 MB comprimido / 250 MB descomprimido), así que no hace falta S3 ni
inyectar `ProfileRepository(dataset_path=...)` apuntando a un objeto remoto
por razones de tamaño. Se puede empaquetar junto al código.

Nota: si más adelante el dataset se reemplaza por el set completo (no el de
participantes) habría que revisar esto de nuevo.

## 4. Qué NO está bloqueado por credenciales

`cdk synth` **no necesita credenciales.** `infra/app.py` instancia el stack con
`cdk.Environment(region="us-east-1")` sin `account`, así que el stack es
environment-agnostic y sintetiza sin llamar a AWS. Verificado leyendo
`infra/app.py`.

Consecuencia práctica: el riesgo técnico más grande del plan (el empaquetado
del binario nativo de `pydantic` para Lambda) se puede de-riesgar ahora mismo,
sin credenciales. Por eso T15 se parte en dos.

Tampoco necesitan AWS:

- **T15a** — escribir `infra/chat_stack.py`, registrarlo en `infra/app.py`,
  agregar los grupos `api` y `eval` a `pyproject.toml` + `uv lock`, validar el
  cross-build del bundle y `npx cdk synth ChileAtiendeChat`.
- **T16** — `moto[dynamodb]`.
- **T17 / T18** — `ScriptedClient` falso de `tests/test_agent.py` + moto.
- **T19** — `phoenix serve` es local; el `BedrockInstrumentor` se comprueba con
  el cliente falso inyectado (spans del turno y del tool-use).
- **T20** — se escribe completa con el marker `eval`; solo la ejecución del
  juez necesita Bedrock real.

## 5. Pendiente de credenciales (para que T21 lo recoja)

| Ítem | Tarea | Qué falta |
|---|---|---|
| Verificar modelos Bedrock en `us-east-1` | preflight | `aws bedrock list-foundation-models` y confirmar `us.anthropic.claude-sonnet-5`, `us.anthropic.claude-opus-5`, `us.anthropic.claude-haiku-4-5` |
| `npx cdk bootstrap` | T15b | requiere cuenta real |
| `npx cdk deploy ChileAtiendeChat --profile hackaton` | T15b | requiere cuenta real |
| Verificación `curl` de `/health` | T15b | 200 con API key, 401/403 sin ella |
| Correr el scorecard de DeepEval con juez Bedrock | T20 | tests con marker `eval` |
| Ver una traza en Phoenix originada desde la Lambda desplegada | T19 | depende de T15b |

En cuanto el usuario renueve las credenciales del perfil `hackaton`, se retoma
T15b y luego la ejecución de T20 y la traza remota de T19.
