---
tipo: verificacion
fecha: 2026-10-15
estado: en curso
---
# Verificación de los últimos pushes

Solicitud: actualizar el checkout y verificar el funcionamiento integrado. Se incorpora `origin/main` (`ad7efb0`) mediante fast-forward sobre `jp/ajustes-frontend`; sus aportes anteriores ya estaban integrados por el PR #3. No hubo conflictos ni duplicaciones nuevas en los módulos modificados.

La base oficial de [[portal-ayuda-tramites]] ahora determina la referencia del chat general. Dos pruebas seguían exigiendo la URL fija anterior de PGU. Se actualizan con un contexto público controlado y una URL de Ventanilla Única Social, conservando las comprobaciones de privacidad y entrega progresiva. La verificación independiente del catálogo mantiene sus casos de recuperación, extracción, citas y cambio de tema.

El script `scripts/verificar_chat_scroll.py` se adapta al placeholder vigente, el selector «Vista» y la interfaz de streaming. Inicia Streamlit con el mismo intérprete y limita su servidor a localhost. La respuesta larga demorada es sintética; la salida se acelera únicamente dentro del harness para verificar envío, espera, scroll automático y lectura manual sin llamadas al modelo.

## Resultados

- Suite completa, incluyendo infraestructura CDK y trazas: **282 pruebas pasan**, ocho evals reales excluidas y ninguna prueba omitida. Permanece una advertencia de deprecación de Altair/Streamlit.
- `src/app/verificar.py`: **TODO OK** en los 500 perfiles, autorización, rutas y respuestas de plantilla.
- `src/app/verify_knowledge.py`: **15 comprobaciones pasan** con BeautifulSoup instalado temporalmente; corpus de 808 documentos.
- Ruff de los tres archivos Python modificados: OK. `git diff --check`: OK.
- Ruff global: 184 observaciones heredadas, principalmente líneas largas, imports y dos lambdas; sigue pendiente la limpieza de estilo del [[board-clemente]].
- Navegador: comprobación en curso.

## Reproducir

Desde la raíz, con `uv` (en esta terminal se encuentra mediante `python3 -m uv`):

```sh
python3 -m uv sync --group app --group infra --group api
.venv/bin/python -m pytest
.venv/bin/python src/app/verificar.py
python3 -m uv run --group app --group infra --group api --with beautifulsoup4 --with playwright python src/app/verify_knowledge.py
python3 -m uv run --group app --group infra --group api --with beautifulsoup4 --with playwright python scripts/verificar_chat_scroll.py
```

El script de navegador requiere Chrome en la ruta macOS indicada en su cabecera. BeautifulSoup es una dependencia opcional del actualizador del corpus, documentada en [[contexto-chatbot-oficial]].

## Límite de esta revisión

Las comprobaciones son locales, con AWS simulado. Esta terminal no tiene perfiles AWS configurados (`boto3.Session().available_profiles` devuelve una lista vacía), por lo que no se comprueban los servicios desplegados ni Bedrock real. Las ocho evals quedan excluidas según la configuración normal del proyecto. No se ejecutan envíos de correo ni modificaciones en AWS.
