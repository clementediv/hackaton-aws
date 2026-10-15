---
tipo: bitacora-integrante
integrante: Bruno
---
# Bitácora de Bruno

Una entrada por avance o commit relevante, la más reciente arriba.

Formato: `### AAAA-MM-DD HH:MM · <tema> · <commit corto>` y debajo qué se hizo, qué falta y si algo bloquea a otro integrante.

### 2026-10-15 · deteccion-elegibilidad-tramites · (sin commit)
Chequeo de solapamiento antes de empezar: traje `origin/main` (12 commits atrás, merge fast-forward sin conflictos). Los pendientes T23/T24/T26 de este board ya estaban cubiertos por otro trabajo: la vista de la persona y el panel del ejecutivo los construyó Johann (`ui_persona.py`, `ui_government.py`, `vista_ejecutivo`/`ui_ficha.py`), y la vista "a tiempo" quedó cubierta por el colador de contacto y el heatmap de Clemente. T25 (conectar ambas vistas a `GET /alertas`) quedó obsoleto: no hay API HTTP en el repo, todo es Streamlit en proceso sobre SQLite. T22/T27/T28 siguen sin tomar.

Me fui a backend: el agente de IA (`src/agent/*`, Bedrock Converse con tool use) nunca llega a evaluar elegibilidad porque `src/agent/tools.py` intenta importar `src.rules`, módulo que no existe en el repo. El puente de Streamlit (`src/app/ruta/chatbot.py`) compensa esa ausencia registrando una sola herramienta que devuelve un contexto ya precalculado por la UI: hoy el modelo parafrasea, no detecta.

Spec `deteccion-elegibilidad-tramites` (requirements-first):
- `requirements.md`: 12 requisitos en formato EARS, cada uno refinado con el detallador de requisitos. Cubren los 7 estados de PGU y los 6 de jubilación con su precedencia, la distinción entre no cumple / falta antecedente / pendiente por fecha, trazabilidad de fuente con URL y estado de verificación, el registro efectivo de las herramientas del agente, consentimiento y aislamiento por RUN, y degradación sin credenciales AWS.
- `design.md`: paquete nuevo `src/detection/` (`engine`, `adapter`, `catalog`, `alerts`, `batch`) que envuelve el motor de reglas vigente y el catálogo de 8 beneficios sin reimplementarlos. Resuelve los tres mecanismos pedidos: cómo corre la detección (un cálculo, tres consumidores: lote por línea de comandos, Streamlit cacheado y el agente), cómo se actualiza la interfaz (la caché de `diagnosticos()` no incluye hoy la fecha de referencia en su clave, así que nunca se invalida; se corrige pasándola como argumento) y cómo se dispara la alerta (separa la urgencia por detección de la dificultad de contacto, hoy colapsadas en `ficha.alert_level`; "nivel máximo" queda reservado para la conjunción de ambas, sin tocar el módulo de Clemente). Define 21 propiedades de corrección para validar con property-based testing (Hypothesis).

Fuera de git: contextualización del problema y la solución con Lean Canvas, en Drive.

Falta: generar `tasks.md`. Bloqueo de entorno — esta máquina no tiene Python ni `uv` instalados, así que nada de esto se ha ejecutado ni verificado todavía; el diseño se validó leyendo código y datos del dataset, no corriendo pruebas. No bloquea a nadie más del equipo.

### 2026-10-14 · T22 · (sin commit)
Primer borrador de `20-arquitectura/ux-demo.md`: flujo de experiencia (diagrama Mermaid, 6 pasos del PPT con bifurcación "declina"), wireframes de la vista persona (invitación, autorización, ruta + checklist, chat) y del panel del ejecutivo (buscar RUN, motivos, ruta, hitos, checklist marcable, historial por canal). Incluye los 5 estados de `evaluar_pgu` (`elegible | no_elegible | antecedente_faltante | proximo | ya_recibe`), los estados de UI (cargando, error, declina, RUN no encontrado) y un JSON de caso como contrato mock provisional para T23/T24, más los 3 casos de demo para T28.

Decisiones tomadas: se usa a "Rosa" (persona del PPT) como ejemplo; montos/plazos siempre con `fuente_url` (regla de dominio). Falta: aprobación del equipo antes de las 21:00, confirmar hitos oficiales PGU (64a 9m / 65) y alinear la forma del mock con `src/contracts/` de Clemente cuando existan. No bloquea a nadie: T23/T24 arrancan con mock a partir de este documento.