---
tipo: investigacion
reto: "[[ChileAtiende-a-tiempo]]"
fecha: 2026-10-14
autor: Bruno (enjambre de agentes de investigación)
estado: borrador para el equipo
---
# Investigación — Adultos mayores, IA y servicios públicos (contexto ChileAtiende a Tiempo)

Investigación de contexto para afinar la solución y la demo. Seis ejes, cada uno con fuentes citadas. **Toda cifra lleva su fuente; lo que no se pudo verificar está marcado como tal.** Contenido parafraseado (sin reproducir >30 palabras de ninguna fuente); el contenido fue reformulado para cumplir restricciones de licencia.

> Cómo leer esto: cada sección tiene **hallazgos** (con fuente) e **insights** (qué hacer). Al final hay un bloque de **insights priorizados para la demo (T22–T28)** y los **pendientes de verificación**.

## Índice
1. Caracterización tecnológica del adulto mayor en Chile
2. Cómo usan los adultos mayores la IA y los chatbots
3. UX y accesibilidad para adultos mayores (alimenta T27)
4. Contexto PGU / jubilación en Chile (fuentes oficiales para el catálogo)
5. Gobierno digital y atención multicanal en Chile
6. Referentes internacionales (inspiración)
7. Insights priorizados para la demo
8. Pendientes de verificación

---

## 1. Caracterización tecnológica del adulto mayor en Chile

