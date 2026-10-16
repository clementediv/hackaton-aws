---
tipo: nota-personal
integrante: Clemente
fecha: 2026-10-16
---
# Pitch: preguntas probables y respuesta corta

**Idea en una línea:** la Ley 21.180 digitaliza trámites; nosotros hacemos que el Estado se adelante y avise antes de que la persona pierda un beneficio.

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué serverless? | Reacciona a eventos y se paga por uso; sin servidores prendidos, escala solo. |
| ¿Por qué Bedrock? | Los datos no salen de la cuenta del Estado; modelos top sin GPUs. |
| ¿Y si la IA se equivoca? | No decide: elegibilidad, montos y plazos salen de código con fuente; la IA solo explica. |
| ¿Por qué DynamoDB? | Todo es por RUN (ms a cualquier escala) y **Streams** avisa cada cambio: detecta «cumplió 65» al instante, sin revisar toda la base. |
| ¿Por qué no RDS / EC2? | No hay consultas complejas; ambos cobran ociosos y no avisan cuando cambia un dato. |
| ¿Lambda + EventBridge? | Lambda corre solo cuando pasa algo; EventBridge cubre el paso del tiempo (avisos por fecha) y el escalamiento email → SMS → terreno. |
| ¿Por qué SES? | Email barato con registro de envío, apertura y clic; en demo solo a casillas verificadas. |
| ¿Costo? | Pago por uso: sin actividad ≈ 0, crece con las personas atendidas. |
| ¿Seguridad? | Consentimiento previo, permisos mínimos, claves en Secrets Manager; el CESFAM solo ve «derivar». |
| ¿Ley 21.180? | No pedir lo que el Estado ya tiene, comunicación electrónica con registro, trazabilidad (expediente), canales equivalentes. |
| ¿Base legal / datos personales? | Finalidad clara + consentimiento revocable + «no me interesa» detiene todo (Ley 21.719). CESFAM y contacto laboral: base legal por validar. |
| ¿Qué falta para producción? | SES con dominio gob.cl, SMS real (SNS), unificar SQLite → DynamoDB. |

Verificar números de ley y plazos en bcn.cl antes de citarlos.
