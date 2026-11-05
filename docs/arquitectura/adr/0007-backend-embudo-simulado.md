---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# ADR 0007 — Backend persistente del embudo y demo con reloj simulado

## Contexto
El usuario pidió revisar sus pendientes e implementar el backend del embudo con una prueba visual local. board-clemente y [contacto-y-campanas](../contacto-y-campanas.md) definen email → llamada → trabajo → presencial, escalando si **no inició el trámite**, no por falta de apertura/respuesta. El dataset no contiene contactos ni territorio.

## Decisión
1. Motor `Funnel` en `src/app/ruta/colador.py`, sin Streamlit ni LLM. Reutiliza detección de `reglas.py` y SQLite del aporte de Johann: tablas `funnel_clock`, `funnel_people`, `funnel_events`, más historial en `eventos` del caso existente.
2. Una fila por RUN y transacciones de escritura serializadas. Inicialización idempotente, semilla/fecha inicial fijas por base, reloj explícito y simulación determinista por RUN/etapa/intento, independiente del tamaño de los avances.
3. Capa sintética separada, reproducible y rotulada. Sin transportes reales, llamadas AWS ni dependencia de que la web esté abierta.
4. La etapa presencial queda en cola; no se simula una visita realizada ni una resolución institucional. Rechazar detiene todo y revoca permiso previo en el caso de demo; iniciar detiene el colador sin otorgar autorización de lectura.
5. El inicio explícito, o completar G1 (solicitud PGU) / J2 (solicitud de pensión) en el caso, detiene el seguimiento. Aceptar invitación, autorizar, abrir o contestar no equivalen al inicio. Son convenciones de integración del MVP, no comprobación de presentación en un organismo.
6. Una UI consume el mismo backend tanto en Detectar e invitar como en `demo_embudo.py`. La demo independiente usa una base separada; una nueva simulación conserva la anterior.

## Consecuencias
Plazos/probabilidades son hipótesis de demostración y están documentados. No se implementan aún transportes, heatmap, `alertas.py` ni CESFAM. El esquema se mantiene junto al aporte de Johann; la unificación con `Case`/contratos del agente sigue pendiente. Guía y evidencia en [backend-embudo-contacto](../backend-embudo-contacto.md).
