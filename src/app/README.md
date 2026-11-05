# Aplicación Streamlit

Interfaz del prototipo ChileAtiende a Tiempo. Incluye Inicio y chat público, Mi Gobierno, ficha y atención de casos, campañas territoriales, contactos AWS, derivaciones CESFAM y medición. Los accesos ciudadano y profesional son ficticios y solo sirven para demostración con datos sintéticos.

Desde la raíz del repositorio:

```powershell
uv sync --frozen --group app
uv run --group app python src/app/verificar.py
uv run --group app streamlit run src/app/app.py --server.address localhost
```

Copiar `.env.example` a `.env` si no existe. Con `CA_AWS=0` se desactiva la conexión proactiva de la interfaz; con `BEDROCK_MODEL_ID` vacío, la interfaz usa plantillas. Para AWS, configurar credenciales del entorno y un modelo admitido por `src/agent/bedrock.py`. Los scripts CLI del agente y la API tienen su propia configuración: ver [transferencia](../../docs/TRANSFERENCIA.md).

El dataset por defecto está en `data/raw/dataset_A_participantes/`; `DATA_DIR` permite otro directorio con `perfiles.json`. `FECHA_REFERENCIA` mantiene la fecha de evaluación de la demo. SQLite guarda los casos locales y requiere un volumen persistente para hosting. No hay un despliegue de Streamlit incluido en los stacks CDK.

La elegibilidad, montos y fechas se calculan en código con parámetros del prototipo. El asistente explica y cita fuentes. La base pública del chatbot se conserva en `knowledge/`: [cobertura y actualización](knowledge/contexto-chatbot-oficial.md). Los adjuntos y el seguimiento local no constituyen una integración con los organismos.

La interfaz y la API de chat comparten componentes, pero sus motores y persistencias todavía requieren unificación. Los estados `futuro` y `excluido` de la app no tienen una representación idéntica en los contratos compartidos.

Para las campañas de demo:

```powershell
uv run --group app streamlit run src/app/demo_embudo.py --server.port 8502 --server.address localhost
```

Los contactos, ubicaciones y campañas son sintéticos. El envío de correo SES sí puede ser real cuando se habilita AWS y se verifican casillas; revisar [despliegue AWS](../../infra/README.md). Las pruebas automatizadas aíslan la conexión a AWS con mocks y `CA_AWS=0`.

Antes de una publicación institucional: resolver [las brechas de producción](../../docs/TRANSFERENCIA.md), incluyendo identidad, autorización, datos y persistencia.
