---
tipo: adr
estado: aceptada
fecha: 2026-10-15
---
# 0015 · Orientación general sin consultar el perfil

## Contexto
Al preguntar qué es la PGU sin consentimiento, el chat devolvía siempre el resumen
personal de fechas. El guard de autorización se ejecutaba antes de identificar la
consulta general. [[portal-ayuda-tramites]] y [[chatbot-desplegado]].

## Decisión
Permitir preguntas generales sobre PGU, AFP, RSH y SCOMP sin consultar antecedentes.
Con Bedrock configurado, answer_general recibe únicamente la pregunta actual,
instrucciones y hechos públicos con sus fuentes. No recibe Case, RUN, nombre,
contexto personal, herramientas ni historial previo, incluso después de revocar.
Las consultas personales conservan el permiso obligatorio y el adaptador autorizado.
El respaldo offline clasifica consultas antes del guard y evita repetir la biografía.

## Consecuencias
Se responde a la pregunta concreta incluso sin autorización. El modo general dentro de Mi Gobierno no
reenvía historial, para proteger conversaciones personales anteriores. El chat público
separado conserva únicamente su propio public_chat_history, sin datos del caso. No evalúa
montos, elegibilidad ni fechas individuales. Las reglas deterministas no cambian.
Se verifica con fakes, pruebas de no filtración y una llamada real a Sonnet 5.

La integración remota añadió responder_publico y /chat. Se conserva esa ruta y se
unifica su llamada en answer_general/BedrockClient, eliminando el cliente boto3
paralelo y temperature, que Sonnet 5 rechaza.
