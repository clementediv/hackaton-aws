---
tipo: board
integrante: Johann
color: verde
entorno: Kiro IDE Pro
frente: Desarrollo del MVP desde src/app
---
# 🟩 Board de Johann — Desarrollo con Kiro

## Entrada para Johann y sus agentes

El código se trabaja entre **Clemente (Codex + Claude)** y **Johann (Kiro de AWS)**, sin asignación de tareas ni carpetas exclusivas. Johann está trabajando desde `src/app`. Ambos envían sus aportes; antes de publicar se integran por merge y se revisan conflictos, duplicaciones e incompatibilidades lógicas.

La guía técnica autocontenida está en [[contexto-codear-johann]]: producto actualizado, pipeline, estado real, módulos, contratos, datos y pruebas. Para reducir el contexto de Kiro, usar [[inicio-kiro-johann]]; cargar la guía bajo demanda y leer después solo los archivos de la tarea elegida. Esta preparación es exclusiva de Johann y no cambia el setup de Clemente.

| | |
|---|---|
| **Entorno** | Kiro IDE Pro |
| **Alcance actual** | `src/app` como punto de trabajo; contexto completo del MVP disponible |
| **Integración** | Commit del aporte → fetch/merge de `origin/main` → resolver y verificar → push |
| **Commits** | Descripción breve del aporte, sin ID de tarea obligatorio |
| **Bitácora** | [[bitacora-johann]] |
| **Contexto para codear** | [[contexto-codear-johann]] · [[inicio-kiro-johann]] |

Este tablero registra avances e integración; no asigna tareas. La guía [[contexto-codear-johann]] incluye el flujo de merge. Las funciones del reparto anterior se conservan en el historial Git, no dirigen a los agentes de Johann.

## En curso
- Desarrollo de Johann desde `src/app`: aporte `0d06dab` integrado en `origin/main` (`ed989ad`) y traído localmente. Streamlit/SQLite, motor de rutas y cuatro vistas disponibles.

## Integración pendiente
- Unificar app y agente/contratos existentes: modelos, estados extra, repositorio/historial y clientes Bedrock. Ver [[revision-aporte-johann]]; merge textual completado, unificación semántica pendiente.
- Contexto local de Kiro preparado; activación en el checkout de Johann según [[inicio-kiro-johann]].

## Bloqueos
-

## Hecho
- Introducción del acceso subida y alineada con el formulario, conservando adaptación móvil. [[mi-gobierno]].
- Logo pequeño en esquina superior derecha del banner; encabezado sin botón duplicado Mi Gobierno ni Vista ejecutivo (disponible en panel lateral). Preguntas frecuentes de un clic en el asistente. 16 pruebas y Chrome escritorio/móvil OK. [[portada-chileatiende]], [[mi-gobierno]].
- Logo IPS más pequeño y centrado en su espacio: 160 px escritorio / 120 px móvil. [[portada-chileatiende]].
- Botón principal sobrio «Ver mis beneficios» y logo IPS arriba a la derecha. Tres pruebas del portal OK. [[portada-chileatiende]].
- Portada con texto y botón a la izquierda, logo IPS proporcionado por el usuario a la derecha y adaptación móvil. Tres pruebas del portal OK. [[portada-chileatiende]].
- Invitación principal centrada en una columna y sin botón lateral de trámites. Tres pruebas del portal OK. [[portada-chileatiende]].
- Retirados los tres textos del directorio lateral de la invitación principal. Enlace al catálogo conservado. [[portada-chileatiende]].
- Recuadro principal simplificado y ampliado: sin etiquetas accesorias, tipografía mayor y botón azul destacado. Tres pruebas del portal OK. [[portada-chileatiende]].
- Línea de tiempo simplificada: solo etapas, fechas y estados, sin párrafos inferiores ni pie explicativo. [[mi-gobierno]].
- Línea de tiempo por beneficio con postulación, revisión y resultado antes de los requisitos. Estados accesibles, calendario oficial FUAS y fechas PGU sin inventar resolución. Nueve pruebas de flujo/modelo OK. [[mi-gobierno]].
- Navegación del portal y subpestañas centradas al retirar el espacio reservado al radio oculto. [[portada-chileatiende]].
- Chat alineado con PGU al inicio y seguimiento centrado al desplazar en escritorio; bordes de 24 px y móvil apilado. Recorrido Chrome verificado. [[mi-gobierno]].
- Diseño del chat restaurado a la versión previa a separarlo en pestaña (`46f0c76`): tarjeta blanca, borde discreto e historial de 240 px; continúa a la derecha de Beneficios. [[mi-gobierno]].
- Dos subpestañas de Mi Gobierno; ayuda con video y carga complementaria dentro de cada requisito pendiente, reutilizando documentos disponibles. Ocho pruebas y recorrido Chrome con ayuda/carga/móvil OK. [[mi-gobierno]].
- Beneficios ampliados hacia los bordes con chat destacado a la derecha y distribución adaptable; se conserva el diseño de las tres subpestañas y el historial compartido. [[mi-gobierno]].
- Mi Gobierno: barra segmentada con Beneficios, Datos personales y Chatbot; asistente exclusivo de su pestaña y requisitos desplegados verdes/amarillos según evaluación. Adjuntos compartidos con estado visible sin aprobación automática. [[mi-gobierno]].
- `8af4ca9` · Acceso RUN/clave ficticia integrado con mejoras de contacto y asistente del equipo. 173 pruebas y verificador de 500 perfiles OK; recorrido Chrome escritorio/móvil validado.
- Acceso de demostración a Mi Gobierno con RUN y clave ficticia, selección del perfil correspondiente y cierre de sesión. Consentimiento separado del acceso. [[mi-gobierno]].
- `ff8c1d8` · Mi Gobierno y portada: beneficios como vista inicial, datos personales separados, documentos compartidos por requisito, asistente y confirmación de revocación. 139 pruebas y verificador de 500 perfiles OK. [[mi-gobierno]].
- Mi Gobierno validado localmente: panel separado de Inicio, autorización, documentos, declaración económica y guía PGU según requisitos. 139 pruebas, verificador 500 perfiles y recorrido Chrome escritorio/móvil OK. [[mi-gobierno]].
- Portada de ChileAtiende reproducida desde los recursos públicos del 15-10-2026, con navegación al acompañamiento y 136 pruebas OK. [[portada-chileatiende]].
- Revisión del aporte y correcciones de integración: grupo uv `app`, revocación de consentimiento/historial y verificador offline. 61 tests y verificación de 500 perfiles OK; lint completo de la app pendiente.
