---
tipo: diseño
fecha: 2026-10-16
estado: implementado
arquitectura: "[[arquitectura-chileatiende]]"
---
# KPI: próximo paso válido dentro del plazo (meta ≥75%)

Instrumenta la meta del usuario ([[0012-detener-contacto-confirmado]]) sobre el mismo registro de eventos que usa la trazabilidad ([[trazabilidad-casos]]). Contacto, apertura e «inicio» **no** la sustituyen.

## Definiciones
| Concepto | Regla en código (`src/app/ruta/kpi.py`) |
|---|---|
| **Cohorte** | Personas con contacto confirmado que **aceptaron**: `invitacion_aceptada` o respuesta en el colador (`colador_answered`, `colador_contacted`, `colador_started`). Si su última respuesta es un rechazo, salen de la cohorte. |
| **Inicio del plazo** | La primera aceptación posterior al último rechazo. |
| **Plazo** | **30 días** desde ese contacto. Es una propuesta de demo, no un plazo institucional. |
| **Paso válido** | Un paso de la ruta distinto de la lectura informativa G0, completado después del contacto: `paso_completado` (ejecutivo o persona) o `eligible_step_completed` con `possible = true` (Mi Gobierno). Un paso reabierto deja de contar. Es **declarado**: el organismo todavía no lo confirma. |
| **No cuentan** | Envío, apertura o clic de un mensaje, aceptar el acompañamiento, `colador_started` y `tramite_iniciado` por sí solos. |

## Estados por persona
- **En plazo:** dio el paso antes de vencer el plazo.
- **Fuera de plazo:** lo dio después.
- **Vencido:** el plazo pasó sin paso.
- **En curso:** sin paso, con el plazo vigente.

## Cálculo
- **KPI = en plazo ÷ cohorte con plazo cumplido** (personas cuyo plazo ya venció, hayan dado el paso o no). Contar solo los casos «cerrados» inflaría el resultado, porque los éxitos se cierran antes que los fracasos.
- Mientras nadie tenga el plazo cumplido, el KPI dice «Sin cohorte con plazo cumplido» y se muestra aparte un **avance provisional**: quienes ya dieron el paso en plazo sobre toda la cohorte. Es un mínimo, no el KPI.
- La fecha de referencia es la más reciente entre ahora y el reloj simulado del colador, para que los escenarios simulados se midan en su propio tiempo.

## Dónde se ve
- **Vista ejecutivo → Medición:** KPI con la meta, avance provisional y tabla por persona (contacto, plazo, paso, estado).
- **Trazabilidad:** la fila del KPI explica el plazo de demo y que falta la confirmación del organismo.

## Verificación
`tests/test_kpi.py`: aceptar no cuenta como paso; G0 no cuenta; paso en plazo, fuera de plazo y vencido; rechazo final saca de la cohorte; paso reabierto deja de contar; KPI sin cohorte cumplida; prueba de UI de Medición.
