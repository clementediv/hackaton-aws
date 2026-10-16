---
tipo: verificacion
fecha: 2026-10-15
estado: verificado localmente
---
# Verificación de los últimos pushes

Solicitud: actualizar el checkout y verificar el funcionamiento integrado. Se incorpora `origin/main` (`ad7efb0`) mediante fast-forward sobre `jp/ajustes-frontend`; sus aportes anteriores ya estaban integrados por el PR #3. Después llegan ajustes visuales hasta `4e4618c`: se integran mediante merge. Un conflicto en el script de navegador se resuelve conservando la alineación y compatibilidad Windows/macOS del remoto y las esperas, aislamiento y correcciones de scroll locales. No se agrega un segundo flujo de chat.

La base oficial de [[portal-ayuda-tramites]] ahora determina la referencia del chat general. Dos pruebas seguían exigiendo la URL fija anterior de PGU. Se actualizan con un contexto público controlado y una URL de Ventanilla Única Social, conservando las comprobaciones de privacidad y entrega progresiva. La verificación independiente del catálogo mantiene sus casos de recuperación, extracción, citas y cambio de tema.

El script `scripts/verificar_chat_scroll.py` se adapta al placeholder vigente y la interfaz de streaming; cada vista se inicia mediante query param para evitar carreras de navegación. Inicia Streamlit con el mismo intérprete y limita su servidor a localhost. La respuesta larga demorada es sintética; la salida se acelera únicamente dentro del harness para verificar alineación, envío, espera, scroll automático y lectura manual sin llamadas al modelo. Se conservan `--alignment-only` y la detección de Chrome en Windows/macOS.

## Resultados

- Suite completa, incluyendo infraestructura CDK y trazas: **282 pruebas pasan**, ocho evals reales excluidas y ninguna prueba omitida. Permanece una advertencia de deprecación de Altair/Streamlit.
- Tras los últimos ajustes visuales: **47 pruebas relacionadas pasan** (Mi Gobierno, chat público, privacidad, streaming e integración).
- `src/app/verificar.py`: **TODO OK** en los 500 perfiles, autorización, rutas y respuestas de plantilla.
- `src/app/verify_knowledge.py`: **15 comprobaciones pasan** con BeautifulSoup instalado temporalmente; corpus de 808 documentos.
- Ruff de los tres archivos Python modificados: OK. `git diff --check`: OK.
- Ruff global: 184 observaciones heredadas, principalmente líneas largas, imports y dos lambdas; sigue pendiente la limpieza de estilo del [[board-clemente]].
- Chrome: ambos chats a 390 y 1440 px pasan dos turnos, alineación con avatar, envío visible, espera animada, scroll automático y lectura manual posterior; sin excepciones de Streamlit.

Implementación de verificaciones: `f4dc140`, estabilización `2ffeca8`; integración final con el remoto: `8c3686b`.

Actualización de cierre: llegó también `5fc01c9` (animaciones de Mi Gobierno). Integrado conservando ambas entradas del board; 25 pruebas de las vistas afectadas pasan y `scripts/verificar_animaciones_gobierno.py` confirma 390/1440 px, movimiento normal/reducido y ausencia de transformaciones persistentes.

## Reproducir

Desde la raíz, con `uv` (en esta terminal se encuentra mediante `python3 -m uv`):

```sh
python3 -m uv sync --group app --group infra --group api
.venv/bin/python -m pytest
.venv/bin/python src/app/verificar.py
python3 -m uv run --group app --group infra --group api --with beautifulsoup4 --with playwright python src/app/verify_knowledge.py
python3 -m uv run --group app --group infra --group api --with beautifulsoup4 --with playwright python scripts/verificar_chat_scroll.py
```

El script de navegador detecta Chrome instalado en Windows/macOS; sin esa instalación requiere el Chromium de Playwright. BeautifulSoup es una dependencia opcional del actualizador del corpus, documentada en [[contexto-chatbot-oficial]].

## Límite de esta revisión

Las comprobaciones son locales, con AWS simulado. Esta terminal no tiene perfiles AWS configurados (`boto3.Session().available_profiles` devuelve una lista vacía), por lo que no se comprueban los servicios desplegados ni Bedrock real. Las ocho evals quedan excluidas según la configuración normal del proyecto. No se ejecutan envíos de correo ni modificaciones en AWS.
