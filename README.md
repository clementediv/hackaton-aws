# ChileAtiende a Tiempo — Equipo Bombazo

Prototipo presentado en AWS Breaking Barriers Chile 2026 (3er lugar). Orienta sobre beneficios y próximos pasos, detecta hitos y acompaña a las personas entre canales. La elegibilidad, los montos y los plazos se calculan en código; el asistente explica y cita fuentes.

Esta entrega contiene el código, infraestructura y datos sintéticos del prototipo. La preparación para producción y la integración institucional requieren trabajo adicional: [transferencia y brechas](docs/TRANSFERENCIA.md).

## Ejecutar localmente

Requisitos: Git, Python 3.12 y uv. Desde la raíz:

```powershell
uv sync --frozen --group app
Copy-Item .env.example .env  # solo si .env no existe
uv run --group app python src/app/verificar.py
uv run --group app streamlit run src/app/app.py --server.address localhost
```

La configuración de ejemplo desactiva la conexión proactiva a AWS (`CA_AWS=0`) y deja Bedrock sin configurar para la interfaz. El acceso ciudadano y profesional es simulado; usar únicamente los perfiles sintéticos y las claves de demo que muestra la aplicación. No ingresar credenciales institucionales.

## Entrega técnica

| Ruta | Contenido |
|---|---|
| `src/app/` | Interfaz Streamlit, reglas, acompañamiento y SQLite |
| `src/agent/`, `src/api/`, `src/contracts/`, `src/cases/`, `src/tools/` | Agente Bedrock, API y casos DynamoDB |
| `src/proactivo/` | Detección de hitos, contacto y escalamiento |
| `infra/` | Dos stacks AWS CDK; [instrucciones de despliegue](infra/README.md) |
| `data/` | Dataset A y contactos sintéticos necesarios para ejecutar y probar |
| `tests/`, `scripts/` | Pruebas y utilidades de operación/verificación |
| `docs/` | Arquitectura, decisiones y transferencia |

La base de conocimiento pública se conserva en `src/app/knowledge/`; sus fuentes, fechas y actualización se describen en [contexto del chatbot](src/app/knowledge/contexto-chatbot-oficial.md). No se actualiza automáticamente durante las consultas.

## Verificar

```powershell
uv sync --frozen --group app --group infra
uv run --group app --group infra pytest
uv run --group app python src/app/verificar.py
```

Las evaluaciones marcadas `eval` están excluidas por defecto; requieren Bedrock y consumen tokens. Los scripts de navegador requieren Playwright y una aplicación local en ejecución. Las pruebas de CDK necesitan Node.js.

Para la sesión con AWS: [arquitectura resumida, configuración y pendientes](docs/TRANSFERENCIA.md). Documentación funcional adicional: [app](src/app/README.md).

## Publicación y licencia

El repositorio es público. No se encontró un archivo LICENSE en la versión recibida: el equipo debe acordar e incorporar la licencia para formalizar las condiciones de reutilización del código. Los contenidos y marcas de terceros conservan sus condiciones de origen. Esta limpieza no cambia la licencia ni reescribe el historial de Git.
