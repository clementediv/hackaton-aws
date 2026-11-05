---
tipo: adr
estado: aceptada
fecha: 2026-10-14
---
# ADR 0004 — El MVP se centra en jubilación + PGU usando el dataset A

## Contexto
El MVP inicial priorizaba el evento nacimiento con un catálogo armado a mano. La organización entregó datos-dataset-A: 500 perfiles sintéticos que cruzan Registro Civil, RSH, residencia, previsión, pensiones y situación laboral, diseñados para evaluar **jubilación y PGU**.

## Opciones consideradas
1. Mantener nacimiento como evento principal y ignorar el dataset.
2. **Cambiar el foco a jubilación + PGU**, usando el dataset como fuente de los perfiles ciudadanos.
3. Hacer los tres eventos con la misma profundidad.

## Decisión
Opción 2. El agente parte de un RUN (o del relato de la persona), lee su perfil del dataset, evalúa la PGU con reglas en código y arma la ruta según el resultado: `elegible`, `no_elegible`, `antecedente_faltante`, `proximo` o `ya_recibe`. Nacimiento y cesantía quedan como extensiones si sobra tiempo, para mostrar escalabilidad.

## Consecuencias
- Hay datos reales de prueba, lo que permite medir sobre los 500 perfiles y no solo sobre usuarios simulados.
- La herramienta nueva `consultar_perfil(run)` lee `perfiles.json`. Con eso se reduce el trabajo de catálogo: solo hacen falta los parámetros de la PGU desde la ficha oficial.
- El caso "a tiempo" queda claro: 17 personas cumplen 65 en los próximos 12 meses, y 37 personas mayores de 65 serían candidatas sin PGU registrada (cálculo preliminar).
- Las métricas del pitch salen del dataset: cuántas PGU no cobradas se detectan y cuántos antecedentes faltantes se resuelven.
