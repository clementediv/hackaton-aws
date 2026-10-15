# Requirements Document

## Introduction

Hoy el sistema no detecta nada por sí mismo en el canal conversacional. El motor determinista existe y funciona (`src/app/ruta/reglas.py`), pero el agente no lo alcanza: `src/agent/tools.py` intenta importar `src.rules`, módulo que no existe en el repositorio, por lo que `build_registry()` solo registra `consultar_perfil` y `leer_caso`. Las herramientas `evaluar_pgu`, `calcular_hitos` y `buscar_beneficios` están declaradas con esquema completo en `src/agent/prompts.py` y nunca se registran. El puente de Streamlit (`src/app/ruta/chatbot.py`) compensa esa ausencia registrando una sola herramienta que devuelve un contexto ya precalculado por la interfaz: el modelo parafrasea hechos masticados.

Este feature cierra ese hueco. La capacidad que se entrega es del sistema, no del modelo: reglas deterministas que clasifican a las 500 personas del dataset A frente a la PGU y a la jubilación, que enumeran los trámites concretados y los requeridos con sus documentos y dependencias, y que quedan expuestas como herramientas para que el asistente consulte, evalúe y explique citando la fuente. El modelo orquesta y redacta; la decisión de elegibilidad, los montos y las fechas los calcula el código. La decisión oficial siempre es del IPS o de la AFP.

El trabajo es de integración y de puente de tipos, no de reescritura: se reutiliza el motor de PGU y jubilación, el catálogo de 8 beneficios como datos con su evaluador genérico, el generador de rutas y los contratos Pydantic ya definidos en `src/contracts/`. El feature también resuelve las desalineaciones que hoy impiden ese puente: estados de PGU que faltan en el contrato, ids de requisito que no calzan, la imposibilidad de distinguir "falta antecedente" de "aún no corresponde por fecha", y fuentes sin URL ni estado de verificación.

### Fuera de alcance

- Unificar los tres vocabularios de documentos que hoy coexisten (`Paso.documentos` como texto libre, los ids de `government.BENEFIT_DOCUMENTS` y `DOCUMENT_TYPES`, y `ChecklistItem` de `src/agent/route.py`). Este feature consume el vocabulario existente y documenta la divergencia.
- Construir una API HTTP (`GET /alertas` y pares) que todavía no existe en el repositorio.
- Fusionar o reemplazar los motores paralelos `src/app/ruta/reglas.py` y `src/proactivo/reglas.py`. Se construye un puente; la consolidación es otra decisión.
- Verificar contra ChileAtiende los requisitos de los 7 beneficios del catálogo marcados `verificado: False`. Se muestran como no verificados.
- El colador de contacto escalonado (email, llamada, trabajo, presencial), el heatmap de campañas y la ficha ejecutiva.
- Persistencia nueva, despliegue en AWS, DynamoDB e integración con fuentes de datos oficiales. El dataset A es sintético.
- Decidir la elegibilidad oficial, presentar solicitudes o afirmar resoluciones institucionales.

## Glossary

- **Eligibility_Service**: capa de detección que ejecuta las reglas deterministas y entrega resultados tipados. Ocupa el lugar del módulo ausente que hoy busca `src/agent/tools.py`.
- **Rules_Engine**: motor determinista vigente en `src/app/ruta/reglas.py`. Expone `evaluar_pgu`, `evaluar_jubilacion` y `calcular_hitos` sobre los dicts crudos del dataset.
- **Benefit_Catalog**: catálogo de 8 beneficios como datos en `src/proactivo/catalogo.py`, cada uno con requisitos `{campo, op, valor, texto}`, paso siguiente y fuente con flag `verificado`.
- **Catalog_Evaluator**: evaluador genérico de requisitos del catálogo en `src/proactivo/reglas.py` (`evaluate`), que devuelve `cumple` en `True`, `False` o sin valor.
- **Route_Engine**: generador de rutas y checklist en `src/app/ruta/rutas.py` (`generar_ruta`, `estado_pasos`, `proximo_paso`).
- **Contract_Adapter**: puente entre los dicts del Rules_Engine y los modelos Pydantic de `src/contracts/`.
- **Tool_Registry**: registro de handlers del agente en `src/agent/tools.py` (`build_registry`, `ToolRegistry.call`).
- **Sobre de resultado**: envoltorio uniforme con que el Tool_Registry entrega todo resultado al modelo, con `ok` y, ante fallo, `error.type` y `error.message`.
- **Agent**: bucle de tool use sobre Bedrock Converse en `src/agent/loop.py`.
- **Chat_Bridge**: puente entre la interfaz Streamlit y el Agent en `src/app/ruta/chatbot.py`.
- **Profile_Repository**: acceso a perfiles en `src/tools/profiles.py`, con control de consentimiento y de RUN.
- **Interface**: aplicación Streamlit, en sus dos vistas: la de la persona y el panel del ejecutivo.
- **Batch_Detector**: ejecución de la detección sobre el conjunto completo de perfiles del dataset A.
- **Verification_Suite**: `uv run pytest`, `uv run ruff check .` y el verificador de dominio `src/app/verificar.py`.
- **PGU**: Pensión Garantizada Universal, aporte mensual del Estado desde los 65 años.
- **PFP**: Puntaje de Focalización Previsional, que se calcula a partir del RSH.
- **RSH**: Registro Social de Hogares.
- **PAFE**: pensión autofinanciada estimada que informa la AFP. En el dataset A es un valor simulado.
- **Fecha de referencia**: fecha a la que se evalúan las reglas. En el dataset A es 2026-10-08 y es un parámetro, no la fecha del sistema.
- **Antecedente faltante**: situación en que un requisito no puede evaluarse porque el perfil carece del dato de origen.
- **Pendiente por fecha**: situación en que un requisito se cumple a partir de una fecha futura conocida.
- **Perfil no clasificado**: perfil cuyo estado no pudo determinarse por un dato con formato inesperado, registrado y excluido de los conteos por estado.
- **Apertura de solicitud**: fecha desde la que la solicitud puede presentarse (64 años y 9 meses para la PGU). Es un hito, no un vencimiento.
- **Trámite concretado**: beneficio o pensión que el perfil registra en estado `vigente`.
- **Trámite requerido**: paso que la persona o un organismo debe completar para acceder a un beneficio.
- **Orientación preliminar**: resultado del Eligibility_Service, sujeto a validación del IPS o la AFP.

