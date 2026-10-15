"""Demo benefit catalog, loaded into the `Beneficios` table.

Requirements are SIMPLIFIED for the demo. Only the PGU cites its official
ficha (parameters as in src/app/ruta/config.py); every other entry stays
`verificado: False` until checked against ChileAtiende. No amounts are given.
"""

CHILEATIENDE = "https://www.chileatiende.gob.cl/"
PGU_URL = "https://www.chileatiende.gob.cl/fichas/102077-pension-garantizada-universal-pgu"


def _unverified(nombre: str) -> dict:
    return {
        "titulo": f"Buscar «{nombre}» en ChileAtiende (requisitos por verificar)",
        "url": CHILEATIENDE,
        "verificado": False,
    }


BENEFICIOS = [
    {
        "beneficio_id": "pgu",
        "nombre": "Pensión Garantizada Universal (PGU)",
        "evento": "Cumplir 65 años",
        "descripcion": (
            "La PGU es un aporte mensual del Estado para personas de 65 años o más que no "
            "pertenecen al 10% de mayores ingresos. Se paga aunque sigas trabajando y se suma a "
            "tu pensión, si la tienes."
        ),
        "por_que_te_conviene": (
            "Sería un ingreso todos los meses que complementa tu pensión, o que te da un ingreso "
            "si no tienes pensión. Mientras antes la solicites, antes empezarías a recibirla."
        ),
        # Maximums from the ficha (src/app/ruta/config.py); the IPS computes the real amount.
        "monto_referencial": (
            "Hasta $231.732 al mes entre los 65 y 74 años, y hasta $250.275 desde los 75 años. "
            "Son montos máximos referenciales: el monto que podrías recibir depende de tu "
            "pensión y de tu situación, y puede ser menor."
        ),
        "titulo_elegible": "¡Felicidades, {nombre}! Aparentemente eres elegible para la PGU",
        "boton": "Quiero solicitar la PGU",
        # Age in months: 64 → prepare; 64 + 8 → one month before the opening.
        "apertura_meses": 64 * 12 + 9,
        "avisos_previos": [
            {
                "id": "preparacion",
                "meses": 64 * 12,
                "titulo": "{nombre}, prepárate: desde el {apertura} podrías solicitar la PGU",
                "motivo": (
                    "Cumpliste 64 años. Desde los 64 años y 9 meses ({apertura}) puedes iniciar "
                    "la solicitud de la PGU, para que, si se aprueba, empieces a recibirla al "
                    "cumplir 65 ({acceso}). Te escribimos ahora para que tengas tiempo de "
                    "reunir tus documentos y revisar si te falta algo."
                ),
                "boton": "Quiero prepararme con ChileAtiende",
            },
            {
                "id": "recordatorio",
                "meses": 64 * 12 + 8,
                "titulo": "{nombre}, falta un mes: el {apertura} se abre tu solicitud de PGU",
                "motivo": (
                    "Tienes 64 años y 8 meses. El {apertura} se abre tu solicitud de la PGU. "
                    "Si la inicias apenas se abra, podrías empezar a recibirla desde que cumplas "
                    "65 ({acceso}). No es un plazo que vence: puedes solicitarla después, pero "
                    "mientras antes la pidas, antes la recibirías."
                ),
                "boton": "Quiero iniciar mi trámite a tiempo",
            },
        ],
        "documentos": [
            "Cédula de identidad vigente",
            "Registro Social de Hogares al día (si no lo tienes, pídelo en tu municipalidad)",
            "Si viviste fuera de Chile, antecedentes de tus años de residencia en el país",
        ],
        # Loss-risk notices for people who already receive the PGU. Threshold from the
        # team's demo brief, NOT verified with the IPS.
        "riesgos": [
            {
                "id": "fuera_de_chile",
                "campo": "dias_fuera_ultimo_anio",
                "op": ">=",
                "valor": 150,
                "titulo": "{nombre}, atención: tu PGU podría verse afectada",
                "motivo": (
                    "Registramos {valor} días fuera de Chile en los últimos 12 meses. "
                    "Permanecer más de 6 meses fuera del país podría hacerte perder la PGU."
                ),
                "explicacion": (
                    "Para mantener la PGU se revisa tu residencia en Chile. Si planeas seguir "
                    "fuera o ya volviste, consulta tu caso antes de que tu pago se vea afectado."
                ),
                "boton": "Quiero revisar mi situación",
                "paso_siguiente": (
                    "Consulta tu caso en ChileAtiende (web, 101 o sucursal) e informa tus fechas "
                    "de viaje. El IPS revisa y decide si tu PGU se mantiene."
                ),
            }
        ],
        "requisitos": [
            {"campo": "edad", "op": ">=", "valor": 65, "texto": "Tener 65 años o más"},
            {
                "campo": "percentil_pfp",
                "op": "<=",
                "valor": 90,
                "texto": "No pertenecer al 10% de mayores ingresos",
            },
            {
                "campo": "residencia_cumple",
                "op": "==",
                "valor": True,
                "texto": "Cumplir el requisito de residencia en Chile",
            },
            {
                "campo": "pension_base",
                "op": "<",
                "valor": 1_252_602,
                "texto": "Pensión base bajo el límite de la PGU",
            },
        ],
        "paso_siguiente": "Solicita la PGU en ChileAtiende (web, 101 o sucursal) con tu cédula.",
        "fuente": {
            "titulo": "Ficha PGU · ChileAtiende",
            "url": PGU_URL,
            "verificado": True,
        },
    },
    {
        "beneficio_id": "subsidio_empleo_joven",
        "nombre": "Subsidio al Empleo Joven",
        "evento": "Cumplir 18 años trabajando",
        "descripcion": (
            "Es un aporte para jóvenes de 18 a 24 años que trabajan y pertenecen a los hogares "
            "más vulnerables, que complementa su sueldo."
        ),
        "por_que_te_conviene": (
            "Te ayuda a aumentar tus ingresos mientras trabajas, sin cambiar de empleo."
        ),
        "boton": "Quiero postular",
        "requisitos": [
            {"campo": "edad", "op": ">=", "valor": 18, "texto": "Tener 18 años o más"},
            {"campo": "edad", "op": "<=", "valor": 24, "texto": "Tener 24 años o menos"},
            {"campo": "trabaja", "op": "==", "valor": True, "texto": "Estar trabajando"},
            {
                "campo": "tramo_rsh",
                "op": "<=",
                "valor": 40,
                "texto": "Pertenecer al 40% más vulnerable según el RSH",
            },
        ],
        "anticipar_dias": 30,
        "paso_siguiente": "Postula al Subsidio al Empleo Joven en ChileAtiende o en SENCE.",
        "fuente": _unverified("Subsidio al Empleo Joven"),
    },
    {
        "beneficio_id": "suf",
        "nombre": "Subsidio Único Familiar (SUF)",
        "evento": "Tener un hijo",
        "descripcion": (
            "Es un aporte mensual para familias vulnerables por cada hijo o hija a cargo que no "
            "recibe asignación familiar."
        ),
        "por_que_te_conviene": "Te ayuda con los gastos de crianza desde los primeros meses.",
        "boton": "Quiero solicitarlo",
        "requisitos": [
            {"campo": "num_hijos", "op": ">=", "valor": 1, "texto": "Tener hijos a cargo"},
            {
                "campo": "tramo_rsh",
                "op": "<=",
                "valor": 60,
                "texto": "Pertenecer al 60% más vulnerable según el RSH",
            },
        ],
        "paso_siguiente": "Solicita el SUF en tu municipalidad con el certificado de nacimiento.",
        "fuente": _unverified("Subsidio Único Familiar"),
    },
    {
        "beneficio_id": "bono_por_hijo",
        "nombre": "Bono por Hijo",
        "evento": "Mujer con hijos que cumple 65 años",
        "descripcion": (
            "Es un bono que aumenta la pensión de las mujeres por cada hijo nacido vivo o adoptado."
        ),
        "por_que_te_conviene": "Al cumplir 65 años se suma a tu pensión de forma permanente.",
        "boton": "Quiero solicitarlo",
        "requisitos": [
            {"campo": "sexo", "op": "==", "valor": "F", "texto": "Ser mujer"},
            {"campo": "edad", "op": ">=", "valor": 65, "texto": "Tener 65 años o más"},
            {"campo": "num_hijos", "op": ">=", "valor": 1, "texto": "Tener al menos un hijo"},
        ],
        "anticipar_dias": 90,
        "paso_siguiente": "Solicita el Bono por Hijo en el IPS o en ChileAtiende.",
        "fuente": _unverified("Bono por hijo"),
    },
    {
        "beneficio_id": "asignacion_conyuge",
        "nombre": "Asignación Familiar por cónyuge",
        "evento": "Casarse o firmar un AUC",
        "descripcion": (
            "Es un aporte mensual para trabajadores que tienen a su cónyuge o conviviente civil "
            "como carga familiar."
        ),
        "por_que_te_conviene": "Aumenta los ingresos de tu familia todos los meses.",
        "boton": "Quiero solicitarla",
        "requisitos": [
            {
                "campo": "estado_civil",
                "op": "in",
                "valor": ["casado", "AUC"],
                "texto": "Estar casado o con Acuerdo de Unión Civil",
            },
            {"campo": "trabaja", "op": "==", "valor": True, "texto": "Estar trabajando"},
            {
                "campo": "tramo_rsh",
                "op": "<=",
                "valor": 60,
                "texto": "Pertenecer al 60% más vulnerable según el RSH",
            },
        ],
        "paso_siguiente": "Pide a tu empleador o caja de compensación tramitar la asignación.",
        "fuente": _unverified("Asignación Familiar"),
    },
    {
        "beneficio_id": "bodas_de_oro",
        "nombre": "Bono Bodas de Oro",
        "evento": "Cumplir 50 años de matrimonio",
        "descripcion": "Es un bono para matrimonios que cumplen 50 años de casados.",
        "por_que_te_conviene": "Es un reconocimiento en dinero para cada cónyuge.",
        "boton": "Quiero solicitarlo",
        "requisitos": [
            {
                "campo": "anios_casado",
                "op": ">=",
                "valor": 50,
                "texto": "Cumplir 50 años de matrimonio",
            },
            {
                "campo": "tramo_rsh",
                "op": "<=",
                "valor": 80,
                "texto": "Pertenecer al 80% más vulnerable según el RSH",
            },
        ],
        "paso_siguiente": "Solicita el Bono Bodas de Oro en ChileAtiende junto a tu cónyuge.",
        "fuente": _unverified("Bono Bodas de Oro"),
    },
    {
        "beneficio_id": "seguro_laboral",
        "nombre": "Seguro de accidentes del trabajo (Ley 16.744)",
        "evento": "Accidente laboral",
        "descripcion": (
            "El seguro de la Ley 16.744 cubre la atención médica, los subsidios y las "
            "indemnizaciones por accidentes del trabajo o de trayecto."
        ),
        "por_que_te_conviene": "Cubre tu tratamiento y tus días de licencia mientras te recuperas.",
        "boton": "Quiero orientación",
        "requisitos": [
            {
                "campo": "accidente_laboral",
                "op": "==",
                "valor": True,
                "texto": "Haber tenido un accidente del trabajo o de trayecto",
            },
            {"campo": "trabaja", "op": "==", "valor": True, "texto": "Estar trabajando"},
        ],
        "paso_siguiente": "Acude a tu mutualidad o al ISL con la denuncia del accidente (DIAT).",
        "fuente": _unverified("Seguro laboral Ley 16.744"),
    },
    {
        "beneficio_id": "subsidio_electrico",
        "nombre": "Subsidio Eléctrico",
        "evento": "Cambio de tramo en el Registro Social de Hogares",
        "descripcion": (
            "Es un descuento en la cuenta de la luz para los hogares más vulnerables según el "
            "Registro Social de Hogares."
        ),
        "por_que_te_conviene": (
            "Te ayuda a pagar menos por la electricidad mientras dure el subsidio."
        ),
        "boton": "Quiero postular",
        "requisitos": [
            {
                "campo": "tramo_rsh",
                "op": "<=",
                "valor": 80,
                "texto": "Pertenecer al 80% más vulnerable según el RSH",
            },
        ],
        "paso_siguiente": "Postula al Subsidio Eléctrico en ChileAtiende.",
        "fuente": _unverified("Subsidio Eléctrico"),
    },
]
