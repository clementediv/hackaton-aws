---
tipo: diseño
estado: implementado
fecha: 2026-10-15
---
# Trazabilidad de casos (portal de ejecutivos)

**Problema:** la meta de ≥75% de avance al próximo paso válido dentro del plazo ([[contexto-compartido-chileatiende]], [[0012-detener-contacto-confirmado]]) no se puede demostrar en la demo: los datos son sintéticos y no hay personas reales que avancen en un trámite.

**Qué sí se demuestra:** que cada caso deja un rastro auditable (cuándo, por qué canal, qué ocurrió y de qué fuente), suficiente para medir el indicador en un piloto y para que ningún caso pierda su seguimiento.

## Dónde está
Pestaña **Trazabilidad** del Portal de ejecutivos (`src/app/ui_ejecutivos.py`), sobre `src/app/ruta/trazabilidad.py`. Lee la bitácora `eventos` de la campaña en pantalla (la escriben `casos.py` y el colador) y, si hay credenciales, suma el historial de la detección en AWS (`ca-historial`, ver [[deteccion-proactiva-aws]]).

## Qué muestra
| Sección | Contenido |
|---|---|
| Cómo se medirá cada indicador | Contacto efectivo, acepta el acompañamiento, próximo paso válido dentro del plazo (meta 75%) y continuidad entre canales (meta 90%): evidencia que se guarda, si se registra o falta algo («Parcial») y cuántos casos de la demo ya tienen esa evidencia |
| Calidad del registro | Eventos registrados, % con fecha + canal + tipo, casos con historial y casos sin movimiento |
| Casos que requieren seguimiento | Casos abiertos sin movimiento hace N días (ajustable): sin respuesta, o respondieron y no avanzan |
| Línea de tiempo de un caso | Todos los eventos del RUN en orden, con su origen (registro local o AWS) |
| Descarga | Registro de auditoría completo en CSV |

## Qué falta para medir el KPI en un piloto
- **Plazo por trámite:** hoy se guarda la fecha del contacto y la del paso completado, pero no el plazo acordado para cada trámite.
- **Validez del paso:** el organismo debe confirmar que el paso registrado es válido (no basta con que la persona lo marque).
- Con eso, el indicador es: casos con paso válido dentro del plazo / casos con contacto confirmado.

Los conteos de la pestaña usan datos sintéticos: **validan que el registro existe, no que la meta se cumpla.** Tests en `tests/test_trazabilidad.py`.