## Requirements

### Requirement 1: Detección determinista con el modelo fuera de la decisión

**User Story:** Como ejecutivo de ChileAtiende, quiero que la elegibilidad la calcule el código y que el asistente solo explique ese cálculo, para poder responder a una persona sin arriesgar una afirmación inventada.

#### Acceptance Criteria

1. THE Eligibility_Service SHALL calcular los estados de elegibilidad, los montos y las fechas con código determinista a partir del perfil y de la fecha de referencia recibidas, sin leer la fecha del sistema ni invocar al modelo, y SHALL devolver los mismos estados, montos y fechas en ejecuciones repetidas con el mismo perfil y la misma fecha de referencia.
2. WHEN el Agent responde sobre elegibilidad, montos, requisitos, hitos o plazos, THE Agent SHALL tomar cada estado, monto y fecha de un resultado de herramienta exitoso del mismo turno, y SHALL abstenerse de derivar montos, edades o fechas que esos resultados no contengan.
3. WHEN el Agent recibe un resultado de herramienta, THE Agent SHALL nombrar en la respuesta el mismo estado que devolvió la herramienta, sin sustituirlo por otro estado de la enumeración, y SHALL incluir todos los motivos de ese resultado.
4. IF la respuesta del Agent declara un estado de elegibilidad distinto al que el Eligibility_Service devolvió para el caso, THEN THE Interface SHALL mostrar el estado del Eligibility_Service y SHALL omitir el estado declarado por el Agent.
5. IF el Agent no tiene un resultado de herramienta exitoso para un estado, un monto o una fecha, o lo recibe como sobre de error, THEN THE Agent SHALL abstenerse de afirmar ese dato, SHALL informar cuál dato falta y SHALL pedir la ejecución de la herramienta que lo entrega.
6. THE Eligibility_Service SHALL obtener la regla de elegibilidad de cada beneficio desde un único origen (el Rules_Engine para PGU y jubilación, el Benefit_Catalog para los beneficios del catálogo) y SHALL abstenerse de reevaluar los umbrales, los montos y las fechas que ese origen ya calculó.
7. THE Eligibility_Service SHALL leer los parámetros normativos (edades de acceso y edades legales, montos máximos por tramo, umbrales de pensión base, percentil máximo de PFP y meses de invitación anticipada) exclusivamente desde `src/app/ruta/config.py`, sin repetir esos valores como literales en otro módulo.
8. WHERE la llamada no entrega una fecha de referencia, THE Eligibility_Service SHALL evaluar con la fecha de referencia definida en `src/app/ruta/config.py`.
9. IF un parámetro normativo requerido falta en `src/app/ruta/config.py`, THEN THE Eligibility_Service SHALL fallar con un error que identifique el parámetro ausente y SHALL abstenerse de sustituirlo por un valor por defecto.

### Requirement 2: Clasificación de PGU en los siete estados del motor

**User Story:** Como ejecutivo, quiero saber en qué situación exacta está una persona frente a la PGU, para distinguir a quién invitar hoy de quién debe esperar y de quién necesita un antecedente.

#### Acceptance Criteria

1. THE Eligibility_Service SHALL clasificar cada perfil recibido en exactamente uno de los siete estados de PGU (`excluido`, `ya_recibe`, `futuro`, `no_elegible`, `antecedente_faltante`, `proximo`, `elegible`), evaluando las reglas a la fecha de referencia recibida como parámetro y no a la fecha del sistema.
2. WHEN más de una condición de resultado se satisface para un mismo perfil, THE Eligibility_Service SHALL devolver el primer estado aplicable en el orden `excluido`, `ya_recibe`, `futuro`, `no_elegible`, `antecedente_faltante`, `proximo`, `elegible`, y SHALL omitir del resultado los estados restantes.
3. IF el perfil registra `registro_civil.estado` igual a `fallecido`, THEN THE Eligibility_Service SHALL devolver el estado `excluido` con un motivo que identifique el fallecimiento como causa, cualquiera sea el estado de los cuatro requisitos de PGU.
4. IF el perfil registra al menos un beneficio de tipo PGU en estado `vigente` y no queda en estado `excluido`, THEN THE Eligibility_Service SHALL devolver el estado `ya_recibe`, cualquiera sea el estado de los cuatro requisitos de PGU.
5. WHEN la persona tiene menos de 65 años cumplidos a la fecha de referencia y los meses completos entre la fecha de referencia y la fecha de acceso a la PGU son más de 12, THE Eligibility_Service SHALL devolver el estado `futuro` e informar la fecha de acceso a la PGU.
6. IF el perfil no queda en `excluido`, `ya_recibe` ni `futuro` y al menos un requisito de PGU queda en estado `no_cumple`, THEN THE Eligibility_Service SHALL devolver el estado `no_elegible` y SHALL enumerar todos los requisitos en `no_cumple` identificándolos por su id.
7. IF el perfil no queda en `excluido`, `ya_recibe` ni `futuro`, ningún requisito de PGU queda en estado `no_cumple` y al menos uno queda en estado `falta_antecedente`, THEN THE Eligibility_Service SHALL devolver el estado `antecedente_faltante` y SHALL enumerar todos los ids de los requisitos en `falta_antecedente`.
8. WHEN la persona tiene menos de 65 años cumplidos a la fecha de referencia, los meses completos entre la fecha de referencia y la fecha de acceso a la PGU son 12 o menos y ningún requisito de PGU queda en `no_cumple` ni en `falta_antecedente`, THE Eligibility_Service SHALL devolver el estado `proximo`, informar la fecha de apertura de la solicitud y la fecha de acceso a la PGU, y SHALL indicar si la fecha de referencia ya alcanzó la fecha de apertura de la solicitud.
9. WHEN los cuatro requisitos de PGU (`edad`, `pfp`, `residencia`, `pension_base`) quedan en estado `cumple` y el perfil no queda en `excluido` ni en `ya_recibe`, THE Eligibility_Service SHALL devolver el estado `elegible` y SHALL declararlo como orientación preliminar sujeta a la resolución del IPS.
10. WHEN el Eligibility_Service devuelve un estado de PGU, THE Eligibility_Service SHALL acompañarlo del monto máximo del tramo de edad que corresponde a la edad a la fecha de referencia (tramo superior cuando la edad alcanza los 75 años, tramo de 65 a 74 años en los demás casos), del monto estimado calculado desde la pensión base, y del origen de la pensión base identificado como pensiones vigentes registradas, PAFE informada por la AFP, o ausencia de registros con pensión base cero.
11. IF el perfil registra un beneficio de tipo PGU en estado `suspendido` y ningún beneficio de tipo PGU en estado `vigente`, THEN THE Eligibility_Service SHALL devolver el mismo estado que devolvería sin ese registro y SHALL prefijar el motivo con la mención de la PGU suspendida.
12. IF el perfil carece de `registro_civil.fecha_nacimiento` o ese valor no puede interpretarse como fecha, THEN THE Eligibility_Service SHALL devolver un error que identifique el campo afectado y SHALL abstenerse de devolver un estado de PGU.

