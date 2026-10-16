---
tipo: demo
fecha: 2026-10-16
estado: ensayo local; M1 verificado por Claude
---
# Guion de demo · ChileAtiende a Tiempo

Objetivo: mostrar detección, contacto sin insistencia después de una respuesta y acompañamiento con continuidad. Duración: cinco minutos. Contexto: [[app-aws-conectada]], [[portal-ejecutivos]], [[trazabilidad-casos]], [[board-clemente]].

## Preparación

- Una pestaña de la app en http://localhost:8501 y otra del correo verificado. El laboratorio :8502 es apoyo, no una segunda app ciudadana.
- Hay dos accesos ejecutivos: **Para ejecutivos**, arriba, abre seguimiento/mapa/trazabilidad; para ficha, AWS, CESFAM y Medición, desplegar la barra lateral con la flecha de la esquina superior izquierda y pulsar **Vista ejecutivo**.
- Ejecutivo ficticio: `ejecutivo.rm@example.com` / `Ejecutivo2026!`. Ciudadano: un RUN del selector «Datos de demostración» / `demo2026`. Aceptar el acompañamiento y autorizar antecedentes son pasos separados.
- Usar solo PDF o imágenes ficticios al mostrar documentos. Preparar un archivo pequeño para «Cédula de identidad».
- Jorge Demo (`90000002-2`) está en AWS, pero **no está en los 500 perfiles locales**: no puede iniciar sesión en Mi Gobierno ni seleccionarse en su ficha local. Mientras no se integre, anunciar el cambio de persona para mostrar acompañamiento con un RUN del dataset. No presentar dos personas como un mismo caso.
- No reiniciar contactos de una persona real. El reinicio borra contactos e historial de la persona de demo seleccionada.

Comandos PowerShell desde la raíz:

```powershell
aws sts get-caller-identity --profile hackaton
aws ses list-identities --identity-type EmailAddress --profile hackaton --region us-east-1
```

Las credenciales temporales del evento vencen aproximadamente cada seis horas; confirmar su vigencia antes del ensayo. Revisar en SES que remitente y destinatario figuren verificados (en sandbox ambos deben estarlo). Para consultar el estado de una casilla:

```powershell
$demoEmail = Read-Host 'Casilla de demo verificada en SES'
aws ses get-identity-verification-attributes --identities $demoEmail --profile hackaton --region us-east-1
```

La preparación siguiente **escribe datos demo en AWS** y puede activar correos en las casillas habilitadas; coordinarla con M1 de Claude. Carga también el catálogo:

```powershell
uv run python scripts/proactivo.py cargar --solo-demo --email $demoEmail
uv run python scripts/proactivo.py resumen
```

