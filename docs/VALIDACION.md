# Validación de la entrega

Revisión realizada el 4 de noviembre de 2026 sobre la rama `codex/entrega-aws`, basada en `fba4e26163aaba0fb8a35f1d4d7189a98fbc109a`.

- `uv sync --frozen --group app --group infra`: instalación correcta con Python 3.12.10 y `uv.lock`.
- `uv run --frozen --group app --group infra pytest`: 361 aprobadas, 1 omitida (instrumentación OpenInference no instalada), 8 evaluaciones con Bedrock excluidas por configuración. Una advertencia de deprecación de Altair.
- `uv run --frozen --group app python src/app/verificar.py`: todos los chequeos correctos sobre los 500 perfiles, reglas, rutas y asistente por plantillas.
- `cdk synth -c email=demo@example.com`: síntesis correcta de `ChileAtiendeProactivo` y `ChileAtiendeChat`, incluidos bundles Lambda Linux x86_64. CLI 2.1147.0; biblioteca Python fijada en el lock. La casilla es de ejemplo y no se desplegó.
- Ruff sobre los scripts operativos modificados y `infra/proactivo_stack.py`: sin observaciones.
- `git diff --cached --check`: correcto.
- Revisión de patrones de access keys AWS, tokens GitHub, claves privadas y correo personal retirado: sin coincidencias en los archivos de entrega. No es una auditoría exhaustiva ni un análisis del historial.

No se ejecutó despliegue, prueba contra la cuenta receptora, evaluación con Bedrock real ni revisión manual de navegador. Los tests de la app usan Streamlit AppTest y mocks. Las brechas institucionales y de producción están descritas en [TRANSFERENCIA.md](TRANSFERENCIA.md).