### Requirement 3: Clasificación de la jubilación en los seis estados del motor

**User Story:** Como ejecutivo, quiero ver la situación de jubilación de una persona junto a la de PGU, para orientar el trámite que corresponde y no mezclar dos decisiones distintas.

#### Acceptance Criteria

1. THE Eligibility_Service SHALL clasificar cada perfil en exactamente uno de los seis estados de jubilación: `excluido`, `pensionado`, `sin_afp`, `puede_pensionarse`, `proximo` y `futuro`, y SHALL entregar ese estado separado del estado de PGU, sin derivar uno del otro.
2. THE Eligibility_Service SHALL aplicar la precedencia `excluido`, `pensionado`, `sin_afp`, `puede_pensionarse`, `proximo`, `futuro`, en ese orden, y SHALL devolver el primer estado cuya condición se cumple a la fecha de referencia.
3. WHEN el perfil registra `registro_civil.estado` igual a `fallecido`, THE Eligibility_Service SHALL devolver el estado `excluido`, cualquiera sea su afiliación, sus pensiones vigentes o sus hitos.
4. WHEN el perfil registra al menos una pensión de tipo `vejez` o `sistema_antiguo` en estado `vigente`, THE Eligibility_Service SHALL devolver el estado `pensionado` y SHALL enumerar todas las pensiones vigentes del perfil con su tipo y su monto.
5. WHEN el perfil carece del bloque `prevision` y no registra pensión de vejez vigente, THE Eligibility_Service SHALL devolver el estado `sin_afp`, SHALL informar que la persona nunca estuvo afiliada a una AFP y que la PGU es la vía principal, y SHALL abstenerse de registrar esa ausencia como requisito en estado `no_cumple` o `falta_antecedente`.
6. WHEN el perfil registra el bloque `prevision`, no registra pensión de vejez vigente y la fecha de referencia es igual o posterior a la fecha de edad legal de vejez, THE Eligibility_Service SHALL devolver el estado `puede_pensionarse`, SHALL informar la fecha de edad legal cumplida y SHALL informar que pensionarse por vejez es voluntario.
7. WHEN el perfil registra el bloque `prevision`, no registra pensión de vejez vigente y la fecha de referencia es igual o posterior a la fecha de invitación a jubilación y anterior a la fecha de edad legal, THE Eligibility_Service SHALL devolver el estado `proximo` y SHALL informar la fecha de edad legal.
8. WHEN el perfil registra el bloque `prevision`, no registra pensión de vejez vigente y la fecha de referencia es anterior a la fecha de invitación a jubilación, THE Eligibility_Service SHALL devolver el estado `futuro` y SHALL informar la fecha de edad legal.
9. THE Eligibility_Service SHALL calcular la edad legal de vejez desde el sexo registral con los valores de `config.py` (60 años para `F` y 65 años para `M`) y SHALL calcular la fecha de invitación a jubilación restando a la fecha de edad legal los meses de anticipación configurados (12 en la configuración vigente).
10. WHEN el Eligibility_Service entrega los hitos de una persona, THE Eligibility_Service SHALL incluir las cinco fechas del motor (invitación a jubilación, edad legal, apertura de solicitud de PGU, acceso a PGU y tramo de 75 años) calculadas desde la fecha de nacimiento y no desde la fecha de referencia, y SHALL marcar las cinco con el indicador de vencimiento en falso, porque son aperturas o cambios de tramo y ninguna caduca.

### Requirement 4: Tres situaciones distinguibles por requisito

**User Story:** Como persona que consulta, quiero entender si no cumplo un requisito, si falta un antecedente que debo conseguir, o si solo debo esperar una fecha, porque las tres situaciones piden acciones distintas.

#### Acceptance Criteria

