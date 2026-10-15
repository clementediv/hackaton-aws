---
tipo: pitch
seccion: problema
destino: generador de diapositivas (IA)
fecha: 2026-10-15
reto: "[[ChileAtiende-a-tiempo]]"
---
# Brief para generar diapositivas — El problema

**Proyecto:** ChileAtiende a Tiempo · Hackatón AWS Breaking Barriers Chile 2026 (14–16 oct, Universidad de Chile).
**Institución:** Instituto de Previsión Social (IPS) / ChileAtiende.
**Foco del MVP:** jubilación y Pensión Garantizada Universal (PGU).
**Objetivo de esta presentación:** instalar el PROBLEMA (no la solución). La solución va en otra sección.

> Instrucciones para la IA que arma las diapositivas: usar frases cortas, una idea por lámina, texto grande. Español. No inventar cifras: usar solo las de este documento. Respetar las notas de "qué NO decir". Tono: cercano y humano, no corporativo.

---

## Mensaje central (una sola frase)
Hoy la persona tiene que descubrir sola qué beneficios le corresponden, en qué orden y con qué plazos; y cada vez que cambia de canal, repite su historia desde cero.

---

## Diapositiva 1 — La historia de Rosa (apertura emocional)
- Rosa, 59 años, se acerca a jubilar. (Personaje ficticio del desafío, usar como relato, no como dato real.)
- No sabe bien qué son AFP, PGU ni SCOMP.
- Visita oficinas, hace filas y recién ahí descubre que le faltan documentos.
- Nadie le dice cuál es el siguiente paso.
- **Cierre de lámina:** "El beneficio existe. El problema es llegar a él a tiempo."

Visual sugerido: una persona mayor frente a un mesón o papeles; sobrio, sin estigma.

## Diapositiva 2 — El problema, en concreto
Cuatro fricciones (una línea cada una):
1. **Descubrir:** la persona debe averiguar sola qué le corresponde.
2. **Ordenar:** no sabe qué trámite va primero ni qué documentos necesita.
3. **Plazos:** se entera tarde de fechas clave (ej. la solicitud de PGU se abre a los 64 años y 9 meses).
4. **Repetir:** al cambiar de canal (web, teléfono, sucursal) cuenta su historia otra vez.

## Diapositiva 3 — Por qué importa (contexto institucional)
Usar como MAGNITUD DEL CONTEXTO, no como resultado del proyecto. Cifras del PPT institucional del IPS, transcritas y SIN verificación externa:
- Personas de 65+ en Chile: **2.587.238** (Censo 2024).
- Personas que recibían PGU: **2.243.121** (diciembre 2025).
- Nuevas personas pensionadas en 2025: **187.799**.
- Contacto efectivo de las campañas IPS 2025: **85%**.

**Qué NO decir:** no restar estos universos entre sí para afirmar "X personas pierden la PGU". Tienen fechas y definiciones distintas. Ninguna de estas cifras es un resultado de nuestra app.

## Diapositiva 4 — El problema es demostrable con datos
Hallazgo propio sobre un dataset sintético de 500 personas (fecha de referencia 2026-10-08), evaluado con reglas en código:
- **26 personas cumplen los requisitos de PGU y no la están recibiendo.**
- Además: 9 no pueden evaluarse porque les falta un antecedente (sin Registro Social de Hogares o sin registro de residencia); 14 cumplen 65 dentro de los próximos 12 meses.

**Qué NO decir:** no son 26 beneficios concedidos ni personas reales; es orientación preliminar sobre datos de prueba. La decisión la toma el IPS. Sirve para mostrar que el problema "beneficios no cobrados por falta de acompañamiento" es detectable automáticamente.

## Diapositiva 5 — La experiencia que falta
Hoy el trámite está aislado. Lo que debería existir es acompañamiento:
anticipado (avisar antes del plazo) · personalizado (según la situación de cada persona) · continuo (el contexto viaja con la persona entre canales).

Transición hacia la solución (si la presentación continúa): "Eso es lo que construimos."

---

## Datos de apoyo (para quien arme el guion; no necesariamente van en lámina)

**Las 4 fricciones salen de:** el desafío institucional descrito en el PPT del IPS. La "experiencia objetivo" tiene 6 pasos: detectar, invitar, autorizar, preparar la ruta, acompañar, cerrar y anticipar.

**Regla de diseño del proyecto (da credibilidad, útil en Q&A):** la elegibilidad y los plazos se calculan en código determinista, nunca los inventa el modelo de lenguaje; toda respuesta cita su fuente. La IA explica y organiza; el IPS valida y resuelve.

**Requisitos de PGU que el sistema evalúa (fuente: ficha ChileAtiende, parámetros a oct-2026, en `src/app/ruta/config.py`):**
- 65 años o más (la solicitud se abre a los 64 años y 9 meses).
- No pertenecer al 10% de mayores ingresos (percentil de focalización ≤ 90).
- Residencia: 20 años desde los 20, y 4 de los últimos 5.
- Pensión base bajo el límite superior ($1.252.602); completa hasta $789.139 y parcial en el tramo intermedio.
- Monto máximo: $231.732 (65–74 años) · $250.275 (75+).

## Trazabilidad y límites (honestidad, importa para el jurado)
- **Verificado en esta sesión:** las 26 personas elegibles sin PGU salen de correr el motor de reglas del repo sobre los 500 perfiles. Reproducible.
- **Transcrito del PPT, sin verificar:** todas las cifras institucionales de la Diapositiva 3, la edad de apertura de PGU a los 64 años 9 meses y la referencia al "estudio de experiencia usuaria 2025" (el PPT lo cita pero no incluye el informe ni su URL; pedirlo antes de citarlo como fuente).
- **Datos sintéticos:** el dataset de 500 personas es 100% ficticio; RUN, AFP e identificadores no corresponden a nadie real. `pfp_percentil` y `pafe_estimada` son simulaciones, no fórmulas oficiales.
- **No es asesoría:** nada de esto adjudica beneficios ni establece elegibilidad legal.

## Criterios de evaluación del hackatón (para calibrar el peso de cada lámina)
Impacto 25 / Solución 25 / Demo 20 / Arquitectura 15 / Factibilidad 15. La sección "problema" alimenta sobre todo Impacto: dejar clara la magnitud y lo humano antes de mostrar la solución.
