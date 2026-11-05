---
tipo: implementacion
fecha: 2026-10-15
responsable: codex
---
# Heatmap y despliegue simulado de campañas

## Área propuesta de despliegue (actualización vigente)

La demo dibuja un **contorno amarillo** de campaña desde las mismas ubicaciones que alimentan el heatmap. Ver [0011-area-campana-segun-heatmap](adr/0011-area-campana-segun-heatmap.md). El ranking comunal se conserva como contexto, pero el despliegue se propone por concentración espacial y puede abarcar varias comunas.

En «Área de despliegue propuesta según el heatmap», ajustar radio (500–3000 m), personal y capacidad diaria; ocultar/mostrar el contorno con su casilla. El radio recalcula el sector de máxima cobertura; la capacidad estima jornadas sin desplazar el área. Solo aparece en Cola presencial. Se mantiene el calor, paleta y los controles de direcciones ficticias.

`ruta/despliegue.py` consume puntos publicables de peso 1, sin RUN/nombres. Busca máxima cobertura para un radio fijo en una aproximación plana local: ubicaciones individuales y centros de los círculos definidos por pares (distancia ≤ 2r). Desempata por compactación y coordenadas, independientemente del orden. El centro medio reemplaza al candidato cuando conserva los casos cubiertos. Umbral de propuesta: cinco casos próximos; si no se alcanza, se explica y no se dibuja un área.

El GeoJSON es un círculo aproximado por 96 segmentos, orden longitud/latitud. Distancias y superficie usan una proyección equirectangular a latitud −33,5°, apropiada para esta simulación local y no para medir deslindes. No usa distancia de calles, rutas, tiempos de viaje ni accesibilidad. El centro no representa una sucursal o sede validada. La propuesta puede cruzar límites comunales.

Escenario precargado: **10 de 84 casos publicables (11,9%) en San Bernardo** con radio 1,5 km; superficie aproximada 7,07 km², dos funcionarios × ocho atenciones/día → una jornada. Son cifras sintéticas; el porcentaje se calcula sobre ubicaciones efectivamente dibujables, no sobre los 92 casos totales. Inicios y rechazos retiran ubicaciones y recalculan la propuesta.

Descargas: JSON con cobertura/capacidad y GeoJSON del área, sin direcciones individuales ni identificadores. La propuesta no se agenda, persiste ni despacha. Se calcula de nuevo desde el snapshot vigente.

Verificación: **126 tests pasan** (13 nuevos), incluyendo concentración real del escenario, centros entre personas, radio/cobertura, jornadas por capacidad, determinismo, datos inválidos, umbral mínimo y recorrido de UI (slider, contorno, ocultación y diagnóstico). Ruff y verificador de 500 perfiles OK; Chrome valida superposición sin excepciones.

## Ubicaciones individuales ficticias (vista vigente)

El usuario pidió mostrar dispersión dentro de la RM, conservando diseño/paleta, en vez de concentrar cada comuna en un círculo. Esta actualización sustituye la representación de centroide del apartado siguiente. [0010-direcciones-simuladas](adr/0010-direcciones-simuladas.md).

Cada contacto metropolitano nuevo tiene dirección **ficticia**, latitud/longitud de seis decimales y `location_source=synthetic-address-v1`. `ruta/geografia.py` usa semilla/RUN/comuna y varios núcleos barriales con dispersión; rechaza candidatos fuera del polígono comunal BCN, incluidos huecos. No llama a un geocodificador ni utiliza domicilios RSH. El nombre «Pasaje Ficticio … (SIMULADA)» no corresponde a una calle verificada; una coordenada simulada puede coincidir con un lugar real por azar. No se asegura que sea una vivienda o esté sobre una calle.

El mismo RUN y semilla conservan posición al consultar, filtrar, reiniciar el proceso o avanzar el reloj; iniciar/declinar retira su peso. Nuevos contactos guardan estos campos en SQLite/CSV. Los snapshots de escenarios antiguos se enriquecen de forma determinista sin reescribir sus contactos originales ni sus estados. El CSV nacional antiguo sigue siendo compatible.

El motor publica **un aporte de peso 1 por persona** de comunas admitidas (mínimo cinco casos). Los 84 casos publicables de la demo generan 84 ubicaciones únicas, no seis puntos ponderados. El ranking mantiene los totales comunales. Coordenadas corruptas o ajenas a la comuna se omiten con aviso; nunca se trasladan silenciosamente al centro.

La UI mantiene fondo, límites, paleta y resolución 2048. Calor continuo por cercanía de ubicaciones; opciones Barrios/Sectores amplios, «Ver ubicaciones simuladas» para puntos y tooltip con dirección ficticia, y «Totales por comuna» para etiquetas agregadas. Ocultar calor deja los puntos visibles. Los círculos grandes comunales desaparecen. Leyenda cualitativa de baja a alta concentración: intensidad relativa al encuadre/suavizado, no un conteo exacto por color ni tasa poblacional. El inspector de personas muestra la misma dirección/coordenadas simuladas.