1. THE Rules_Engine SHALL asignar a cada uno de los cuatro requisitos de PGU que evalúa (`edad`, `pfp`, `residencia`, `pension_base`) exactamente uno de los estados `cumple`, `no_cumple`, `falta_antecedente` o `pendiente`, mutuamente excluyentes.
2. IF el dato de origen de un requisito está presente y el valor observado queda fuera del umbral del parámetro correspondiente de `config.py` (`pfp_percentil_max` para `pfp`, `pension_superior` para `pension_base`, `residencia_anios_desde_20` y `residencia_anios_ultimos_5` para `residencia`), THEN THE Rules_Engine SHALL asignar el estado `no_cumple` e informar el valor observado y el umbral aplicado.
3. IF el dato de origen de un requisito está ausente o es insuficiente para aplicar su umbral, THEN THE Rules_Engine SHALL asignar el estado `falta_antecedente`, SHALL identificar el dato ausente y SHALL nombrar el organismo que lo entrega entre `Registro Civil`, `RSH`, `Residencia / PDI` y `AFP / Compañías / IPS`.
4. WHEN el dato de origen de un requisito está presente y el requisito queda cumplido a partir de una fecha posterior a la fecha de referencia, THE Rules_Engine SHALL asignar el estado `pendiente`, SHALL informar la fecha desde la que el requisito queda cumplido y SHALL excluirlo tanto de la enumeración de requisitos incumplidos como de la de antecedentes faltantes.
5. IF el perfil carece del bloque `rsh`, o el bloque `rsh` tiene `info_pfp_disponible` en falso o `pfp_percentil` sin valor, THEN THE Rules_Engine SHALL asignar el estado `falta_antecedente` al requisito `pfp` y SHALL nombrar al `RSH` como organismo que entrega el dato.
6. IF el perfil carece del bloque `residencia`, THEN THE Rules_Engine SHALL asignar el estado `falta_antecedente` al requisito `residencia` y SHALL nombrar a `Residencia / PDI` como organismo que entrega el dato.
7. IF el perfil carece del bloque `prevision` y no registra pensiones vigentes, THEN THE Rules_Engine SHALL evaluar el requisito `pension_base` con pensión base cero, SHALL informar que ese valor proviene de la ausencia de registros y SHALL abstenerse de asignar el estado `falta_antecedente` al requisito `pension_base`.
8. THE Contract_Adapter SHALL representar los cuatro estados por requisito con cuatro valores distintos entre sí en el contrato publicado, y SHALL abstenerse de representar dos estados distintos con un mismo valor, en particular `falta_antecedente` y `pendiente`.
9. WHEN la Verification_Suite convierte las evaluaciones de los 500 perfiles del dataset A a la fecha de referencia del dataset, THE Verification_Suite SHALL comprobar que el estado de cada requisito recuperado del contrato publicado coincide con el estado que asignó el Rules_Engine.
10. WHEN la Interface presenta un requisito en estado `pendiente`, THE Interface SHALL mostrarlo como espera de una fecha junto a la fecha desde la que queda cumplido, y SHALL abstenerse de presentarlo como requisito incumplido o como antecedente faltante.

### Requirement 5: Resultados tipados en los contratos sin duplicar reglas

**User Story:** Como desarrollador del equipo, quiero que el agente y la interfaz consuman los resultados del motor a través de los contratos Pydantic, para integrar sin reimplementar ni desalinear reglas.

#### Acceptance Criteria

1. THE Contract_Adapter SHALL mapear cada uno de los siete resultados de PGU del Rules_Engine (`excluido`, `ya_recibe`, `futuro`, `no_elegible`, `antecedente_faltante`, `proximo`, `elegible`) a exactamente un miembro de `PguStatus`, SHALL conservar sin renombrar los cinco valores ya publicados (`elegible`, `no_elegible`, `antecedente_faltante`, `proximo`, `ya_recibe`) y SHALL publicar `excluido` y `futuro` con el mismo texto que emite el Rules_Engine.
2. THE Contract_Adapter SHALL emitir un `Reason` por cada requisito que entrega el Rules_Engine, con los ids `edad`, `pfp`, `residencia` y `pension_base`, y SHALL omitir los ids `vivo` y `sin_pgu_vigente` mientras el Rules_Engine no los emita, sin reemplazarlos por un `Reason` con un valor supuesto.
3. WHEN el Contract_Adapter convierte una evaluación del Rules_Engine, THE Contract_Adapter SHALL publicar el estado, el id de cada requisito, el estado por requisito y el texto de detalle tal como los entrega esa evaluación y en el mismo orden, SHALL tomar el título de la fuente del texto que entrega el Rules_Engine, y SHALL abstenerse de recalcular umbrales, montos o fechas y de construir una URL que el Rules_Engine no haya entregado.
4. WHEN el Contract_Adapter procesa los 500 perfiles de `data/raw/dataset_A_participantes/perfiles.json` con la fecha de referencia 2026-10-08, THE Contract_Adapter SHALL producir para cada perfil un `PguResult` cuyo estado, cantidad de requisitos, ids de requisito en el mismo orden, estado por requisito y texto de detalle corresponden uno a uno con los de la evaluación del Rules_Engine para ese perfil, y SHALL convertir los 500 perfiles sin ningún error de equivalencia.
5. IF una evaluación del Rules_Engine contiene un resultado de PGU, un id de requisito, un estado por requisito o un tipo de hito sin equivalencia declarada en el contrato, THEN THE Contract_Adapter SHALL interrumpir la conversión de ese perfil con un error que nombre el valor sin equivalencia y el RUN, SHALL abstenerse de devolver un `PguResult` con un valor por defecto o con requisitos incompletos, y SHALL dejar la evaluación recibida sin modificar.
6. THE Contract_Adapter SHALL registrar en el `PguResult` el `run` del perfil evaluado y la misma fecha de referencia con la que el Rules_Engine evaluó ese perfil, sin sustituirla por la fecha del sistema, y SHALL mantener el campo `preliminary` en verdadero.
7. WHEN el Contract_Adapter entrega los hitos de un perfil, THE Contract_Adapter SHALL emitir cinco objetos `Milestone`, uno por cada fecha del Rules_Engine (invitación a jubilación, edad legal de vejez, apertura de solicitud de PGU, acceso a PGU y tramo de 75 años), cada uno con un `MilestoneKind` distinto, incluido el tramo de 75 años que el contrato hoy no declara, con la fecha idéntica a la que entrega el Rules_Engine, con descripción no vacía, con el marcador de vencimiento en falso por tratarse de aperturas y con una fuente cuyo título identifique el origen del hito.
8. WHEN el Contract_Adapter recibe un `Profile` en lugar del dict crudo del dataset, THE Contract_Adapter SHALL entregar al Rules_Engine el volcado por alias en español de ese `Profile` y SHALL producir el mismo `PguResult` y los mismos `Milestone` que produce a partir del dict crudo equivalente.
9. IF la evaluación recibida del Rules_Engine contiene un estado o un detalle que no se deriva de los datos del perfil, THEN THE Contract_Adapter SHALL publicarlos sin corregirlos ni recalcularlos.

