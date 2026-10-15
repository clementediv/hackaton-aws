---
tipo: bitacora-integrante
integrante: Bruno
---
# Bitácora de Bruno

Una entrada por avance o commit relevante, la más reciente arriba.

Formato: `### AAAA-MM-DD HH:MM · <tema> · <commit corto>` y debajo qué se hizo, qué falta y si algo bloquea a otro integrante.

### 2026-10-14 · T22 · (sin commit)
Primer borrador de `20-arquitectura/ux-demo.md`: flujo de experiencia (diagrama Mermaid, 6 pasos del PPT con bifurcación "declina"), wireframes de la vista persona (invitación, autorización, ruta + checklist, chat) y del panel del ejecutivo (buscar RUN, motivos, ruta, hitos, checklist marcable, historial por canal). Incluye los 5 estados de `evaluar_pgu` (`elegible | no_elegible | antecedente_faltante | proximo | ya_recibe`), los estados de UI (cargando, error, declina, RUN no encontrado) y un JSON de caso como contrato mock provisional para T23/T24, más los 3 casos de demo para T28.

Decisiones tomadas: se usa a "Rosa" (persona del PPT) como ejemplo; montos/plazos siempre con `fuente_url` (regla de dominio). Falta: aprobación del equipo antes de las 21:00, confirmar hitos oficiales PGU (64a 9m / 65) y alinear la forma del mock con `src/contracts/` de Clemente cuando existan. No bloquea a nadie: T23/T24 arrancan con mock a partir de este documento.
