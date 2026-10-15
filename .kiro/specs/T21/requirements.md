# T21 · Despliegue completo

[[plan-chatbot-desplegado]]: bundle agrega cases y solo reglas/config/fechas de la
app, sin UI ni SQLite. Variables explícitas de datos, fecha, tabla, modelo y Phoenix.
Clave Phoenix en Secrets Manager: sustituir por una key real al configurar endpoint;
sin endpoint no se consulta el secreto ni se exporta. Assertions de seguridad/GSI/env.

Verificar auth, tres turnos HTTP y recarga real por CLI DynamoDB. Suite offline,
script 500 perfiles, synth y lint de archivos propios. No tocar Proactivo.