### Requirement 6: Trazabilidad de la fuente con URL y estado de verificación

**User Story:** Como ejecutivo, quiero que cada afirmación traiga su fuente y su estado de verificación, para responder con respaldo y advertir cuando un dato todavía no está contrastado.

#### Acceptance Criteria

1. WHEN el Eligibility_Service entrega un requisito, un hito o un paso, THE Eligibility_Service SHALL adjuntarle exactamente una fuente con título no vacío y con estado de verificación siempre presente, y SHALL copiar la URL literal de `FUENTE_PGU`, `FUENTE_PGU_AUMENTO` o de la clave de `FUENTES` de `config.py` que corresponda al origen, sin componer ni alterar esa URL.
2. THE Eligibility_Service SHALL representar con valores mutuamente distinguibles las tres situaciones de respaldo: fuente verificada (estado de verificación verdadero y URL presente), fuente no verificada (estado de verificación falso) y ausencia de fuente (sin fuente adjunta).
3. WHEN el Eligibility_Service entrega un beneficio del Benefit_Catalog, THE Eligibility_Service SHALL propagar sin modificar el flag `verificado` del catálogo, de modo que la PGU se entregue como fuente verificada con la URL de su ficha y los otros 7 beneficios se entreguen como fuente no verificada con la URL de búsqueda genérica de ChileAtiende.
4. WHEN la Interface muestra un dato de detección, THE Interface SHALL mostrar junto a ese dato uno de tres indicadores mutuamente excluyentes: fuente verificada con su título y su URL, fuente no verificada con la advertencia de dato sin contrastar, o ausencia de fuente con el aviso de dato sin respaldo citable.
5. IF una fuente carece de URL, THEN THE Eligibility_Service SHALL nombrar en el título el origen disponible (el organismo que el Rules_Engine informa para ese requisito o el dataset A), SHALL mantener la URL ausente y el estado de verificación en falso, y SHALL declarar que ese origen no entrega una URL de respaldo.
6. WHEN la respuesta se construye sobre datos del dataset A, THE Eligibility_Service SHALL identificar el dato como sintético, SHALL informar la fecha de referencia aplicada (`FECHA_REFERENCIA`, 2026-10-08 en el dataset A) y SHALL entregar esa fuente como no verificada.
7. IF un resultado de herramienta llega sin fuente, THEN THE Agent SHALL declarar que ese dato no tiene fuente disponible, SHALL pedir el contraste con el organismo competente y SHALL abstenerse de sustituir la fuente ausente por una URL propia o por la fuente de otro dato.
8. THE Agent SHALL citar textualmente el título y la URL devueltos por las herramientas del turno, y SHALL abstenerse de incluir en la respuesta cualquier URL que no aparezca en esos resultados.

### Requirement 7: Herramientas del agente efectivamente registradas y coherentes

**User Story:** Como desarrollador, quiero que el agente tenga registradas las herramientas de evaluación y de catálogo, para que el asistente detecte en vez de parafrasear un contexto precalculado.

#### Acceptance Criteria

1. WHEN `build_registry()` se ejecuta con el módulo del Eligibility_Service resuelto, THE Tool_Registry SHALL registrar los cinco nombres `consultar_perfil`, `leer_caso`, `evaluar_pgu`, `calcular_hitos` y `buscar_beneficios`.
2. THE Tool_Registry SHALL resolver `evaluar_pgu` y `calcular_hitos` desde un módulo versionado en el repositorio, sin depender del módulo ausente `src.rules`.
3. IF la resolución de ese módulo falla o el módulo no entrega `evaluar_pgu` y `calcular_hitos`, THEN THE Tool_Registry SHALL fallar con un error que nombre el módulo y la herramienta no resuelta, en lugar de devolver un registro con menos de los cinco nombres.
4. WHEN la Verification_Suite se ejecuta, THE Verification_Suite SHALL comparar los nombres declarados en `_TOOL_SPECS` de `src/agent/prompts.py` con los nombres registrados por `build_registry()` y SHALL fallar nombrando cada herramienta que figure en solo uno de los dos conjuntos.
5. WHERE `guardar_caso` no tiene handler registrado, THE Agent SHALL mantener ese nombre fuera de `_TOOL_SPECS` y fuera del tool config, de modo que ninguna herramienta declarada al modelo quede sin handler.
6. WHEN `build_tool_config()` recibe los nombres registrados por `build_registry()`, THE Agent SHALL exponer al modelo únicamente esas herramientas, con los valores admitidos declarados para `buscar_beneficios` iguales a los `beneficio_id` y a los eventos del Benefit_Catalog de 8 beneficios.
7. WHEN `buscar_beneficios` se ejecuta con un `beneficio_id` o un evento del Benefit_Catalog, THE Tool_Registry SHALL devolver, por cada beneficio coincidente, sus requisitos con el texto declarado, su paso siguiente y su fuente con título, URL y estado de verificación.
8. IF el argumento de `buscar_beneficios` no corresponde a ningún `beneficio_id` ni a ningún evento del Benefit_Catalog, THEN THE Tool_Registry SHALL devolver el sobre de error con `error.type` igual a `invalid_input` y un mensaje que identifique el argumento recibido, sin devolver beneficios.
9. WHEN un handler lanza una excepción, THE Tool_Registry SHALL devolver el sobre de resultado con `error.type` igual a `permission_denied` ante `PermissionError`, `invalid_input` ante `ValueError` e `internal` ante cualquier otra excepción, con un mensaje que no reproduzca el texto ni la traza de la excepción no prevista, y SHALL dejar el caso sin modificaciones.
10. WHEN `evaluar_pgu` o `calcular_hitos` devuelve un resultado para el caso actual, THE Tool_Registry SHALL guardar ese resultado en el caso y SHALL recalcular la ruta y el checklist desde el resultado de PGU y los hitos guardados, manteniendo la ruta y el checklist sin cambios mientras el caso no tenga un resultado de PGU guardado.

