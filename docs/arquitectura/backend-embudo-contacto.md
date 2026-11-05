---
tipo: implementacion
fecha: 2026-10-15
responsable: codex
---
# Backend del embudo de contacto

## Regla vigente: detener al contactar (corrección de Clemente)

[0012-detener-contacto-confirmado](adr/0012-detener-contacto-confirmado.md) sustituye el criterio anterior de esperar al inicio del trámite. Ahora **responder o aceptar detiene todos los canales posteriores**, aunque la persona todavía no haya iniciado. Enviar o abrir sin responder no confirma contacto. `active` = sin respuesta confirmada; `contacted` = contactado pendiente de trámite; `started` y `declined` se registran aparte. Una persona contactada puede luego iniciar o declinar; nunca se reactiva el escalamiento por seguir pendiente su trámite.

La aceptación en el caso compartido también detiene; G1/J2 o `tramite_iniciado` pueden convertir `contacted` en `started`. Ninguna respuesta simulada concede autorización. Respuestas históricas `answered` cancelan intentos futuros al leer/avanzar; se conserva el historial y no se finge que la nueva regla existía antes.

**Aclaración de la demo sin respuestas:** 500 perfiles analizados, 92 detectados; 77 personas con email, 85 con teléfono y 38 con empleador sintético. Hubo 77 emails, **255 intentos de llamada para 85 personas (3 cada una)** y 38 intentos laborales. Los demás canales se saltaron; los 92 quedan en cola presencial, con cero contactos confirmados. No hay 255 personas detectadas ni visitas ejecutadas.

La visual y JSON separan `reached` (incluye saltos), `attempted` (personas distintas con intento), `attempts` (intentos), `skipped`, `confirmed` y `active`. La barra representa personas con intento; el total de contactos confirmados incluye respuestas, aceptaciones y rechazos. Los estados disjuntos suman detectados: active + contacted + started + declined.

En localhost:8502 se puede elegir **Embudo con respuestas** (`funnel-demo-contacto-ejemplo.db`) o **Sin respuestas · mapa de campañas** (`funnel-demo-rm.db`); escenarios anteriores se conservan. En un clon sin bases locales, inicializar y avanzar el reloj. El control de respuestas afecta los próximos intentos y no reescribe el pasado. `FUNNEL_DEMO_DB` conserva el override para tests/escenarios propios.

Ejemplo nuevo con semilla 20261008 y 19 días: 92 detectados, 66 contactos confirmados (34 iniciaron, 23 contactados sin inicio, 9 declinaron), 26 sin contacto en presencial. Se detuvo a 25 en email; 67 pasaron a la etapa telefónica, con 60 personas que tenían teléfono y 131 intentos; 28 llegaron a trabajo (9 con empleador) y 26 quedan en presencial. No son KPI reales. Los datos históricos del apartado original debajo corresponden al modelo anterior.

La probabilidad por canal ahora representa respuesta; un sorteo independiente del 65% ilustra inicio posterior. Es hipótesis sin calibrar; no se ajusta para forzar una meta. **Meta del usuario: ≥75% de próximo paso válido dentro del plazo**. Ese KPI aparece «Sin medir» hasta instrumentar evidencia/paso/plazo; inicio/detectados se muestra solo como proxy.

Acciones del inspector: Abrió el correo (solo email activo), Confirmar contacto (detiene), Inició su trámite y Declinar (también disponibles desde contacted). CLI `respond --response answered` o `contacted` confirma respuesta. Regresiones: confirmar por email evita llamada/trabajo/presencial; contestar la primera llamada evita repeticiones; aceptar no inventa inicio; personas/intentos y reconciliación histórica comprobados.

Verificación vigente: **136 tests pasan** (10 nuevos), ruff check/format y verificador de 500 perfiles OK. El mapa/área siguen usando los mismos estados activos; se conserva el escenario sin respuestas para pruebas espaciales. El diseño y las cifras originales siguientes son registro previo a esta corrección.

Implementa los pendientes de colador en board-clemente y el diseño [contacto-y-campanas](contacto-y-campanas.md). Decisión en [0007-backend-embudo-simulado](adr/0007-backend-embudo-simulado.md).

## Verlo funcionar

Demo independiente en **http://localhost:8502**, con una base `src/app/funnel-demo.db` separada de los casos de la página. Para iniciarla:

```powershell
uv run --group app streamlit run src/app/demo_embudo.py --server.address localhost --server.port 8502
```

La pantalla permite inicializar, avanzar 1/5/7/19 días, simular respuestas o dejar a todos sin responder, inspeccionar un RUN, abrir/contestar, iniciar o declinar. Muestra embudo acumulado, pendientes actuales, intentos, personas por provincia sintética e historial. Se puede descargar el snapshot JSON y crear una simulación nueva sin borrar la anterior. `FUNNEL_DEMO_DB` cambia la base del laboratorio si hace falta.

Para observar todos los límites: nueva simulación → Sin respuestas → inicializar → +7 días (primera llamada) → +5 días (tres llamadas acumuladas, trabajo o salto si falta empleador) → +7 días (cola presencial). Abrir/contestar no detiene el reloj; iniciar o declinar sí. Si falta email/teléfono/empleador, el canal se salta inmediatamente y queda registrado.

En la página principal, entrar a los controles laterales → **Detectar e invitar**. El mismo componente consume el backend sobre `casos.db`; sus eventos se ven también en el historial del caso. El laboratorio independiente se recomienda para probar sin alterar los casos de la página.

## Backend sin web

