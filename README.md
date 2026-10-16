# ChileAtiende a tiempo · Hackatón AWS 2026

Aplicación de orientación y acompañamiento de beneficios: Inicio, Mi Gobierno, Asistente de IA y portal del ejecutivo. Este repositorio también es un vault de Obsidian y el espacio compartido de trabajo del equipo.

La evaluación PGU y los hitos se calculan en Python; Bedrock explica con fuentes. La app local conserva casos y seguimiento en SQLite. Los stacks AWS de detección proactiva y API del chat usan DynamoDB, Lambda y otros servicios; su integración completa con la app sigue pendiente. Arquitectura y límites en [[arquitectura-chileatiende]].

## Ejecutar localmente

Desde la raíz, con Python 3.12 y `uv`:

```sh
uv sync --frozen --group app
uv run --group app streamlit run src/app/app.py --server.address 127.0.0.1 --server.port 8501
```

Abre <http://localhost:8501>. Mi Gobierno y Vista ejecutivo tienen accesos ficticios de demostración; las credenciales se muestran en sus pantallas. El consentimiento de antecedentes es independiente del ingreso. Guía de vistas y laboratorios en [src/app/README.md](src/app/README.md).

Bedrock es opcional para la app. Si falta `.env`, copia `.env.example` y completa perfil `hackaton`, región `us-east-1` y el modelo permitido; conserva un `.env` existente. Sin modelo configurado, el asistente ofrece respuestas locales con fuentes. No se requieren credenciales AWS para las comprobaciones locales.

En entornos donde `uv` está instalado como módulo y no aparece en el PATH, usa `python3 -m uv` en lugar de `uv`.

## Verificar la integración

```sh
uv sync --frozen --group app --group infra --group api
uv run --group app --group infra --group api pytest
uv run --group app python src/app/verificar.py
```

La suite normal excluye las evals que consumen Bedrock real. Los grupos `infra` y `api` permiten comprobar también CDK y trazas opcionales. Existe deuda de lint global: `uv run ruff check .` informa observaciones pendientes, no un cierre de calidad completo. Estado de la revisión en [[verificacion-proyecto-2026-10-16]].

## Componentes y documentación

| Ruta | Contenido |
|---|---|
| `src/app/` | Streamlit, motor PGU, casos SQLite, colador y campañas simuladas |
| `src/agent/`, `src/contracts/`, `src/tools/` | Agente Bedrock, contratos y consulta autorizada de perfiles |
| `src/proactivo/` | Detección por eventos, correos y seguimiento del contacto en AWS |
| `src/api/`, `src/cases/` | API del chat y persistencia de casos en DynamoDB |
| `infra/` | Stacks CDK; instrucciones en [infra/README.md](infra/README.md) |
| `20-arquitectura/presentacion-aws/` | Láminas SVG/PNG/HTML; guion en [[presentacion-servicios-aws]] |
| `35-roles/`, `40-bitacora/` | Boards, avances y registros del equipo |

## Trabajo compartido

La lista vigente está en los boards de `35-roles/`. Cada aporte se guarda en commit, se integra con `origin/main`, se revisan conflictos y duplicaciones, se ejecutan verificaciones y se hace push. Se permiten aportes superpuestos, según [[AGENTS]]. Obsidian puede abrir esta carpeta como vault.