### Requirement 8: Detección de los trámites, documentos y dependencias

**User Story:** Como persona próxima a jubilar, quiero saber qué trámites ya tengo resueltos y cuáles me faltan, con los documentos y el orden, para avanzar al próximo paso sin adivinar.

#### Acceptance Criteria

1. THE Eligibility_Service SHALL entregar en dos colecciones separadas los trámites concretados, que son los beneficios y pensiones que el perfil registra en estado `vigente`, y los trámites requeridos, que son los pasos pendientes de la persona o de un organismo, y SHALL clasificar como requerido todo beneficio o pensión en un estado distinto de `vigente`, incluido `suspendido`.
2. WHEN el Route_Engine recibe un diagnóstico, THE Route_Engine SHALL devolver los pasos requeridos, cada uno con un id único dentro de la ruta, trámite entre `Jubilación`, `PGU`, `Antecedentes` y `Seguimiento`, título, qué hacer, dónde, documentos en el vocabulario de texto libre vigente, dependencias, fecha de disponibilidad cuando el paso la tenga, tipo entre `persona` y `organismo`, y fuente.
3. WHERE un requisito del beneficio queda en estado `falta_antecedente`, THE Route_Engine SHALL incluir una sola vez el paso de obtención de ese antecedente y SHALL declararlo dependencia del paso de solicitud del beneficio.
4. WHEN el Catalog_Evaluator evalúa un beneficio cuyo campo requerido está ausente en el perfil del dataset A y ningún requisito evaluable de ese beneficio queda incumplido, THE Catalog_Evaluator SHALL devolver `cumple` sin valor, SHALL nombrar cada campo ausente y SHALL abstenerse de informar como incumplido un requisito cuyo campo está ausente.
5. WHEN el Eligibility_Service enumera los beneficios de una persona, THE Eligibility_Service SHALL evaluar los 8 beneficios del Benefit_Catalog y SHALL incluir únicamente los que no figuran como trámite concretado y no tienen ningún requisito evaluable incumplido, cada uno etiquetado como cumplido o con antecedente faltante, con su paso siguiente y su fuente.
6. WHERE un paso lo resuelve un organismo, THE Route_Engine SHALL marcar el tipo como `organismo`, SHALL nombrar en el campo dónde al organismo responsable y SHALL entregar ese paso sin documentos ni acciones pedidas a la persona.
7. THE Route_Engine SHALL asignar a cada paso exactamente un estado, evaluando en este orden `completado` cuando el paso figura como completado, `bloqueado` cuando alguna de sus dependencias no figura como completada, `en_espera` cuando su fecha de disponibilidad es posterior a la fecha de referencia y `disponible` en los demás casos, y SHALL señalar como único próximo paso el primer paso `disponible` en el orden de la ruta o, si ninguno queda `disponible`, el primer paso `en_espera`.
8. WHEN un beneficio o un paso queda disponible a partir de una fecha, THE Route_Engine SHALL informar esa fecha como apertura de solicitud y SHALL abstenerse de presentarla como vencimiento, plazo de caducidad o fecha límite.
9. WHERE ningún requisito del beneficio queda en estado `falta_antecedente`, THE Route_Engine SHALL omitir de la ruta los pasos de obtención de antecedentes.
10. THE Route_Engine SHALL declarar en las dependencias de cada paso únicamente ids de pasos presentes en la misma ruta y SHALL mantener el grafo de dependencias sin ciclos, de modo que todo paso alcance el estado `disponible` al completarse sus dependencias.
11. IF ningún paso de la ruta queda en estado `disponible` ni `en_espera`, THEN THE Route_Engine SHALL devolver la ruta sin próximo paso y SHALL informar si la ruta no tiene pasos, si todos están completados o si quedan pasos bloqueados por dependencias sin completar.

### Requirement 9: Detección sobre el conjunto completo de perfiles

**User Story:** Como equipo, quiero correr la detección sobre las 500 personas del dataset y ver el conteo por estado, para validar las reglas y elegir los RUN de la demo.

#### Acceptance Criteria

