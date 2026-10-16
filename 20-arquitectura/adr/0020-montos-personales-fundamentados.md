---
tipo: adr
estado: aceptado
fecha: 2026-10-16
---
# 0020 — Montos personales limitados al contexto del motor

En [[auditoria-chatbot-final]], una inferencia mezcló el tope del snapshot público con el motor, pese a conservar el resultado preliminar. Para respuestas personales, `construir_contexto` entrega límites monetarios y fecha de referencia del motor. El prompt indica su prioridad frente al material público.

`_bedrock` comprueba las expresiones de moneda contra el contexto autorizado. Si aparece una cantidad ajena, descarta la respuesta y usa un resumen determinista de resultado, motivo, requisitos pendientes y próximo paso. No se inventan cálculos ni se cambia elegibilidad; el IPS resuelve. El respaldo no solicita permiso de nuevo ni se limita a definir la PGU.

La comprobación cubre pesos con símbolo $, CLP y «pesos»; no prueba corrección de todo el texto ni vigencia institucional de la configuración. Los números sin indicación de moneda y las explicaciones causales requieren evaluación adicional. Las consultas públicas siguen sujetas a fuentes y límites del prompt. Phoenix no se activa por esta decisión.
