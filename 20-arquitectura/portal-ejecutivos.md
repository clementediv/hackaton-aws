---
tipo: implementacion
fecha: 2026-10-15
estado: demo-local
---
# Portal para ejecutivos y asistentes sociales

Página de gestión accesible desde **Para ejecutivos** en el encabezado, o `/?vista=ejecutivos`. Reutiliza logo, fuentes, navegación, azules y tarjetas del frontend. El laboratorio técnico sigue en el acceso lateral «Vista ejecutivo». Diseño: [[0016-portal-ejecutivos]], [[contacto-y-campanas]], [[arquitectura-chileatiende]].

## Inicio de sesión de demostración

El botón «Para ejecutivos», el enlace directo y las herramientas laterales solicitan correo y clave antes de mostrar casos o mapa. Acceso ficticio, separado del ingreso y consentimiento de Mi Gobierno. Las cuentas aparecen en un desplegable en la misma pantalla:

| Persona ficticia | Perfil de demostración | Correo | Clave |
|---|---|---|---|
| Carolina Soto | Ejecutiva de atención | `ejecutivo.rm@example.com` | `Ejecutivo2026!` |
| Daniel Fuentes | Asistente social | `social.rm@example.com` | `Ejecutivo2026!` |

Ambas cuentas ven las mismas campañas; los perfiles solo identifican a la persona ficticia, sin permisos diferentes. Credenciales públicas de ejemplo, sin vinculación a funcionarios o cuentas institucionales. No reemplazan una autenticación profesional de producción.

Una clave incorrecta muestra error y limpia el formulario. «Cerrar sesión de ejecutivo» elimina la identidad y filtros del ejecutivo, sin borrar casos, campañas ni la sesión/historial ciudadano. Volver a la portada no cierra la sesión; cerrar la sesión exige ingresar nuevamente. No se guardan claves en SQLite ni se usan credenciales AWS para este acceso.

Implementación: `ruta/staff_auth.py`, formulario y guardia compartida en `ui_ejecutivos.require_login()`. Pruebas cubren cuentas válidas/inválidas, entrada directa sin sesión, acceso al mapa tras ingresar, salida y aislamiento de Mi Gobierno.

## Seguimiento

- Resumen de personas alertadas, sin contacto confirmado, contactadas que esperan orientación y quienes iniciaron el trámite. Quienes declinaron se cuentan aparte en el seguimiento; ninguna cifra representa resoluciones concedidas.
- Contactos por canal con respuestas únicas por canal, incluyendo rechazos; pendientes de atención en terreno por separado. No se suman intentos como personas.
- Tabla con búsqueda por nombre/RUN, estado y comuna. Detalle con siguiente acción, contacto de campaña e historial comprensible. No consulta RSH, pensiones ni documentos privados del perfil ni mezcla fichas de otra base.
- Responder/aceptar detiene el escalamiento; enviar/abrir sin responder no lo detiene. Iniciar no implica resolver. Declinar detiene todos los canales. Reglas compartidas en [[0012-detener-contacto-confirmado]].
- Meta ≥75% del próximo paso válido dentro del plazo explícitamente pendiente de instrumentación. No se reemplaza por porcentaje de respuesta o de inicio.

## Campañas en terreno

Mapa RM con la misma paleta y ubicaciones ficticias de [[heatmap-campanas-simulado]]. Solo representa pendientes presenciales sin contacto confirmado, con umbral comunal de cinco personas. No usa domicilios reales del RSH. Casos fuera de RM y grupos pequeños no se publican.

Único ajuste de planificación: **Personal disponible**, entre 1 y 20. Se buscan radios de 750, 1000, 1500, 2000, 2500 y 3000 metros; cada uno usa la búsqueda geométrica existente de máxima cobertura. Se elige el menor que alcance una jornada del equipo (8 atenciones por integrante; supuesto de demo), o la mayor cobertura disponible si ninguno alcanza esa capacidad. Empates conservan el radio menor. No se publica área con menos de cinco personas cercanas.

Contorno amarillo, personas cubiertas, comunas, radio informativo y jornadas estimadas; descarga GeoJSON sin RUN, nombres ni direcciones. La propuesta no agenda ni envía mensajes. Sede, acceso y disponibilidad requieren validación operativa; no representa una ruta vial.

## Fuentes y ejecución

Por defecto, demostración persistente y aislada `src/app/funnel-demo-ejecutivos.db` (ignorada por Git), con contactos RM ficticios y 19 días de respuestas simuladas. Puede sustituirse con `STAFF_DEMO_DB`. No reinicia una campaña ya preparada. Resultado de referencia: 92 detectadas = 26 por contactar + 23 esperan orientación + 34 iniciaron + 9 declinaron.

El selector «Casos de la aplicación» lee el embudo de `config.DB_PATH`; no descarga los contactos de DynamoDB ni unifica automáticamente AWS/SQLite. Esa integración sigue pendiente en [[board-clemente]]. La base vacía tiene un estado informativo. El mapa necesita conexión para las teselas CARTO/OpenStreetMap.

```powershell
uv run --group app streamlit run src/app/app.py --server.address localhost --server.port 8505 --server.headless true
```

Abrir `http://localhost:8505/?vista=ejecutivos`.

Código: `ui_ejecutivos.py`, `ruta/ejecutivos.py`, `ruta/despliegue.py`, `assets/executive.css`; integración en `portal.py` y `app.py`.

Verificación: `uv run --group app pytest`, `uv run --group app python src/app/verificar.py`; pruebas nuevas en `tests/test_executives.py` cubren planificación según equipo, privacidad, persistencia, filtros, navegación, mapa y campaña vacía. Recorrido Chromium en escritorio y móvil.

Implementación `81755d7`, merge `710df25`. Se conserva el chat público remoto en `/chat` y la carga dinámica de estilos. La integración también corrige la lectura UTF-8 de perfiles en la API para Windows y completa la aceptación de invitación en el test autorizado; no cambia las condiciones para leer el perfil.

Resultado integrado: **224 pruebas OK**, una omitida por dependencia opcional de trazas no instalada y ocho evaluaciones Bedrock excluidas del comando offline; verificador de 500 perfiles TODO OK. Chromium comprueba mapa y navegación sin errores JavaScript, a 1440 y 390 px. Vista local en puerto 8505.