**Demografía**
- Censo 2024: **3.665.028 personas de 60+ (19,8% de la población)**, ya superan a los menores de 15 — [INE/Diario Estrategia](https://www.diarioestrategia.cl/texto-diario/mostrar/6034175/ine-pais-residen-3665028-personas-60-anos-equivalentes-198-poblacion-residente), [La Tercera](https://www.latercera.com/nacional/noticia/mayores-de-60-anos-ya-son-uno-de-cada-cinco-habitantes-en-chile-y-se-proyectan-como-el-grupo-mas-numeroso-en-2044/).
- Proyección: de 18,1% (2022) a **~32% en 2050**; grupo más numeroso hacia 2044 — [UC](https://www.uc.cl/academia-en-los-medios/el-32-de-la-poblacion-chilena-en-el-2050-sera-adulto-mayor/), [ADN](https://www.adnradio.cl/2026/03/23/chile-enfrenta-una-vejez-record-personas-mayores-serian-el-grupo-mas-numeroso-del-pais-en-2044/).

**Acceso vs. uso real**
- **88% tiene internet en el hogar, pero solo 42% lo usa activamente** (UC–Confuturo 2024) — [El Mostrador](https://www.elmostrador.cl/agenda-pais/agenda-digital/2024/07/04/solo-la-mitad-de-los-adultos-mayores-chilenos-tiene-un-smartphone-para-comunicarse/), [Infogate](https://infogate.cl/2025/09/brecha-digital-en-chile-el-desafio-de-incluir-a-los-adultos-mayores-en-la-era-tecnologica/).
- **~50% tiene smartphone propio**; el uso subió de 47% (2019) a 58% (2021) por la pandemia — [Confuturo](https://www.confuturo.cl/continuemos/articulos/observatorio-del-envejecimiento/solo-la-mitad-de-los-adultos-mayores-chilenos-tiene-un-smartphone), [UC](https://www.uc.cl/academia-en-los-medios/adultos-mayores-aumentaron-el-uso-de-tecnologia/).
- Dispositivo principal 60+: smartphone (42,5%), luego computador/tablet (38,8%) — [UC](https://www.uc.cl/academia-en-los-medios/adultos-mayores-aumentaron-el-uso-de-tecnologia/).

**ClaveÚnica: el cuello de botella del trámite**
- **Solo ~21% de los 60+ sabe usar ClaveÚnica**; en zonas rurales 9 de cada 10 nunca la usaron (UC–Confuturo 2024) — [Infogate](https://infogate.cl/2025/09/brecha-digital-en-chile-el-desafio-de-incluir-a-los-adultos-mayores-en-la-era-tecnologica/). Es la llave para postular a la PGU online.

**Alfabetización y carga emocional**
- Solo **~5% recibió capacitación digital formal**; **66% no usa email**; ~25% siente que "ya no está en edad de aprender" — [Infogate](https://infogate.cl/2025/09/brecha-digital-en-chile-el-desafio-de-incluir-a-los-adultos-mayores-en-la-era-tecnologica/), [OEI](https://oei.int/oficinas/chile/noticias/el-66-de-las-personas-mayores-no-usa-correo-electronico/).
- **66% se ha sentido presionado** a aprender tecnología para no quedar excluido — [La Tercera](https://www.latercera.com/publirreportajes/noticia/adultos-mayores-66-se-ha-sentido-presionado-por-adoptar-nuevas-tecnologias/26GT455IZZF6JHF2SITJ2DX4OU/).

**Confianza y fraude**
- Tramo 61–80: **77% confía en transacciones digitales**, pero **~40% sufrió un intento de estafa** en el último año; ~55% se considera vulnerable a ciberestafas (Cadem–WOM 2025–2026) — [CNN Chile](https://www.cnnchile.com/pais/alfabetizacion-digital-en-personas-mayores-el-75-afirma-que-las-aplicaciones-moviles-les-permiten-ahorrar-tiempo-en-su-dia-a-dia/), [El Dínamo](https://www.eldinamo.cl/presentado-por/2026/09/07/personas-mayores-son-mas-vulnerables-a-sufrir-ciberestafas-pese-a-confianza-en-los-pagos-online/).

**Política pública**
- Octubre 2025: **Estrategia Nacional de Inclusión Digital para Personas Mayores 2025–2035** — [MinSegPres](https://msgg.gob.cl/wp/2025/10/23/gobierno-lanza-estrategia-nacional-de-inclusion-digital-para-personas-mayores/). El proyecto se alinea con esta estrategia.

**Insights**
- El público objetivo no es "digital por defecto": diseñar para baja alfabetización, con apoyo presencial/telefónico como parte del flujo, no como excepción.
- No asumir ClaveÚnica: detectarla, guiar su obtención y ofrecer ruta presencial.
- WhatsApp es la interfaz más familiar del país (~91,9% uso general, dato **nacional** no desagregado 60+) — [MG Branketing](https://www.mgbranketing.cl/post/porcentajes-de-las-redes-sociales-m%C3%A1s-usadas-en-chile-en-el-2025). Vale evaluarlo como canal, aunque la demo use web.

## 2. Cómo usan los adultos mayores la IA y los chatbots

**Adopción (Chile)**
- **47% de personas 55+ usa IA en 2025** (vs 33% en 2024); promedio nacional 60% (III Encuesta Percepción Social IA, U. Autónoma, vía FayerWayer).
- 84% dice conocer la IA pero 43% siente preocupación; 1 de cada 3 fue víctima de fraude en 2025 (Senior Tech, Claro+Criteria).
- **51% de los 55+ no distingue contenido IA de humano** → riesgo de fraude/deepfakes.

**Benchmark EE.UU.**
- Solo 10% de los 65+ ha usado ChatGPT (Pew 2025); 77% nunca usa chatbots (Pew 2026).

**Qué consultan** (datos Senior Tec, Chile, ~1.895 sesiones): soporte emocional/acompañamiento, trámites paso a paso, salud/medicamentos (~14%), tareas operativas y compras (~11%).

**Barreras**: desconfianza en la exactitud, privacidad, alucinaciones, dificultad para distinguir IA de humano.

**Preferencias**: respuestas simples y reformulables ("explícamelo más simple"), IA como asistente y no autoridad.

> Nota: estos datos chilenos provienen de prensa que cita estudios; conviene re-verificar en la fuente primaria antes de citarlos en el pitch.

**Insights**
- Lenguaje claro por defecto + botón **"explícamelo más simple"**.
- **Confianza informada**: citar fuente oficial (IPS/ChileAtiende) y fecha en cada dato de PGU.
- **Nunca pedir ClaveÚnica ni claves bancarias**, y decirlo explícitamente; advertir sobre fraudes de "bono/pensión".
- Posicionar como **puente hacia el trámite oficial**, no autoridad final.

## 3. UX y accesibilidad para adultos mayores (alimenta T27)

**Base**: las necesidades de usuarios mayores se cubren con WCAG; apuntar a nivel **A y AA** — [W3C/WAI](https://www.w3.org/WAI/older-users/), [W3C/WAI developing](https://www.w3.org/WAI/older-users/developing/). Los 65+ son ~43% más lentos navegando que los 21–55 — [NN/g](https://www.nngroup.com/articles/usability-seniors-improvements/).

**Checklist de UX accesible (para T27, sobre las vistas de `ux-demo.md`)**
1. **Contraste** AA: 4.5:1 texto normal, 3:1 texto grande/íconos. Nada de grises claros sobre blanco — [W3C](https://www.w3.org/WAI/older-users/developing/), [UserWay](https://userway.org/blog/web-accessibility-for-the-elderly/).
2. **Letra grande**, peso normal/semibold (no "light"), ampliable sin romper layout; más grande pero sin pasar el punto crítico de legibilidad — [Frontiers in Psychology](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.931646/full).
3. **Objetivos táctiles** mínimo 24×24 px (WCAG 2.5.8 AA), apuntar a ~44×44 px en los CTA principales — [W3C SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum).
4. **Espaciado generoso** entre controles (botones de invitación/autorización, casillas del checklist) — [W3C SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum).
5. **Layout lineal** de una columna en la vista persona; agrupaciones claras en el panel — [gov.uk](https://accessibility.blog.gov.uk/2016/09/02/dos-and-donts-on-designing-for-accessibility/).
6. **Lenguaje claro** ~6°–8° grado: oraciones cortas, voz activa, un paso por frase — [digital.gov](https://digital.gov/resources/an-introduction-to-plain-language), [US DOL](https://www.dol.gov/agencies/eta/ui-modernization/use-plain-language/unemployment-applications).
7. **Definir términos** (PGU, pensión base, RSH, "antecedente faltante") la primera vez que aparecen — [NN/g](https://www.nngroup.com/articles/define-techy-words-old-users/).
8. **Chatbot predecible**: respuestas cortas, tono de acompañante, mismo estilo de acciones — [SeniorTalk](https://www.senior-talk.com/blog/chatbot-user-experience-designing-interfaces-for-the-elderly), [Springer](https://link.springer.com/article/10.1007/s11042-025-20989-7).
9. **Manejo de error amable**: cuando el bot no entienda, decirlo simple y ofrecer salida ("¿quieres hablar con un ejecutivo?") — [NIH/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8692264/).
10. **Estados de carga/error perceptibles** (WCAG 4.1.3): spinner, "Reintentar", "No encontramos ese RUN" en regiones ARIA live (`role="status"` / `role="alert"`); nunca stack traces — [W3C ARIA19](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA19), [TestParty](https://testparty.ai/blog/wcag-4-1-3-status-messages-2025-guide).
11. _(opcional)_ Entrada por **voz** en el chat — [Springer](https://link.springer.com/article/10.1007/s11042-025-20989-7).
12. **No depender solo del color** para los 5 estados: ícono + texto además del verde/rojo/ámbar — [CUNY](https://guides.cuny.edu/accessibility/a11ydodont).

## 4. Contexto PGU / jubilación (fuentes oficiales para el catálogo)

Fuente principal verificada en vivo: [Ficha ChileAtiende PGU (102077)](https://www.chileatiende.gob.cl/fichas/102077-pension-garantizada-universal-pgu).

**Montos (ficha vigente consultada)**: pensión base ≤ $789.139 → PGU **$231.732**; entre $789.140 y $1.252.602 → monto decreciente; ≥ $1.252.603 → sin derecho. **75+**: máximo **$250.275** (Reforma de Pensiones).

**Requisitos oficiales**: (1) 65 años cumplidos; (2) no estar en el 10% más rico (Puntaje de Focalización Previsional, usa RSH); (3) residencia ≥20 años desde los 20 y ≥4 de los últimos 5; (4) pensión base ≤ $1.252.602.

**Edad de solicitud — CONFIRMADO**: se accede al pago a los **65**, pero se puede **ingresar la solicitud desde los 64 años y 9 meses**. Son dos hitos distintos del mismo trámite — [ChileAtiende 102077](https://www.chileatiende.gob.cl/fichas/102077-pension-garantizada-universal-pgu). (Resuelve el pendiente que teníamos en `ux-demo.md` y en el board.)

**Marco legal**: Ley 21.419, Ley 21.538, Decreto 52, Ley 20.255, Res. Ex. N° 77.

**Canales**: online (requiere ClaveÚnica), videoatención, presencial (solo cédula), call center 101.

**Causales de suspensión/extinción** (útiles para seguimiento): no cobrar 6 meses; no entregar antecedentes en 3 meses; >180 días fuera de Chile; pasar al 10% más rico. Reclamo: 5 días hábiles.

**Cobertura**: ~2.225.101 beneficiarios a nov-2025 (dato de la Superintendencia de Pensiones **leído vía prensa**, re-verificar en spensiones.cl antes del pitch) — [Hacienda, ley corta](https://hacienda.cl/noticias-y-eventos/noticias/pgu-congreso-despacha-ley-corta).

**Insights (fricciones a resolver)**
- Separar **jubilar (AFP/SCOMP)** de **solicitar PGU**: son trámites distintos; la PGU no reemplaza jubilarse — [SCOMP](https://www.scomp.cl/que-es-scomp.html), [CMF Educa](https://cmfchile.cl/educa/621/w3-article-1686.html).
- Calcular y avisar la fecha exacta de **64a 9m** según nacimiento (ventana de solicitud anticipada).
- Explicar en lenguaje simple el **porqué** de la elegibilidad y del monto.
- Anticipar el **rechazo por residencia** (certificado de viajes PDI) para quienes vivieron fuera.
- Recordar mantención del beneficio (cobro, viajes, plazos de reclamo).

> URLs oficiales para el catálogo de Johann: ficha PGU 102077, [aumento PGU 130457](https://www.chileatiende.gob.cl/fichas/130457-aumento-de-la-pension-garantizada-universal-pgu), [Superintendencia de Pensiones](https://www.spensiones.cl/portal/institucional/594/w3-propertyvalue-9899.html).

## 5. Gobierno digital y atención multicanal en Chile

- **ChileAtiende** (red del IPS): 200 sucursales, Call Center 101, atención móvil, redes sociales, agendamiento web — [ChileAtiende](https://www.chileatiende.gob.cl/que-es-chileatiende), [Agendamiento](https://www.chileatiende.gob.cl/agendamiento).
- **ClaveÚnica**: identidad digital del Estado, **~15,9 millones de usuarios**, +1.700 trámites — [digital.gob.cl](https://www.digital.gob.cl/media/noticias/gobierno-digital-lanza-campana-para-proteger-y-mantener-actualizados-los-datos-de-claveunica/).
- **Notificador del Estado + CasillaÚnica**: el IPS lideró la primera notificación masiva avisando **proactivamente** sobre beneficios no cobrados (incluida la PGU), y durante 2026 lo integra en "Mi ChileAtiende" y **todos los canales**, para que cualquier ejecutivo vea los mensajes de la persona — [digital.gob.cl](https://www.digital.gob.cl/media/noticias/ips-lidera-primera-notificacion-masiva-del-estado-traves-de-la-casillaunica/). **Esto es casi exactamente nuestro flujo.**
- Chile subió al **puesto 10** del Índice de Gobierno Digital OCDE (2025) — [digital.gob.cl](https://digital.gob.cl/media/noticias/chile-sube-22-puestos-y-queda-decimo-en-el-ranking-de-gobierno-digital-de-la-ocde/).

**Insights**
- **Integrarse, no competir**: apoyarse en CasillaÚnica/Notificador y "Mi ChileAtiende" como carriles oficiales de aviso y continuidad.
- **Autenticar con ClaveÚnica** (no inventar login) siguiendo la guía técnica.
- La **continuidad entre canales** (ejecutivo retoma el mismo caso) es el valor diferencial y coincide con la dirección oficial del IPS.
- **No duplicar** la postulación PGU: orientar, anticipar y derivar al trámite oficial.

## 6. Referentes internacionales (inspiración)

- **Estonia** — servicios proactivos por "eventos de vida": el Estado ofrece el beneficio en vez de que la persona lo busque — [OECD-OPSI](https://oecd-opsi.org/innovations/life-event-based-services-in-estonia/), [e-Estonia](https://e-estonia.com/proactive-services-estonia/). _Nuestro "detectar hito → invitar" es esto._
- **Reino Unido — GOV.UK Chat**: IA conversacional **RAG solo sobre contenido oficial**, con avisos de error, preguntas de aclaración y derivación a humano; corre sobre **Amazon Bedrock + Claude** (precisión ~76%→~90% en pilotos) — [Inside GOV.UK](https://insidegovuk.blog.gov.uk/2026/03/16/5-things-we-learned-testing-gov-uk-chat-an-ai-assistant-for-government/), [DSIT](https://www.gov.uk/algorithmic-transparency-records/dsit-gov-dot-uk-chat). _Casi nuestra arquitectura._
- **España — ISSA (Seguridad Social)**: asistente que orienta sobre la pensión de jubilación con info oficial y **redirige a la Sede Electrónica** para el trámite — [Seg. Social](https://revista.seg-social.es/-/%C2%BFconoces-a-issa-es-el-asistente-virtual-para-facilitar-consultas-y-tr%C3%A1mites-de-la-seguridad-social). _"Orienta → organismo resuelve", idéntico._
- **Singapur — VICA / chat.gov.sg**: plataforma única de IA conversacional, +60 agencias, +800.000 consultas/mes — [GovTech](https://www.tech.gov.sg/technews/ai-agents/).
- **Australia — myGov / Service NSW**: jubilación como life event con journey guiado y calculadoras — [myGov](https://my.gov.au/en/services/ageing/retirement).
- **OCDE**: 20 de 28 países diseñan por eventos de vida (incluida jubilación); la proactividad real alimenta decisiones operativas — [OCDE GaaG 2025](https://www.oecd.org/en/publications/government-at-a-glance-2025_0efd0bcd-en.html).

**Riesgos documentados (diseñar con cuidado)**
- **NYC MyCity**: bot daba respuestas contrarias a la ley, sin revisión previa — [Governing](https://www.governing.com/management-and-administration/is-your-government-ready-for-ai-a-simple-test-for-local-leaders).
- **Air Canada**: la empresa fue responsabilizada por el consejo erróneo de su chatbot — [AgencyChat](https://agencychat.substack.com/p/government-chatbot-liability).
- **ODI**: los LLM dan respuestas poco fiables sobre servicios públicos y entierran lo clave en textos largos — [Computer Weekly](https://www.computerweekly.com/news/366638829/Large-language-models-provide-unreliable-answers-about-public-services-Open-Data-Institute-finds).

**Insights**
- Patrón ganador: **RAG solo sobre fuente oficial + cita verificable + derivación a humano para lo personal/la decisión**. Reglas de elegibilidad en código, no en el LLM (ya es nuestra decisión).
- Guardrails desde el día uno: avisos de error, preguntas de aclaración, nunca pedir datos sensibles.

---

## 7. Insights priorizados para la demo (T22–T28)

Lo que conviene incorporar a `ux-demo.md` y a las vistas:

1. **Letra grande, alto contraste, botones grandes, una columna** — regla base de todas las pantallas (checklist §3). Impacta T22, T23, T24, T27.
2. **Lenguaje claro + definir términos + botón "explícamelo más simple"** en el chat. T23, T27.
3. **Mensaje de confianza/seguridad explícito**: "canal oficial, nunca te pediremos tus claves". Reduce el riesgo de fraude que afecta a este grupo. T22, T23.
4. **Fecha 64a 9m confirmada**: la pantalla de ruta puede mostrar la fecha exacta de apertura de solicitud según nacimiento. Resuelve el pendiente del documento. T22.
5. **Derivación a humano/sucursal** como paso de primera clase (no error): "¿prefieres que te atienda un ejecutivo?". Encaja con el panel ejecutivo. T23, T24.
6. **No depender del color** en los 5 estados: ícono + texto. T24, T27.
7. **Narrativa del pitch**: envejecimiento (19,8%→~32%), baja alfabetización digital, y que nuestro flujo coincide con la dirección oficial del IPS (Notificador/CasillaÚnica) y con referentes como Estonia, GOV.UK (Bedrock+Claude) y la ISSA española. T28 y pitch de Jp.

## 8. Pendientes de verificación (no citar como hecho sin confirmar)

- Uso de WhatsApp y de smartphone **desagregado 60+** desde fuente oficial (hoy solo hay nacional o de estudios UC/Cadem).
- Cifras chilenas de uso de IA en 55+ (47%, 51% no distingue IA) vienen de **prensa citando estudios**: re-verificar en fuente primaria para el pitch.
- Cobertura PGU **2.225.101 (nov-2025)**: confirmar en spensiones.cl antes de usarla.
- Los **montos y umbrales PGU** deben cargarse al catálogo con `fuente_url` y fecha de consulta (tarea de Johann); aquí quedan como referencia de la ficha vigente.
- El término formal "eventos de vida" no aparece literal en fuentes .gob.cl chilenas; sí el marco "de trámites a servicios" y el reporte OCDE sobre Chile.

## Relacionado
[[contexto-compartido-chileatiende]] · [[ux-demo]] · [[datos-dataset-A]] · [[arquitectura-chileatiende]] · [[board]]
