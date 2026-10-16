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
- Reportería para municipalidades y ministerios: vista territorial y PDF automático descargable. Rama `codex/reporteria-institucional`. [[reporteria-institucional]].

## Por hacer
- Integrar Streamlit con la API cuando se amplíe el alcance; hoy conserva su adaptador local.
- Configurar endpoint/key Phoenix remoto si se habilita; Lambda queda cableada e inerte.

## Bloqueos
- Sin bloqueos locales actuales: suite de cierre con 256 pruebas pasando. Los cinco fallos UI registrados anteriormente son históricos.

## Hecho
- Desplazamiento automático al enviar/recibir y espera con puntos en ola en ambos chats. `df392ec`; Chromium 390/1440 px y 256 pruebas pasan. [[portal-ayuda-tramites]].
- Cortafuegos estándar y educado en ambos chats, con referencias naturales «Si quieres saber más, puedes revisar…». `7d90e9e`; 57 pruebas enfocadas pasan. [[portal-ayuda-tramites]].
- Conversación natural y memoria general aislada, dictado editable y voz sintética opcional en ambos chats. `7ba7c2f`, integración `5f78e6f`. 43 pruebas enfocadas y 235 de suite completa pasan. [[0017-conversacion-y-voz-del-navegador]].
- Elegibilidad personal en Mi Gobierno: «puedo tener yo la PGU?» reconocida, consentimiento con paso concreto y agente autorizado preservado. `78bfcf6`. [[portal-ayuda-tramites]].
- Consultas generales del chat corregidas; Bedrock público sin perfil y respaldo pertinente. Cliente unificado con /chat remoto. `33eed79`, integración `d8bde76`. [[0015-orientacion-general-sin-perfil]].
- [x] T15: API mínima autenticada y Bedrock real. `f9e7f6d`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T16: Repositorio de casos DynamoDB. `65224cf`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T17: Turnos persistentes y evaluación determinista. `c7599d7`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T18: Rutas HTTP y consentimiento. `25140a2`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T19: Phoenix local con Converse instrumentado. `03d99f0`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T20: Ocho evals DeepEval con juez Bedrock. `64b09ca`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
- [x] T21: Stack completo y continuidad de tres turnos verificada con AWS CLI. `a54d5df`, integrado a main en `df99c3b`. [[chatbot-desplegado]]
