# Contexto oficial del chatbot

La base pública complementa el acompañamiento de [[mi-gobierno]] y [[portal-ayuda-tramites]]. Se mantiene dentro de `src/app`, según el alcance solicitado.

## Fuentes y alcance

La captura inicial contiene **808 documentos y 5.429 fragmentos**: 408 fichas principales de Ventanilla Única Social, 147 páginas de ayuda, sus 12 categorías y otras páginas del portal; 231 documentos de ChileAtiende y cinco portales institucionales adicionales. El sitemap aportó 540 URLs públicas y se agregaron enlaces descubiertos en las páginas. No quedaron URLs pendientes de Ventanilla Única en ese recorrido. Esto describe la cobertura observada, no demuestra que toda prestación existente en Chile esté publicada allí.

- Ventanilla Única Social: sitemap, fichas, microfichas, categorías y centro de ayuda. También se siguen enlaces públicos del catálogo que no aparezcan en el sitemap.
- ChileAtiende: fichas de beneficios y trámites, categorías, ayuda y rutas por momentos de vida.
- Complementos institucionales: Registro Social de Hogares, Beneficios Estudiantiles, AFC, Minvu y Sence, cuando el contenido público sea accesible.

`documents.jsonl` guarda cada documento con título, URL, fuente, fecha de descarga UTC, fecha de actualización indicada cuando existe, secciones y enlaces. Se conservan requisitos, documentos, canales, etapas, costos, incompatibilidades y contactos tal como estén publicados; no se completan campos ausentes con suposiciones. El hash permite identificar cambios del texto. `manifest.json` informa la cobertura, redirecciones resueltas mediante descargas exitosas, páginas pendientes y errores. Las microfichas que redirigen a una misma ficha no son documentos distintos.

No se usan credenciales, cuentas de ciudadanos ni páginas autenticadas. Se consulta `robots.txt`, se limita la concurrencia a tres descargas y se espacian solicitudes por dominio. Los sitios bloqueados o dependientes de contenido no extraíble quedan reportados; no se eluden restricciones.

Quedaron cuatro accesos sin extracción útil: portada de ClaveÚnica, dos páginas de ayuda/atención de ChileAtiende y la portada de beneficiarios de Fonasa, esta última bloqueada por robots. Se conserva orientación de esos temas en las fichas accesibles de ChileAtiende y Ventanilla Única. No hay una base verificada de direcciones y horarios de todas las sucursales: el asistente debe remitir al buscador oficial y preguntar comuna/canal antes de orientar una visita, sin inventar una dirección.

## Uso en el chat

`ruta/knowledge.py` divide el texto en fragmentos y busca por términos con ponderación de título, sección, intención y sinónimos como PGU, RSH, FUAS o quedar sin trabajo. Las preguntas de seguimiento recuperan el tema del historial público; una consulta que nombra otro beneficio cambia el tema. Cada turno incorpora hasta seis fragmentos, con un presupuesto de 13.000 caracteres y referencias explícitas.

El chat público y el asistente del caso autorizado reciben estas referencias. La ruta personal y sus reglas siguen siendo la fuente para evaluaciones individuales. El modelo puede explicar requisitos publicados, pero no adjudicar beneficios ni calcular elegibilidad, montos o plazos personales. Ante discrepancias o convocatorias antiguas, debe exponer la limitación y remitir al organismo. El texto extraído se trata como datos externos, nunca como instrucciones.

Para acompañar, el modelo recibe la instrucción de identificar el beneficio exacto, reconocer lo que la persona declaró haber realizado, proponer un próximo paso con documentos y canal oficial, y confirmar antes de avanzar. Es seguimiento conversacional: no presenta solicitudes ni verifica automáticamente su estado. Una nueva evaluación determinista para beneficios distintos de PGU requiere implementación específica.

Sin Bedrock, se muestran extractos atribuidos y un enlace al procedimiento completo, sin inventar una secuencia. La búsqueda funciona localmente y no descarga sitios durante una consulta del usuario.

## Actualizar y revisar

Desde la raíz, con Python del entorno de la app:

```powershell
python -m pip install -r src/app/requirements-knowledge.txt
python src/app/crawl_knowledge.py --vus --chileatiende-limit 180
python src/app/query_knowledge.py "Cómo postular al subsidio de arriendo" --context
python src/app/verify_knowledge.py
python src/app/verificar.py
```

La ejecución habitual reutiliza documentos descargados y completa faltantes. Para consultar nuevamente las fuentes se debe usar `--refresh`; conviene hacerlo semanalmente y antes de una demo o campaña con fechas relevantes. La caché de HTML comprimido queda en `knowledge/.cache/`, ignorada por Git. `--reparse` vuelve a extraer esa caché sin red ni cambio de fechas de descarga. Para incluir más fichas de ChileAtiende, aumentar `--chileatiende-limit` o agregar semillas oficiales en el script.

Una consulta reciente no demuestra que el período descrito siga abierto. Se conserva la fecha publicada y el asistente debe diferenciarla de la fecha de descarga. Esta base es una captura reproducible de información pública, no una conexión con el estado de las solicitudes de cada organismo.