Antes de iniciar otra app, revisar quién ocupa :8501; cerrar únicamente el proceso de la app anterior, conservando las demás herramientas:

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen | Select-Object LocalPort,OwningProcess
uv run --group app streamlit run src/app/app.py --server.port 8501 --server.headless true
```

Comprobación local reproducible:

```powershell
uv run --group app pytest -q
uv run --group app python src/app/verificar.py
```

## Recorrido de cinco minutos

| Tiempo | Qué hacer | Qué decir |
|---|---|---|
| 0:00–0:45 · a | Barra lateral → Vista ejecutivo → iniciar sesión → «Contactos AWS» → «Simular evento de vida». Seleccionar Jorge. Si se repite el ensayo, volver primero a 64 años, aplicar y esperar; reiniciar sus contactos; luego aplicar 65 años. | «Un cambio en sus datos activa reglas de código. Detectamos una oportunidad y enviamos una invitación; la IA no decide la elegibilidad». |
| 0:45–1:10 · b | Abrir el correo de Jorge y pulsar «Quiero orientación». Volver a Contactos AWS → Actualizar ahora; comprobar «Aceptó». | «Abrir no confirma contacto. Al responder, detenemos los siguientes canales y pasamos al acompañamiento». |
| 1:10–1:45 · c | Mostrar historial AWS de Jorge en Contactos AWS. Luego abrir «Ficha del beneficiario» y seleccionar el RUN local preparado para el resto del recorrido. | «Aquí se conserva lo ocurrido por canal. Para mostrar la ficha y los documentos usamos ahora otra persona sintética del dataset local». No afirmar que Jorge aparece en esa ficha. |
| 1:45–2:20 · d | En el portal ejecutivo, abrir «Campañas en terreno», fuente Demostración. Mostrar concentración, contorno propuesto y cantidad de personal. | «El equipo prioriza las zonas con personas sin contacto confirmado. La propuesta se calcula a partir del mapa y del personal disponible». Aclarar que direcciones y coordenadas son ficticias. |
| 2:20–3:10 · e | Mi Gobierno → RUN preparado / `demo2026` → aceptar y autorizar si corresponde. Mostrar aviso AWS solo si existe para ese mismo RUN. Datos personales → Documentos → adjuntar PDF ficticio. En ficha, «Marcar validado»; volver a Mi Gobierno y comprobar «Validado por ChileAtiende». | «La persona comparte un antecedente una sola vez. El ejecutivo registra la revisión y la persona puede verla. Esto no concede el beneficio ni cambia las reglas de elegibilidad». |
| 3:10–3:45 · f | Barra lateral → Vista ejecutivo → Punto CESFAM. Usar un RUN del ejemplo de alerta máxima. Consultarlo y pulsar «Derivar a ChileAtiende». Ir a Atención del caso → Derivaciones pendientes → Atender. | «El punto de salud solo ve que debe derivar. El ejecutivo recibe el resumen necesario para continuar». Usar una persona que siga sin respuesta: Jorge aceptó y no debe volver a escalar. Ver [[cesfam-derivacion]]. |
| 3:45–4:10 · g | Vista ejecutivo → Medición. Mostrar «Próximo paso dentro del plazo», avance provisional y tabla por persona. Si indica «Sin medir», mostrar que aún no hay cohorte cuyo plazo haya vencido. | «La meta es 75%. Esta implementación mide a quienes aceptaron y cuyo plazo de demo de 30 días ya venció; cuenta pasos declarados distintos de G0. No equivale todavía al KPI institucional sobre todas las personas invitadas ni a una confirmación del organismo». Ver [[kpi-proximo-paso]]. |
| 4:10–5:00 · h | Portal ejecutivo → Trazabilidad. Mostrar alerta → ingreso → condiciones → avance, luego reconexiones, vista del proceso y continuidad a 7/30 días. | «Distinguimos contacto de avance. También vemos si la persona vuelve y consulta su proceso. Los datos de esta pantalla de demostración son simulados; una visita o un inicio no prueban el KPI». |

Si Jorge ya tiene 65 años, volver a aplicar 65 puede no generar transición. Reiniciar contactos por sí solo no cambia su edad. Preparar el estado inicial antes de exponer.

## Plan B: AWS no responde

No esperar más de 20 segundos durante la exposición. Mostrar el aviso de indisponibilidad en Contactos AWS y pasar al recorrido local: ficha, mapa, documentos y trazabilidad. Explicar que los correos no se están enviando y que se está usando una simulación persistente en SQLite. No pulsar repetidamente «Aplicar evento».

Para ensayar sin acceso a AWS, iniciar la app en una terminal dedicada:

```powershell
$env:CA_AWS = '0'
uv run --group app streamlit run src/app/app.py --server.port 8501 --server.headless true
```

Para volver al ensayo conectado, cerrar ese servidor, quitar la variable y reiniciar:

```powershell
Remove-Item Env:CA_AWS -ErrorAction SilentlyContinue
uv run --group app streamlit run src/app/app.py --server.port 8501 --server.headless true
```

## Criterio de cierre del ensayo

- [x] M1: Claude registra en el board (16-10, 13:16) casilla SES verificada, correo real, respuesta HTTP 200 y contacto aceptado. Codex no repitió el envío.
- [x] Recorrido Chromium :8501 con ficha, carga de PDF ficticio, validación por ejecutivo, estado compartido en Mi Gobierno, mapa y trazabilidad; sin excepciones visibles.
- [x] M2–M4: CESFAM, derivación y Medición incorporados al guion y ensayados. RUN `100000002-3`: derivado y atendido; Medición muestra «Sin medir» por falta de cohorte con plazo cumplido.
- [ ] Si se quiere una única persona de punta a punta: resolver el acceso local de Jorge con Claude; mientras tanto se declara el cambio de persona.

Ensayo verificado por tramos: AWS/correo por Claude (M1), recorrido local por Codex. No se ha ensayado con una única persona desde el correo hasta Mi Gobierno: el guion declara el cambio de persona. La meta ≥75% requiere el próximo paso válido y evidencia dentro de su plazo; no se sustituye por contactos, clics ni aperturas.

Validación integrada final: 340 pruebas aprobadas, una omitida por dependencia opcional de trazas y ocho evaluaciones Bedrock excluidas. Verificador de los 500 perfiles: TODO OK. Laboratorio :8502 conserva ambos escenarios; guardar su cambio local sigue pendiente de la confirmación solicitada en C1.

## Entrega técnica C2–C4

- `normalize_run` admite el RUN sin guion y espacios, conserva validación del dígito verificador y rechazo de formatos malformados. No se acopla la herramienta de perfiles a la UI de acceso.
- El prompt exige una evaluación de herramientas antes de explicar requisitos o montos, y pide identificar si falta perfil, autorización o herramienta.
- Los documentos guardan `validated_by` y `validated_at`. La migración agrega columnas sin borrar adjuntos; los antiguos aparecen como recibidos. El ejecutivo de la sesión valida desde la ficha; el historial conserva el evento y el hash del archivo. Reemplazar elimina la validación anterior, borrar vuelve a pendiente, revocar impide consultar/validar. Nada de esto cambia elegibilidad ni completa automáticamente un paso.
- Verificación reproducible: `uv run --group app pytest tests/test_profiles.py tests/test_prompts.py tests/test_document_review.py tests/test_government.py tests/test_ficha.py -q`.
