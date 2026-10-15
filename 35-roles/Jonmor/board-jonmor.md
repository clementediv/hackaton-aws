---
tipo: board
integrante: Jonmor
entorno: Kiro IDE Pro
---
# Board de Jonmor

| | |
|---|---|
| **Entorno** | Kiro IDE Pro |
| **Integración** | Commit del aporte → fetch/merge de `origin/main` → resolver y verificar → push |
| **Bitácora** | [[bitacora-jonmor]] |
| **Equipo y pipeline** | [[_equipo]] · [[_avance]] |

Lista de pendientes propia, sin tareas asignadas. Antes de elegir qué hacer, revisa el estado del pipeline en [[_equipo]] y los boards de los demás en [[_avance]] para no duplicar trabajo.

## En curso
- Sin tareas abiertas de T15–T21.

## Por hacer
- Integrar Streamlit con la API cuando se amplíe el alcance; hoy conserva su adaptador local.
- Configurar endpoint/key Phoenix remoto si se habilita; Lambda queda cableada e inerte.

## Bloqueos
- Cinco pruebas UI heredadas fallan también en origin/main; evidencia en [[chatbot-desplegado]]. No bloquean la API desplegada.

## Hecho
- [x] T15: API mínima autenticada y Bedrock real. `f9e7f6d`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T16: Repositorio de casos DynamoDB. `65224cf`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T17: Turnos persistentes y evaluación determinista. `c7599d7`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T18: Rutas HTTP y consentimiento. `25140a2`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T19: Phoenix local con Converse instrumentado. `03d99f0`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T20: Ocho evals DeepEval con juez Bedrock. `64b09ca`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T21: Stack completo y continuidad de tres turnos verificada con AWS CLI. `a54d5df`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
