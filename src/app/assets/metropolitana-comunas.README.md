# Límites comunales RM para la demo

Fuente: Biblioteca del Congreso Nacional, servicio `comunas2017`:
https://arcgiswebad.bcn.cl/arcgis/rest/services/MBases/Servicio_Comunas/FeatureServer/0

Consulta `/query`, `where=codregion=13`, `outFields=*`, `outSR=4326`, `geometryPrecision=5`, `maxAllowableOffset=0.00025`, `f=geojson`. Descargado el 2026-10-15. 52 geometrías. Propiedades conservadas: código, comuna y provincia. Algunos nombres acentuados llegan dañados desde el servicio; las etiquetas de casos usan el catálogo sintético local y no esos nombres.

Cartografía de referencia de 2017, no certificación de límites vigentes ni domicilios. Se conserva atribución a BCN; el servicio no especifica licencia en `copyrightText`. El fondo urbano corresponde a CARTO / OpenStreetMap y se solicita durante la ejecución. Ver [heatmap-campanas-simulado](../../../docs/arquitectura/heatmap-campanas-simulado.md).
