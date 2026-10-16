---
tipo: presentacion
fecha: 2026-10-16
referencia_codigo: 912b025
---
# Servicios AWS y recorrido actual de la página

Material para presentar [[arquitectura-chileatiende]], [[mi-gobierno]] y [[portal-ayuda-tramites]]. Basado en el código integrado hasta `912b025`; no implica una nueva validación del despliegue AWS.

## Diagramas para las diapositivas

Ambas láminas usan formato 16:9, 1920 × 1080. SVG permite editar o escalar y PNG permite insertar directamente en PowerPoint/Google Slides. HTML abre la misma lámina en el navegador.

- Arquitectura: [PNG](presentacion-aws/arquitectura-aws.png) · [SVG](presentacion-aws/arquitectura-aws.svg) · [HTML](presentacion-aws/arquitectura-aws.html).
- Recorrido de la página: [PNG](presentacion-aws/recorrido-pagina.png) · [SVG](presentacion-aws/recorrido-pagina.svg) · [HTML](presentacion-aws/recorrido-pagina.html).

## Qué cambió en la página

- **Inicio:** animaciones escalonadas y revelado de secciones; se respeta movimiento reducido.
- **Mi Gobierno:** pestañas Beneficios y Datos personales, con identidad, documentos, contacto, trabajo y salud. Las tarjetas y detalles de beneficios se presentan alineados y contenidos.
- **Ambos asistentes:** respuesta progresiva a 25 ms por palabra, sin cursor añadido; indicador de espera y alineación de avatar/texto. En Mi Gobierno, pregunta a la derecha y scroll limitado al historial.
- **Conversación:** ante insultos incluso con errores de escritura, se responde brevemente antes de buscar fuentes o invocar Bedrock; no se arrastra automáticamente el tema PGU. Las consultas reales con groserías mantienen su tratamiento normal.
- **Continuidad:** acceso de demo y consentimiento siguen separados; existen historial público y contexto personal autorizado. Dictado revisable y lectura opcional dependen del navegador.

Estos cambios afectan la experiencia de la página. Los stacks y conexiones AWS permanecen iguales respecto del esquema anterior.

## Arquitectura implementada

| Bloque | Flujo y responsabilidad |
|---|---|
| App local | Streamlit → adaptador Python → Bedrock Converse/ConverseStream → explicación con fuentes. SQLite guarda casos, documentos y seguimiento; JSON contiene las fuentes públicas. Hay respaldo local cuando Bedrock no está configurado o falla antes de entregar respuesta. |
| `ChileAtiendeProactivo` | DynamoDB personas/catalogo → Stream → Lambda detector → SES. EventBridge activa revisión diaria y escalamiento cada minuto; otras Lambdas registran respuesta y actualizan contactos/historial. La app consulta estos datos en solo lectura. |
| `ChileAtiendeChat` | API Gateway → Lambda con agente/evaluación determinista → Bedrock. Lambda guarda casos, consentimiento, evaluaciones y mensajes en DynamoDB. La API permanece separada del adaptador que usa el frontend local. |

| Servicio | Papel en el programa |
|---|---|
| Amazon Bedrock | Ejecuta Claude para explicar y acompañar; no decide elegibilidad. |
| AWS Lambda | Ejecuta detección, revisiones, escalamiento, registro de respuestas y API del chat. |
| Amazon DynamoDB + Streams | Guarda datos del flujo AWS y activa detección al agregar/modificar personas. |
| Amazon EventBridge | Programa la revisión diaria y el escalador. |
| Amazon SES | Envía emails reales solo a casillas verificadas/autorizadas; otros destinatarios se simulan. |
| Amazon API Gateway | Expone la API HTTPS del chat. |
| AWS Secrets Manager | Guarda claves de API y secretos de trazas. |
| IAM / CloudWatch | Definen permisos y registran logs. |
| CDK / CloudFormation | Definen y despliegan la infraestructura mediante código. |

## Guion breve para presentar

> La página ofrece orientación general y acompañamiento personal con autorización. Desde Inicio se accede al asistente o a Mi Gobierno, donde la persona revisa beneficios, documentos y etapas. Python calcula la evaluación preliminar de PGU y Amazon Bedrock genera explicaciones con fuentes. En paralelo, DynamoDB, Lambda y EventBridge detectan oportunidades y organizan el contacto; SES permite enviar correos. El ejecutivo consulta contactos y seguimiento. La IA explica; el organismo competente valida y resuelve.

## Límites que deben conservarse al presentar

- Frontend local y API desplegada todavía son recorridos separados. SQLite y DynamoDB no están completamente sincronizados.
- SMS, llamadas y visitas no constituyen transportes reales integrados. El flujo AWS email → SMS simulado → terreno y el colador local email → llamada → trabajo → presencial tienen implementaciones separadas.
- Abrir/enviar no confirma contacto. Aceptar/responder detiene el escalamiento; declinar detiene la insistencia. Aceptar contacto no concede por sí solo autorización para consultar antecedentes ampliados.
- Las cuentas son de demostración; la interfaz no implementa una identidad ciudadana/profesional de producción.
- Solo PGU tiene evaluación personal integrada en la app; mostrar otros beneficios no equivale a determinar su elegibilidad. El catálogo proactivo también conserva reglas de demo pendientes de validación institucional.
- No se afirma cumplimiento del KPI de próximo paso ≥75%; el progreso declarado y el contacto son medidas diferentes.

## Reproducir y comprobar

```sh
.venv/bin/python scripts/generar_presentacion_aws.py
python3 -m uv run --group app --group infra --group api --with playwright python scripts/generar_presentacion_aws.py --png
```

La exportación PNG necesita Chrome instalado en Windows/macOS o Chromium de Playwright. Comprueba que todo el texto entre dentro de la diapositiva. Verificación de integración: 305 pruebas pasan, ocho evals reales excluidas; el verificador determinista de 500 perfiles termina TODO OK. Los SVG también se revisan como XML y las láminas se inspeccionan visualmente.