1. WHEN el Batch_Detector se ejecuta sobre `data/raw/dataset_A_participantes/perfiles.json`, THE Batch_Detector SHALL asignar a cada uno de los 500 perfiles exactamente un estado del conjunto de PGU (`excluido`, `ya_recibe`, `futuro`, `no_elegible`, `antecedente_faltante`, `proximo`, `elegible`) y exactamente un estado del conjunto de jubilación (`excluido`, `pensionado`, `sin_afp`, `puede_pensionarse`, `proximo`, `futuro`).
2. WHEN el Batch_Detector termina de recorrer el archivo de perfiles, THE Batch_Detector SHALL informar el conteo por cada estado de PGU, el conteo por cada estado de jubilación, el conteo de perfiles no clasificados, el total de perfiles leídos, SHALL cuadrar que en cada conjunto la suma de los conteos por estado más los no clasificados iguale el total leído, y SHALL nombrar el RUN de cada perfil no clasificado.
3. WHEN el Batch_Detector se ejecuta dos veces sobre el mismo archivo de perfiles con la misma fecha de referencia, THE Batch_Detector SHALL devolver para cada RUN el mismo estado de PGU, el mismo estado de jubilación, el mismo motivo y el mismo monto estimado de PGU, con independencia de la fecha del sistema y del orden de lectura de los perfiles.
4. WHERE la fecha de referencia se entrega como parámetro en formato AAAA-MM-DD, THE Batch_Detector SHALL calcular las edades, los hitos y los estados a esa fecha y SHALL informar en el reporte la fecha de referencia aplicada.
5. IF un perfil carece de un campo requerido o lo trae nulo, trae una fecha no interpretable en formato AAAA-MM-DD, o trae un valor fuera del conjunto admitido para ese campo, THEN THE Batch_Detector SHALL registrar el RUN, el campo afectado y cuál de esas tres condiciones se detectó, SHALL dejar el perfil como no clasificado y SHALL continuar con los perfiles restantes sin abortar la ejecución.
6. WHEN un perfil queda en estado `excluido`, THE Batch_Detector SHALL marcarlo como no contactable, SHALL informar el motivo de la exclusión, SHALL dejarlo fuera de la lista de contacto y de la lista de campaña, y SHALL informar el conteo de perfiles `excluido`, que para el dataset A evaluado a su fecha de referencia es 20 personas fallecidas.
7. WHEN el Batch_Detector termina, THE Batch_Detector SHALL informar al menos un RUN de ejemplo por cada estado de PGU y por cada estado de jubilación cuyo conteo sea mayor que cero, y SHALL omitir del listado de ejemplos los estados con conteo igual a cero.
8. WHERE la fecha de referencia no se entrega como parámetro, THE Batch_Detector SHALL usar `FECHA_REFERENCIA` de `src/app/ruta/config.py`, cuyo valor para el dataset A es 2026-10-08, y SHALL abstenerse de usar la fecha del sistema.
9. WHEN el Batch_Detector clasifica los RUN `100000051-1` y `100000232-8` del dataset A a la fecha de referencia del dataset, THE Batch_Detector SHALL devolver para ambos el estado de PGU `antecedente_faltante` y SHALL identificar el antecedente ausente: el RSH para `100000051-1` y la residencia para `100000232-8`.
10. THE Batch_Detector SHALL completar la ejecución del lote sin realizar llamadas al modelo de lenguaje y sin incluir datos de perfiles en ningún mensaje dirigido al modelo.

### Requirement 10: Enganche con la interfaz

**User Story:** Como persona o como ejecutivo frente a la pantalla, quiero ver el resultado de la detección y conversar sobre el mismo caso, para no recibir dos versiones distintas de la misma situación.

#### Acceptance Criteria

1. WHILE el caso tiene autorización confirmada, WHEN la persona envía una pregunta en el chat, THE Chat_Bridge SHALL registrar en el Tool_Registry de ese turno las herramientas `leer_caso`, `evaluar_pgu`, `calcular_hitos` y `buscar_beneficios`, antes de la primera llamada al Agent.
2. WHEN el Agent responde sobre un estado, un monto, un requisito o una fecha, THE Interface SHALL mostrar el título de la fuente devuelta por la herramienta, su URL cuando la fuente la trae y el organismo o el dataset de origen cuando no la trae, y SHALL abstenerse de mostrar enlaces que ninguna herramienta devolvió.
3. WHEN un ejecutivo selecciona un RUN en la vista del ejecutivo, THE Interface SHALL mostrar el estado de PGU, el estado de jubilación, el estado y el detalle de cada requisito evaluado con su fuente, los hitos con su fecha, los trámites requeridos con sus documentos y el próximo paso, tomados del mismo resultado del Eligibility_Service.
4. WHILE al menos un paso del caso no está en estado `completado`, THE Interface SHALL señalar exactamente un próximo paso con su estado (`disponible`, `bloqueado` o `en_espera`) y SHALL abstenerse de señalar un segundo próximo paso.
5. IF una herramienta devuelve el sobre de error, THEN THE Interface SHALL mostrar un mensaje distinto para cada tipo recibido entre `not_found`, `permission_denied`, `invalid_input`, `unknown_tool` e `internal`, SHALL limitar el texto en pantalla al mensaje del sobre y SHALL conservar visible el último resultado determinista del caso.
6. THE Interface SHALL mostrar la etiqueta de orientación preliminar sujeta a validación del IPS o de la AFP en cada vista que presente un estado de PGU, un estado de jubilación o un monto estimado.
7. WHEN la persona o el ejecutivo marca un paso como completado, THE Interface SHALL recalcular con el Route_Engine, en la misma interacción, el estado de todos los pasos del caso y el próximo paso, y cada paso SHALL quedar en exactamente uno de los estados `completado`, `disponible`, `bloqueado` o `en_espera`.
8. WHEN la vista de la persona y la vista del ejecutivo presentan el mismo RUN con la misma fecha de referencia, THE Interface SHALL mostrar en ambas el mismo estado de PGU, el mismo estado de jubilación, el mismo estado por requisito y el mismo próximo paso.
9. IF todos los pasos del caso quedan en estado `completado`, THEN THE Interface SHALL informar el término de la ruta y el próximo hito aplicable, sin señalar un próximo paso.

### Requirement 11: Consentimiento y aislamiento por RUN

**User Story:** Como responsable del dato, quiero que ninguna detección individual lea un perfil sin autorización ni cruce el RUN de otra persona, para sostener la regla de consentimiento del proyecto.

#### Acceptance Criteria

