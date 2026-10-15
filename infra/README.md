# Infra · Detección proactiva de beneficios

Stack CDK `ChileAtiendeProactivo` (us-east-1). Diseño en [[deteccion-proactiva-aws]].

## Desplegar
```powershell
cd infra
uv sync --group infra
npx cdk bootstrap --profile hackaton      # una vez por cuenta/región
npx cdk deploy --profile hackaton
```
- Al desplegar, SES envía un correo de verificación a `curibeo@utem.cl`: **hay que hacer clic en el enlace** antes de que lleguen los emails.
- Otro correo: `npx cdk deploy -c email=otra@casilla.cl`. Esperas de demo: `-c espera_email_min=2 -c espera_sms_min=2`.
- Si la cuenta no permite crear roles IAM: `-c lambda_role_arn=arn:aws:iam::<cuenta>:role/<rol>` (el rol necesita DynamoDB y `ses:SendEmail`).

## Cargar datos
```powershell
uv run python scripts/proactivo.py cargar             # 8 beneficios + 6 personas demo + 500 del dataset A
uv run python scripts/proactivo.py cargar --solo-demo # solo las personas demo
uv run python scripts/proactivo.py resumen
```
La carga del dataset abre unos 620 contactos simulados (`@example.com`, nunca se envían). En ~10 minutos el escalador los pasa a SMS simulado y luego a terreno.

## Guion de la demo
| Evento | Comando | Beneficio detectado |
|---|---|---|
| Cumple 65 | `evento 90000002-2 --edad 65` | PGU |
| Cumple 18 | `evento 90000001-4 --edad 18` | Subsidio al Empleo Joven |
| Tiene un hijo | `evento 90000003-0 --hijos 1` | Subsidio Único Familiar |
| Se casa | `evento 90000004-9 --estado-civil casado` | Asignación familiar por cónyuge |
| Accidente laboral | `evento 90000005-7 --accidente` | Seguro laboral Ley 16.744 |
| Baja su tramo RSH | `evento 90000006-5 --tramo 70` | Subsidio Eléctrico |

Todos con `uv run python scripts/proactivo.py ...`. También se puede editar el ítem directamente en la consola de DynamoDB (tabla `ca-personas`, campo `fecha_nacimiento`, `num_hijos`, etc.): el stream dispara la misma detección.

Luego:
1. Llega el email con «Sí, quiero ayuda» / «No me interesa» / «Ver detalle».
2. `estado <run>` muestra el contacto (`email_enviado`, `email_abierto`, `email_click`, `sms_enviado`, `respuesta`) y el historial.
3. Sin respuesta: a los 5 min pasa a SMS simulado y a los 10 min a `terreno`. `terreno` lista al equipo de visita por comuna.
4. Respuesta del equipo o del call center: `responder <run> <beneficio> acepto --canal terreno`.
5. `escalar` y `revisar` ejecutan ahora el escalador y la revisión diaria (anticipación por edad).

## Tablas
| Tabla | Clave | Contenido |
|---|---|---|
| `ca-personas` | `run` | Atributos que leen las reglas; stream NEW_AND_OLD_IMAGES |
| `ca-beneficios` | `beneficio_id` | Catálogo con requisitos como datos |
| `ca-contactos` | `run` + `beneficio_id` | Estado del contacto, canales y respuesta; índices `cola-siguiente` y `estado-detectado` |
| `ca-historial` | `run` + `sk` | Bitácora de cada evento |

## Borrar
`npx cdk destroy --profile hackaton` (las tablas se eliminan con sus datos).
