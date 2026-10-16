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

La app no tiene login: es para demo local. `--server.address localhost` evita exponerla en la red.

IA generativa (opcional): define `BEDROCK_MODEL_ID` (por ejemplo `us.anthropic.claude-sonnet-5`) junto con `AWS_PROFILE=hackaton` y `AWS_REGION=us-east-1`. Sin ella, el asistente responde con plantillas a partir del mismo contexto.

El chatbot consulta una base local de fuentes oficiales de Ventanilla Única Social, ChileAtiende y organismos relacionados. Recupera secciones pertinentes con URLs y fechas, conserva el tema para preguntas de seguimiento y mantiene la evaluación personal en código. Cobertura, actualización y verificaciones en [[contexto-chatbot-oficial]] (`knowledge/contexto-chatbot-oficial.md`).

## Vistas
- **Chat público (`/chat`)**: el banner de Inicio abre una conversación dedicada y conserva la primera pregunta. Permite seguir preguntando y comenzar una nueva conversación. Da orientación general sin consultar perfiles personales; usa Bedrock si está configurado y respuestas predefinidas con fuentes como alternativa. El historial dura la sesión. Verificación en navegador: enviar desde el banner, continuar con una segunda pregunta, abrir `/chat` directamente y volver a Inicio.
- **Contactos AWS** (Vista ejecutivo): lee en solo lectura lo que la detección proactiva desplegada en AWS detectó, envió y registró (`ca-contactos`, `ca-historial`), con métricas, filtros e historial por persona; la ficha del beneficiario muestra lo mismo para su RUN. Usa el perfil `hackaton` de `.env`; si las credenciales vencen, la vista lo avisa. Ver [[deteccion-proactiva-aws]].
- El acompañamiento ciudadano se concentra en **Mi Gobierno**: autorización, beneficios, ruta PGU con próximo paso destacado, avance guardado, historial y asistente junto a los pasos. La antigua sección de ayuda ya no aparece en la navegación; sus accesos llevan a Mi Gobierno. Ver [[mi-gobierno]].
- Acceso Mi Gobierno: usa el RUN sintético mostrado en la pantalla y la clave ficticia `demo2026`. No ingreses tu ClaveÚnica real. El acceso abre el perfil correspondiente y la autorización de antecedentes se concede por separado.
- **Vista ejecutivo**: entrada única para Mapa de calor y campañas, Detectar e invitar, Ficha del beneficiario, Atención del caso y Medición. El selector interno abre una herramienta a la vez. Ver [[ficha-beneficiario]].
- **Mi Gobierno**: espacio personal separado de Inicio, con consentimiento, identidad, situación económica, adjuntos locales y evaluación PGU. «Cobrar beneficio» abre la guía; el organismo resuelve y paga. Becas y otros apoyos aún no se evalúan. Ver [[mi-gobierno]].
- Portada: réplica visual basada en el HTML y los estilos públicos de ChileAtiende del 15-10-2026, con fuentes e imágenes locales. Abre en Inicio y conserva Ayuda para tus trámites / Mi ruta. Los destacados no se actualizan automáticamente. Ver [[portada-chileatiende]].
- Embudo de contacto: `uv run --group app streamlit run src/app/demo_embudo.py --server.port 8502 --server.address localhost`. Backend sin web: `uv run python scripts/colador_backend.py --db src/app/funnel-demo.db init --simulate` y `advance --days 7 --simulate`. Guía completa en [[backend-embudo-contacto]]. No se hacen envíos reales.
- Portal inspirado en `https://www.chileatiende.gob.cl/`: Inicio, Ayuda para tus trámites (entrada del MVP) y Mi ruta. Buscador y enlaces al portal oficial. Chatbot integrado con el agente compartido cuando se configura Bedrock; sin configuración responde por plantillas. Ver [[portal-ayuda-tramites]].
- **Ruta de la persona**: guía ciudadana paso a paso (invitación → autorización → tu situación → tu ruta) con asistente.
- **Vista ejecutivo**: el mismo caso con requisitos, fuentes e historial, para sucursal o call center.
- **Detectar e invitar**: segmentos sobre los 500 perfiles y campaña de invitación simulada.
- **Medición**: KPIs del PPT sobre los casos de la demo.

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