No se muestran RUN/nombres en los datos del mapa. La precisión individual y las direcciones se habilitan **solo con origen sintético**; no constituyen una política de acceso para domicilios reales. Los agregados conservan el umbral comunal; no se promete anonimato de las ubicaciones ficticias ni se intenta usar esta vista con información personal real.

Verificación ampliada: **113 tests pasan**. Nuevas comprobaciones de 500 puntos únicos dentro de su comuna, reproducibilidad, CSV nuevo/antiguo, compatibilidad de snapshots, conservación de peso, dispersión dentro de cada comuna, exclusión al iniciar/declinar, coordenadas inválidas y controles de mapa/UI. Ruff y verificador de 500 perfiles OK. Demo en http://localhost:8502, sobre el mismo escenario RM conservado.

## Vista vigente: Región Metropolitana (rediseño solicitado)

**Este apartado sustituye la vista nacional descrita debajo, que queda como registro del aporte inicial.** El mapa actual se limita a la RM y publica agregados por comuna. El usuario pidió más detalle, resolución y concentración legible. Decisión: [0009-heatmap-metropolitano](adr/0009-heatmap-metropolitano.md).

- Fondo urbano oscuro CARTO Dark Matter / OpenStreetMap con calles y etiquetas vectoriales; necesita internet. Sin claves aportadas por el usuario. Los datos del mapa son exclusivamente agregados sintéticos.
- Contornos locales de las 52 comunas: servicio público BCN `comunas2017`, consultado con `codregion=13`, WGS84, precisión 5 decimales y simplificación 0,00025 grados. Ver `assets/metropolitana-comunas.README.md`. Son referencias cartográficas de 2017, no límites validados a 2026.
- Encuadres Gran Santiago y Región completa, mapa de 650 px de alto, zoom hasta 15. Heatmap de textura 2048, halos cualitativos y círculos de área proporcional al volumen. Etiquetas con conteo exacto y comuna; tooltip con provincia/puntaje. Interruptor para retirar halos y comparar círculos sin suavizado.
- Colores estables por número de personas: 5–9 celeste, 10–14 turquesa, 15–19 amarillo, 20–24 naranja, 25+ rosado. La leyenda corresponde a los círculos; el halo es suavizado relativo, no una tasa ni un conteo por vivienda.
- Ranking por volumen descendente, luego puntaje demo. Propuesta descargable por comuna y capacidad del equipo. **Supresión mínima de cinco ahora por comuna**, más estricta que el agregado provincial previo. No se infiere el conteo de grupos omitidos en las métricas visibles.

Nuevas inicializaciones de la UI usan `generate_contacts(..., territory="metropolitana")`, con ocho comunas y pesos deliberadamente desiguales. No son estadísticas RSH ni de población. Solo cambia ubicación; conserva emails/teléfonos/empleadores y probabilidades. Las personas del escenario anterior no se reasignan al consultar el mapa.

El laboratorio usa ahora `src/app/funnel-demo-rm.db`, conservando la base anterior `funnel-demo.db`. Ejecución habitual: `uv run --group app streamlit run src/app/demo_embudo.py --server.address localhost --server.port 8502`. Escenario reproducible: Nueva simulación → Sin respuestas → Inicializar → +19 días. Con semilla 20261008: 92 casos en presencial; 84 se publican en seis comunas (21 Maipú, 17 Puente Alto, 14 San Bernardo, 14 Santiago, 13 La Florida, 5 Quilicura); el resto queda omitido por el umbral. Ninguna cifra es institucional.

Las coordenadas son puntos comunales aproximados de referencia, no domicilios ni distribución dentro de cada comuna. Los mapas muestran el área urbana; no fabrican ubicaciones individuales para llenar la imagen. Para otros procesos, el generador nacional y `campaign_ranking` se conservan compatibles, pero la UI solo usa `metropolitan_ranking`.

Verificación ampliada: **99 tests** (antes 90), con determinismo territorial, conservación de canales y personas, exclusión de otras regiones, umbral comunal 4/5, casos terminales, encuadres, interruptor de calor, colores estables, textura 2048 y etiquetas Unicode correctamente serializadas. Chrome a doble densidad verifica la presentación real; ruff OK y verificador de 500 perfiles TODO OK.

## Registro de la implementación nacional inicial

Extensión de [backend-embudo-contacto](backend-embudo-contacto.md), según [contacto-y-campanas](contacto-y-campanas.md) y [0008-heatmap-campanas-sinteticas](adr/0008-heatmap-campanas-sinteticas.md). Disponible en **http://localhost:8502** y en Detectar e invitar del portal. No necesita AWS, claves de mapas ni geocodificación.

