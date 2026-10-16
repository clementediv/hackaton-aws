# ChileAtiende a Tiempo · MVP Jubilación + PGU

Prototipo del desafío IPS/ChileAtiende: detecta hitos, invita, pide autorización, arma una ruta personalizada, acompaña con un asistente y mide el avance. La IA explica; las reglas están en código y AFP/IPS resuelven.

## Ejecutar con el entorno compartido (desde la raíz)
```powershell
uv sync --group app
uv run python src/app/verificar.py
uv run --group app streamlit run src/app/app.py --server.address localhost
```
El grupo `app` instala Streamlit y pandas con las versiones del aporte; boto3 usa el lock del repo. Las verificaciones son offline incluso con `BEDROCK_MODEL_ID` exportado. No instalar `requirements.txt` sobre el entorno compartido: fija otra versión de boto3.

## Alternativa autónoma (desde `src/app/`)
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python verificar.py        # chequeos sobre los 500 perfiles
.\.venv\Scripts\streamlit run app.py --server.address localhost
```
Lee `perfiles.json` desde `data/raw/dataset_A_participantes/` en la raíz del repo. Se puede cambiar con la variable `DATA_DIR`.

Mi Gobierno y Vista ejecutivo tienen accesos ficticios para demo local; no implementan identidad de producción. El consentimiento de antecedentes se solicita por separado. `--server.address localhost` limita el acceso a este equipo.

Para demostrar la autorización desde cero: ingresa a Mi Gobierno con `123456789` y `demo2026`. La cuenta ficticia «Persona De Prueba» solicita permiso en cada ingreso; no muestra resultados personales hasta activarlo. Ver [[perfil-demo-autorizacion]].

IA generativa (opcional): define `BEDROCK_MODEL_ID` (por ejemplo `us.anthropic.claude-sonnet-5`) junto con `AWS_PROFILE=hackaton` y `AWS_REGION=us-east-1`. Sin ella, el asistente responde con plantillas a partir del mismo contexto.

El chatbot consulta una base local de fuentes oficiales de Ventanilla Única Social, ChileAtiende y organismos relacionados. Recupera secciones pertinentes con URLs y fechas, conserva el tema para preguntas de seguimiento y mantiene la evaluación personal en código. Cobertura, actualización y verificaciones en [[contexto-chatbot-oficial]] (`knowledge/contexto-chatbot-oficial.md`).

## Vistas

- **Inicio:** portada inspirada en ChileAtiende con estilos, fuentes e imágenes locales, banner de beneficios/asistente y navegación. Los destacados no se actualizan automáticamente. Animaciones con alternativa de movimiento reducido. Ver [[portada-chileatiende]].
- **Asistente de IA (`/chat`):** conversación desde la pestaña o el banner, historial y reinicio. Orientación general con fuentes, Bedrock opcional y respaldo local. La consulta personal PGU requiere sesión y consentimiento; el historial personal se separa del público. Texto progresivo, espera animada y dictado revisable/lectura opcional mediante el navegador. Ver [[portal-ayuda-tramites]].
- **Mi Gobierno:** acceso con el RUN sintético mostrado y clave ficticia `demo2026`. Beneficios y Datos personales reúnen consentimiento, identidad, documentos, evaluación PGU, etapas, progreso declarado y asistente. No se presenta ni se cobra un beneficio desde la demo; el organismo resuelve. Becas y otros apoyos todavía no tienen evaluación personal integrada. Los accesos antiguos de ayuda llevan aquí. Ver [[mi-gobierno]].
- **Vista ejecutivo:** acceso de demo separado, con credenciales visibles en el formulario. Reúne seguimiento, mapa de campañas, detección/invitaciones, ficha, atención, trazabilidad y medición. Un contacto o inicio no equivale al KPI de próximo paso válido en plazo, que sigue pendiente de instrumentación. Ver [[portal-ejecutivos]], [[ficha-beneficiario]] y [[trazabilidad-casos]].
- **Contactos AWS:** herramienta del ejecutivo para leer `ca-contactos` y `ca-historial`; también alimenta la ficha. Consulta en solo lectura con las credenciales configuradas y muestra un aviso si faltan o vencen. No sincroniza todavía los cambios de SQLite con DynamoDB. Ver [[deteccion-proactiva-aws]].
- **Laboratorio de embudo:** `uv run --group app streamlit run src/app/demo_embudo.py --server.port 8502 --server.address localhost`. CLI: `uv run python scripts/colador_backend.py --db src/app/funnel-demo.db init --simulate` y `advance --days 7 --simulate`. Este laboratorio no hace envíos reales; el flujo SES pertenece al stack AWS separado. Ver [[backend-embudo-contacto]].

## Estructura
| Archivo | Rol (paso del PPT) |
|---|---|
| `ruta/config.py` | Parámetros PGU y edades legales, con fuente |
| `ruta/reglas.py` | Hitos, orientación PGU y jubilación, segmento de campaña (Detectar) |
| `ruta/rutas.py` | Pasos con dependencias y fechas (Preparar la ruta) |
| `ruta/casos.py` | SQLite: invitación, autorización, pasos, historial por canal (Acompañar) |
| `ruta/asistente.py` | Mensaje de invitación y explicación; Bedrock o plantillas (Invitar / Acompañar) |
| `ui_persona.py` | Interfaz ciudadana |
| `app.py` | Navegación y vistas ejecutivo, campaña y medición |

## Resultados PGU (precedencia)
`excluido` (fallecido) → `ya_recibe` → `futuro` (>12 meses para los 65) → `no_elegible` → `antecedente_faltante` → `proximo` → `elegible`.
Un incumplimiento verificable pesa más que un antecedente faltante, porque conseguir el antecedente no cambiaría el resultado.

## Pendiente de integrar con el resto del repo
El motor de rutas y SQLite mantienen el aporte autónomo. El chatbot Bedrock ya usa `src/contracts/` y `src/agent/` mediante `ruta/chatbot.py`; la unificación de reglas/persistencia sigue pendiente. Para este agente compartido usar el entorno uv de la raíz. Los identificadores históricos siguen en español, a diferencia de la convención del repo.

Revisión de integración en [[revision-aporte-johann]]. `futuro` y `excluido` no pertenecen a `PguStatus` del contrato compartido; hace falta acordar su representación antes de conectar los motores. Los montos/fechas se calculan en código con los parámetros del prototipo, no constituyen adjudicación ni validación completa de la normativa.
# Campañas territoriales de la simulación

La demo de embudo (`http://localhost:8502`) y Detectar e invitar incluyen un mapa detallado de la Región Metropolitana, ranking comunal y propuesta de capacidad. Para probar: nueva simulación → Sin respuestas → inicializar → +19 días. Fondo urbano CARTO/OSM (internet), límites BCN y datos territoriales sintéticos, grupos mínimos de cinco por comuna y ningún despacho real. El laboratorio usa `funnel-demo-rm.db` y conserva la base anterior. Ver [[heatmap-campanas-simulado]].