1. IF el caso no tiene consentimiento vigente (invitación aceptada o sin invitación, y autorización otorgada y no revocada), THEN THE Profile_Repository SHALL lanzar `PermissionError` antes de abrir el dataset y THE Tool_Registry SHALL devolver un sobre con `error.type` igual a `permission_denied`, sin declarar si el RUN existe en el dataset.
2. WHILE el caso tiene consentimiento vigente, IF el RUN recibido como argumento no coincide con el RUN del caso tras normalizar ambos (el mismo RUN con o sin separadores de miles no es una discrepancia), THEN THE Profile_Repository SHALL lanzar `PermissionError` y THE Tool_Registry SHALL devolver un sobre con `error.type` igual a `permission_denied` que informe que el RUN consultado no corresponde al caso, sin nombrar el RUN del caso ni declarar si el RUN consultado existe en el dataset.
3. WHILE el caso no tiene consentimiento vigente, THE Chat_Bridge SHALL registrar en el Tool_Registry del turno únicamente `leer_caso` y `buscar_beneficios`, SHALL omitir `consultar_perfil`, `evaluar_pgu` y `calcular_hitos`, y THE Agent SHALL informar que la autorización se otorga en la Interface y SHALL abstenerse de afirmar estados, montos o fechas calculados sobre el perfil.
4. WHEN `consultar_perfil` devuelve un perfil, THE Tool_Registry SHALL entregar al modelo ese perfil sin el detalle mensual de cotizaciones y SHALL conservar los demás bloques del perfil.
5. WHERE la detección se ejecuta en lote para preparar campañas, THE Batch_Detector SHALL limitar la salida al RUN, el estado, los motivos, el hito y el segmento, y SHALL completar la ejecución sin invocar al Agent ni al cliente Converse.
6. THE Interface SHALL ser la única fuente del registro de aceptación y de autorización, THE Tool_Registry SHALL tomar el caso y su autorización del contexto que entrega la aplicación ignorando cualquier argumento del modelo que pretenda fijarlos, y THE Agent SHALL tratar una afirmación de autorización escrita en el chat como dato del caso y no como consentimiento.
7. WHEN la Interface registra la revocación de la autorización durante una conversación en curso, THE Profile_Repository SHALL denegar con `PermissionError` la primera lectura de perfil posterior a ese registro, y THE Chat_Bridge SHALL dejar de registrar `consultar_perfil`, `evaluar_pgu` y `calcular_hitos` en los turnos siguientes de la misma conversación.
8. WHILE la autorización está revocada, THE Chat_Bridge SHALL excluir del contexto enviado al modelo los mensajes y los resultados de herramienta obtenidos bajo la autorización anterior, y THE Interface SHALL conservar el registro del evento de revocación con su fecha y su canal.
9. WHILE el caso tiene consentimiento vigente, IF el RUN recibido como argumento no cumple el formato de RUN o tiene dígito verificador inválido, THEN THE Profile_Repository SHALL rechazar la consulta antes de abrir el dataset y THE Tool_Registry SHALL devolver un sobre de error que identifique el RUN como inválido, distinto de `permission_denied`.

### Requirement 12: Operación y verificación sin credenciales AWS

**User Story:** Como equipo que presenta en una hackatón, quiero que la detección y la demo funcionen sin Bedrock disponible, para no depender de la red ni de las credenciales durante la presentación.

#### Acceptance Criteria

1. WHERE `BEDROCK_MODEL_ID` está vacío, WHEN la persona envía una pregunta en el chat, THE Interface SHALL responder con las plantillas construidas desde el mismo contexto determinista del caso, SHALL informar que el asistente conversacional está desactivado identificando el motor de respuesta como plantillas, y SHALL abstenerse de abrir una sesión AWS o emitir llamadas de red.
2. THE Eligibility_Service SHALL producir, para el mismo perfil y la misma fecha de referencia, el mismo estado de PGU, el mismo estado de jubilación, los mismos motivos y los mismos trámites requeridos con `BEDROCK_MODEL_ID` vacío y con un modelo permitido configurado.
3. IF la ruta conversacional hacia Bedrock lanza cualquier excepción (configuración de modelo rechazada, credenciales ausentes, modelo no habilitado o falla de red), THEN THE Chat_Bridge SHALL entregar la respuesta por plantillas sobre el mismo contexto determinista, SHALL agregar un aviso de que la explicación conversacional no está disponible, y SHALL conservar sin cambios el estado, los motivos y los trámites mostrados.
4. WHEN la Verification_Suite se ejecuta sin credenciales AWS configuradas, THE Verification_Suite SHALL completar todas sus comprobaciones sin emitir llamadas de red, usando el cliente Converse falso inyectado en las pruebas del Agent, y SHALL abstenerse de omitir pruebas por credenciales ausentes.
5. WHEN `uv run pytest` y `uv run ruff check .` se ejecutan en la raíz del repositorio, THE Verification_Suite SHALL terminar sin pruebas fallidas y sin hallazgos de lint bajo el límite de 100 caracteres por línea configurado en el repositorio.
6. WHEN el verificador de dominio `src/app/verificar.py` se ejecuta, THE Verification_Suite SHALL fijar `BEDROCK_MODEL_ID` en vacío antes de evaluar, SHALL informar el conteo por estado de los 500 perfiles del dataset A y el total evaluado, y SHALL nombrar el RUN de cada perfil cuya clasificación no pudo determinarse por antecedente faltante.
7. IF `BEDROCK_MODEL_ID` contiene un valor distinto de `us.anthropic.claude-sonnet-5`, `us.anthropic.claude-opus-5` o `us.anthropic.claude-haiku-4-5`, THEN THE Chat_Bridge SHALL rechazar la configuración con un error que identifique el modelo no permitido, antes de abrir la sesión AWS y sin emitir ninguna llamada de red.
8. IF una comprobación del verificador de dominio no cuadra con los conteos conocidos del dataset A, THEN THE Verification_Suite SHALL señalar la ejecución como fallida y SHALL nombrar cada comprobación incumplida con el RUN afectado cuando corresponda a un perfil.