## Recorrido de demostración

1. Nueva simulación → Sin respuestas → Inicializar embudo → Avanzar 19 días.
2. Ir a «Campañas territoriales · vista de ejecutivos». Las 92 personas detectadas quedan repartidas entre seis provincias sintéticas.
3. Arrastrar o ampliar el mapa; pasar sobre un círculo muestra provincia, personas y puntaje demo. Calor y tamaño representan volumen absoluto, no tasas ni densidad poblacional. La posición es una ciudad de referencia aproximada, no un centroide provincial ni un domicilio.
4. Filtrar por región y revisar el ranking. «Todo el seguimiento activo» es diagnóstico; no habilita propuestas de despliegue.
5. Elegir provincia, personal y capacidad diaria para estimar jornadas. Descargar ranking CSV o propuesta JSON. No se guarda una campaña, se agenda ni se despachan funcionarios. El responsable decide lugar y fechas.
6. Iniciar o declinar en el inspector y observar el mapa/ranking. Una provincia con menos de cinco casos desaparece de mapa, ranking, selectores y exportaciones agregadas. Es un umbral de demo, no una garantía de anonimato ante consultas repetidas.

La base inicial puede conservar respuestas simuladas anteriores. Para ver cobertura completa usar el escenario nuevo sin respuestas; no se inflan los datos para llenar el mapa.

## Datos RSH: qué existe y qué no

El RSH contempla domicilio e información del hogar según sus [preguntas frecuentes oficiales](https://www.registrosocial.gob.cl/preguntas-frecuentes-web). **El `rsh.csv` del hackatón no contiene comuna, provincia ni coordenadas**; tampoco `residencia.csv` permite geolocalizar domicilios. No hay conexión con un RSH real.

Esta demo une perfiles por RUN con `contacto.py`, exclusivamente sintético: seis combinaciones región/provincia/comuna, asignadas reproduciblemente, sin representar distribución real. No se infiere ubicación del tramo CSE o percentil PFP. Una integración real requeriría fuente territorial autorizada, fecha de actualización, catálogo comuna → provincia y revisión institucional de su uso. No se presupone una API pública de domicilios.

## Agregación y prioridad

`src/app/ruta/campanas.py` consume el snapshot sin modificar estados ni autorizaciones. Por defecto selecciona `status=active` y `stage=4`: quienes no iniciaron trámite, aunque hayan abierto o contestado. Excluye inicios y rechazos; omite territorios desconocidos y contactos no sintéticos.

Agrupa por región/provincia y suprime grupos menores de 5 **antes de devolverlos al frontend**. No devuelve RUN, nombres, direcciones ni integrantes. La vista convive con el inspector individual de la demo; no implementa autenticación institucional ni reemplaza controles de acceso de producción.

Puntaje **ilustrativo, no institucional** por persona: 1 base + 2 si el motor indica que podría solicitar PGU + 1 si falta antecedente PGU + 1 si hay hito de edad legal, apertura o acceso PGU entre hoy y 90 días. Evaluación del motor a la fecha inicial y reloj simulado para cercanía del hito. Sin perfil disponible solo suma base. Ranking por suma descendente, luego volumen y territorio para desempate determinista. No declara PGU adjudicada o impaga. Jornadas = `ceil(personas / (funcionarios × capacidad diaria))`.

## Cartografía y límites

`ui_campanas.py` usa pydeck (incluido con Streamlit): HeatmapLayer, círculos y etiquetas sobre contornos locales. `assets/campaign-basemap.geojson` extrae Chile, Argentina, Bolivia y Perú de [Natural Earth 1:110m](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_admin_0_countries.geojson), descargado el 15-10-2026, reducido a nombre y geometría. [Dominio público](https://www.naturalearthdata.com/about/terms-of-use/). No son límites provinciales ni cartografía oficial. Las seis posiciones en `PROVINCE_POINTS` son aproximaciones de ciudades; no se dispersan puntos para aparentar residencias.

No usa proveedores de teselas durante la ejecución. El mapa necesita WebGL; ranking y descargas permiten revisar los mismos agregados. Quedan pendientes cobertura de 56 provincias, localización validada, asignación de equipos, agenda, rutas, despacho, alertas y CESFAM.

## Verificación

`uv run --group app pytest` → **90 tests pasan**. Incluye supresión a 4/5, terminales, territorios desconocidos, ausencia de identificadores, prioridad trazable, capacidad y recorrido UI con reloj y filtros. `uv run --group app python src/app/verificar.py` → TODO OK sobre 500 perfiles. Ruff check/format en módulos nuevos. Ver board-clemente.
