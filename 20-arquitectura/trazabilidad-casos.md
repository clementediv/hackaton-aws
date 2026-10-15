---
tipo: diseño
estado: implementado
fecha: 2026-10-15
---
# Trazabilidad de casos (portal de ejecutivos)

Vista visual del recorrido **alerta → ingreso → condiciones → avance declarado en un trámite disponible**, más continuidad de uso y reconexiones. Decisión: [[0018-trazabilidad-de-uso]]. La meta ≥75% en plazo sigue pendiente de validación; una visita o un avance declarado no acreditan una solicitud presentada o aprobada.

**Qué sí se demuestra:** que cada caso deja un rastro auditable (cuándo, por qué canal, qué ocurrió y de qué fuente), suficiente para medir el indicador en un piloto y para que ningún caso pierda su seguimiento.

## Dónde está
Pestaña **Trazabilidad** de [[portal-ejecutivos]]: `ui_trazabilidad.py` presenta los cálculos de `ruta/engagement.py`, sobre `eventos` cargados por `ruta/trazabilidad.py`. AWS se consulta solo al solicitarlo en la auditoría individual; sus eventos no se mezclan con las cifras de esta cohorte local.

## Qué muestra
| Sección | Contenido |
|---|---|
| Recorrido en cuatro hitos | Personas únicas por etapa, en orden temporal, y porcentaje sobre alertadas |
| Continuidad | Personas con dos o más sesiones, mediana del último intervalo entre ingresos, vistas del proceso e inactividad de siete días |
| Gráfico diario | Personas únicas que ingresaron por día, últimos 14 días, calendario de Santiago |
| Regreso durante 7/30 días | Reingreso dentro de esa ventana desde el primer acceso; solo cohortes con observación completa. No es retención exacta en el día 7/30 |
| Recorrido individual | Hitos con fecha/hora, sesiones, último ingreso, última consulta y secuencia de accesos |
| Detalle desplegable | Continuidad por persona, auditoría local/AWS y descarga CSV |

## Qué se registra

Mi Gobierno registra `platform_login` con sesión única, `platform_logout`, `process_viewed` al abrir o volver a Beneficios/ruta tras autorizar, y `eligible_step_completed` desde su control existente de pasos. Se conserva `autorizacion_otorgada` como evidencia de condiciones. No guarda claves ni copia RSH/pensiones en esta telemetría. El reinicio local borra sus claves de deduplicación.

La alerta es la primera detección/entrada al colador, señal o invitación: no demuestra entrega de email. El ingreso debe ser posterior a esa alerta, la autorización posterior al ingreso y el avance posterior a condiciones, de un beneficio disponible según código y distinto de G0. La aceptación es evidencia histórica; no sustituye el permiso vigente.

Abrir correo, responder una llamada o tener estado `started` en el colador no acredita ingresar o realizar un trámite. Las recargas no suman sesiones ni vistas; cambiar de sección y volver al proceso sí registra una vista. El intervalo es **entre inicios de sesión**, no tiempo exacto desconectado ni duración de lectura. Quienes declinaron no se incluyen en la tarjeta de posible acompañamiento por inactividad; no se reactiva el colador.

El botón «Cobrar beneficio» sigue retirado. Donde no exista un control de avance habilitado faltará esa evidencia; no se agrega una acción de cobro para producir métricas. Fechas nuevas UTC con zona; fechas locales históricas interpretadas como America/Santiago. Se excluyen eventos futuros respecto del reloj de la vista.

## Demostración aislada

Solo «Demostración · Región Metropolitana» agrega un escenario de uso ficticio e idempotente, marcado `simulated`, al abrir Trazabilidad en su base aislada. Ejemplo: 92 alertas → 73 ingresos → 54 autorizaciones observadas → 8 avances declarados; 37 personas regresan. El consentimiento ilustrativo no concede permisos reales del perfil.

«Casos de la aplicación» muestra lo registrado por Mi Gobierno y nunca recibe este escenario ficticio. Los perfiles sin alerta quedan fuera de la cohorte. Un historial sin eventos de login muestra ausencia de evidencia: no se reconstruye a partir de contactos.

## Qué falta para medir el KPI en un piloto
- **Plazo por trámite:** hoy se guarda la fecha del contacto y la del paso completado, pero no el plazo acordado para cada trámite.
- **Validez del paso:** el organismo debe confirmar que el paso registrado es válido (no basta con que la persona lo marque).
- **Denominador:** acordar la cohorte con el IPS; los porcentajes visuales sobre alertas no sustituyen el KPI validado.

La demo **valida registro y visualización, no cumplimiento de la meta con personas reales**. Pruebas en `tests/test_trazabilidad.py` y `tests/test_engagement.py`: orden temporal, duplicados, autorización previa, fechas futuras, G0/pasos no disponibles, ventanas completas, aislamiento y recorrido de login/vistas/reconexión. Chromium escritorio/móvil y verificador de 500 perfiles.
