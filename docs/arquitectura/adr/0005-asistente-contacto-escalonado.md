---
tipo: adr
estado: aceptada
fecha: 2026-10-14
---
# ADR 0005 — Reestructuración: asistente ChileAtiende, contacto escalonado y acompañamiento completo

## Contexto
El MVP original ([0004-mvp-jubilacion-pgu](0004-mvp-jubilacion-pgu.md)) era un chat de orientación PGU más un panel de ejecutivo sobre el mismo caso. El equipo redefinió la idea central el 14-10: el problema no es solo orientar a quien llega, sino **llegar a quien no llega** y **acompañarlo hasta que el trámite quede en marcha**.

## Decisión
El producto tiene cuatro piezas sobre el mismo pipeline medular (detectar → invitar → autorizar → consultar → evaluar → preparar ruta → acompañar → derivar → seguir):

1. **Asistente frontal**: chatbot conversacional con la experiencia de la página de ChileAtiende. Guía a la persona en su trámite y es la cara visible del sistema.
2. **Contacto escalonado**: ante una alerta (hito próximo o beneficio posiblemente no cobrado), se contacta en este orden y **solo se pasa a la etapa siguiente si la persona no responde**:
   1. Email
   2. Llamada telefónica
   3. Contacto a través de su lugar de trabajo
   4. Campaña puerta a puerta
3. **Campañas dirigidas por heatmap**: la etapa puerta a puerta no es aleatoria. Se propone dónde ir según un mapa de calor de personas pendientes de contactar, para concentrar el esfuerzo donde hay más casos.
4. **Acompañamiento completo y back-office**: una vez contactada, el asistente acompaña a la persona en la recolección de documentos, le explica los pasos del trámite y la deriva al ejecutivo que lo pone en marcha. Ejecutivos y trabajadores sociales ven con claridad qué se recopiló del beneficiario y en qué estado están sus solicitudes.

Detalle en [contacto-y-campanas](../contacto-y-campanas.md) y [arquitectura-chileatiende](../arquitectura-chileatiende.md).

## Se mantiene
- Jubilación + PGU como primer caso de uso, con el datos-dataset-A.
- Reglas en código y fuentes citadas; `elegible` es orientación preliminar ([0003-orquestacion-agente](0003-orquestacion-agente.md), T02-contratos).
- Sin autorización no se consulta el perfil ampliado.

## Consecuencias
- **Brecha de datos**: el dataset A **no trae** email, teléfono, empleador, dirección ni comuna. Sin eso no hay escalera de contacto ni heatmap. Hay que pedir el dato a los mentores (¿dataset B?) o generar una capa sintética rotulada como tal. Ver [contacto-y-campanas](../contacto-y-campanas.md).
- **Privacidad**: el contacto laboral y el puerta a puerta exponen a la persona ante terceros. El mensaje no revela beneficios, montos ni datos personales; solo pide que la persona se comunique con ChileAtiende. Hay que validar la base legal con los mentores.
- **Una persona que declina detiene la escalera**: decir que no también es una respuesta, y se respeta.
- **Cambios de código**:
  - Los contratos (T02) necesitan canales y entidades nuevas: email, llamada, lugar de trabajo y terreno; intento de contacto; campaña; documento; estado de la solicitud; ejecutivo asignado.
  - El agente (T04) suma herramientas de documentos y de derivación al ejecutivo.
- **Reparto del equipo**: las tareas se redistribuyeron. `35-roles/` se actualizará cuando el equipo comparta el nuevo reparto.
- **Marca**: la experiencia se inspira en ChileAtiende, pero usar su logo e identidad visual requiere autorización de la institución. Confirmarlo con los mentores.