```powershell
# Detectar candidatos, crear contactos ficticios si faltan e iniciar la campaña:
uv run python scripts/colador_backend.py --db src/app/funnel-demo.db init --simulate

# Ejecutar el trabajo pendiente hasta siete días más adelante:
uv run python scripts/colador_backend.py --db src/app/funnel-demo.db advance --days 7 --simulate

# Consultar sin avanzar el reloj:
uv run python scripts/colador_backend.py --db src/app/funnel-demo.db status

# Registrar una acción explícita en la demo (RUN de una persona del embudo):
uv run python scripts/colador_backend.py --db src/app/funnel-demo.db respond --run 100000010-4 --response started

# Exportar el estado completo a JSON:
uv run python scripts/colador_backend.py --db src/app/funnel-demo.db --output reports/embudo.json status
```

El script no necesita el grupo `app`: solo Python y las dependencias base. `--db` sin argumento usa el SQLite configurado en `CASOS_DB`/`casos.db`, compartido con el MVP. `init` admite `--seed`, `--date` y `--contacts`; fechas/semillas no se cambian silenciosamente en una campaña existente. Para otro escenario, usar otra base. Un archivo de contactos existente se conserva; `--seed` solo regenera los contactos si el archivo todavía no existe. El export no puede sobrescribir la base SQLite.

## Reglas exactas del embudo

| Etapa | Entrada y reloj | Fin / salto |
|---|---|---|
| Email | Intento simulado inmediato; espera 7 días | Sin email se salta; sin inicio escala al teléfono |
| Llamada | Intentos en días 0, 2 y 5 desde su entrada | Tras el tercero sin inicio pasa a trabajo; sin teléfono se salta |
| Trabajo | Intento simulado; espera 7 días | Solo con empleador ficticio; si no hay, se salta |
| Presencial | Cola de campaña, sin fecha automática | Espera una acción explícita; no finge haber visitado a la persona |

Estado `active`, `started` o `declined`. Una persona puede tener muchas señales pero una sola fila de seguimiento; nuevas señales se agregan sin repetir contactos ni reiniciar su reloj. Los ya fallecidos/no seleccionados por `diagnosticar` no ingresan. Una aceptación/autorización no se convierte automáticamente en «inició trámite».

El backend reconoce rechazo y progreso del caso compartido antes de avanzar o mostrar el estado. La finalización de pasos G1/J2 se interpreta como inicio en el MVP; no se afirma que hubo una presentación real ante IPS/AFP. La simulación no completa pasos ni concede autorizaciones. Un rechazo se refleja en el caso de demo y cancela el siguiente contacto; reejecutar inicialización no lo reactiva.

## Datos y simulación

`data/synthetic/contacto.csv`: 500 filas, semilla 20261008, marca `synthetic=True`, emails de ejemplo, teléfonos no marcables, empleadores ficticios y seis combinaciones territoriales ilustrativas. No se altera `data/raw/`. La selección viene del motor de reglas existente, sin modificar requisitos ni montos PGU.

La respuesta se deriva de SHA-256 de semilla/RUN/etapa/intento. Hipótesis **no calibradas**: rechazo 4% por intento; inicio 32% en email (descuenta 1,2 puntos por año sobre 65, piso 8%), 22% por llamada, 25% en trabajo. No se simula una visita presencial. Mismos contactos, semilla y operaciones producen el mismo resultado, incluso al avanzar 19 días de una vez o 7+5+7.

Ejemplo verificado con semilla 20261008: 92 candidatos; tras siete días simulados, 39 inicios, 8 rechazos y 45 activos (10 en cola presencial). **No son resultados reales ni KPI institucionales.** Las personas que no tienen ningún canal remoto pueden llegar a presencial desde el día inicial por saltos registrados.

## Archivos y persistencia
- `src/app/ruta/contacto.py`: generación y CSV; nunca sobrescribe archivos existentes.
- `src/app/ruta/colador.py`: reloj, estados, intentos, sincronización con el caso y snapshots.
- `scripts/colador_backend.py`: ejecución por lotes y exportación.
- `src/app/ui_embudo.py` / `demo_embudo.py`: prueba visual del mismo motor.
- SQLite: tablas propias + eventos en el historial de `casos.py`. Repetir un tick no reenvía contactos; reiniciar la demo desde Medición también limpia el embudo de esa base, para evitar referencias huérfanas. Las bases demo/journals están ignoradas por Git.

El mensaje laboral no menciona PGU, montos o RUN. Cada intento declara `simulated=True` y `delivered=False`. No existe un proveedor de envío detrás de estos registros.

## Evidencia y pendientes
Actualización: el heatmap y las propuestas de despliegue simulado ya están implementados en [heatmap-campanas-simulado](heatmap-campanas-simulado.md) (90 tests). El siguiente párrafo conserva la evidencia del aporte inicial del embudo; las campañas reales, alertas y CESFAM siguen pendientes.

`uv run --group app pytest`: **84 tests pasan**, incluidos CLI real, persistencia entre procesos, determinismo, límites temporales, casos sin canales, permisos/progreso, señales repetidas y recorrido de la UI. Ruff check/format OK en los módulos y tests nuevos. Verificador de 500 perfiles TODO OK; hay una advertencia de deprecación de Altair desde Streamlit, sin fallo funcional.

Vista comprobada con Chrome headless, gráfico y tablas renderizados sin excepciones. Quedan fuera de este aporte: heatmap, campañas físicas, `alertas.py`, punto CESFAM, envío real, scheduler AWS y validación institucional de las políticas. El campo `alert_level` del snapshot es solo la etapa activa (0 en terminales); no equivale al servicio de alertas/CESFAM pendiente.
