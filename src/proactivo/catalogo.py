"""Demo benefit catalog, loaded into the `Beneficios` table.

Requirements are SIMPLIFIED for the demo. Only the PGU cites its official
ficha (parameters as in src/app/ruta/config.py); every other entry stays
`verificado: False` until checked against ChileAtiende. Texts address the
person formally ("usted").
"""

CHILEATIENDE = "https://www.chileatiende.gob.cl/"
PGU_URL = "https://www.chileatiende.gob.cl/fichas/102077-pension-garantizada-universal-pgu"


def _unverified(nombre: str) -> dict:
    return {
        "titulo": f"Buscar «{nombre}» en ChileAtiende (requisitos por verificar)",
        "url": CHILEATIENDE,
        "verificado": False,
    }


def _rsh(percent: int) -> dict:
    return {
        "campo": "tramo_rsh",
        "op": "<=",
        "valor": percent,
        "texto": f"Pertenecer al {percent}% más vulnerable según el RSH",
    }


BENEFICIOS = [
    {
        "beneficio_id": "pgu",
        "nombre": "Pensión Garantizada Universal (PGU)",
        "evento": "Cumplir 65 años",
        "descripcion": (
            "La Pensión Garantizada Universal es un aporte mensual del Estado para personas de "
            "65 años o más que no pertenecen al 10% de mayores ingresos de la población. Es "
            "compatible con continuar trabajando y se suma a la pensión que usted perciba, si "
            "corresponde."
        ),
        "por_que_te_conviene": (
            "Constituiría un ingreso mensual que complementa su pensión o que, si usted no "
            "recibe pensión, le proporcionaría un ingreso. Mientras antes la solicite, antes "
            "podría comenzar a recibirla."
        ),
        # Maximums from the ficha (src/app/ruta/config.py); the IPS computes the real amount.
        "monto_referencial": (
            "Hasta $231.732 mensuales entre los 65 y 74 años, y hasta $250.275 desde los 75 "
            "años. Se trata de montos máximos referenciales: el monto que usted podría recibir "
            "depende de su pensión y de su situación particular, y puede ser inferior."
        ),
        "titulo_elegible": "Felicitaciones: aparentemente usted es elegible para la PGU",
        "boton": "Solicitar la PGU",
        # Age in months: 64 → prepare; 64 + 8 → one month before the opening.
        "apertura_meses": 64 * 12 + 9,
        "avisos_previos": [
            {
                "id": "preparacion",
                "meses": 64 * 12,
                "titulo": "Prepare su trámite: desde el {apertura} podrá solicitar la PGU",
                "motivo": (
                    "Junto con saludarle, le informamos que usted cumplió 64 años. A partir de "
                    "los 64 años y 9 meses ({apertura}) podrá iniciar la solicitud de la "
                    "Pensión Garantizada Universal, de modo que, si es aprobada, comience a "
                    "recibirla al cumplir 65 años ({acceso}). Le escribimos con anticipación "
                    "para que disponga de tiempo para reunir sus documentos y verificar si le "
                    "falta algún antecedente."
                ),
                "boton": "Preparar mi trámite con ChileAtiende",
            },
            {
                "id": "recordatorio",
                "meses": 64 * 12 + 8,
                "titulo": "Falta un mes: el {apertura} se abre su solicitud de la PGU",
                "motivo": (
                    "Junto con saludarle, le informamos que el {apertura} se abre el período "
                    "para solicitar su Pensión Garantizada Universal. Si presenta la solicitud "
                    "en cuanto se abra, podría comenzar a recibirla desde que cumpla 65 años "
                    "({acceso}). Esta fecha no corresponde a un plazo de vencimiento: puede "
                    "presentar la solicitud con posterioridad; sin embargo, mientras antes la "
                    "presente, antes podría recibir el beneficio."
                ),
                "boton": "Iniciar mi trámite oportunamente",
            },
        ],
        "documentos": [
            "Cédula de identidad vigente",
            "Registro Social de Hogares actualizado (si no cuenta con él, puede solicitarlo en "
            "su municipalidad)",
            "Si residió fuera de Chile, antecedentes que acrediten sus años de residencia en el "
            "país",
        ],
        # Loss-risk notices for people who already receive the PGU. Threshold from the
        # team's demo brief, NOT verified with the IPS.
        "riesgos": [
            {
                "id": "fuera_de_chile",
                "campo": "dias_fuera_ultimo_anio",
                "op": ">=",
                "valor": 150,
                "titulo": "Atención: su PGU podría verse afectada",
                "motivo": (
                    "Junto con saludarle, le informamos que registramos {valor} días fuera de "
                    "Chile en los últimos 12 meses. Permanecer más de 6 meses fuera del país "
                    "podría ocasionar la pérdida de la PGU."
                ),
                "explicacion": (
                    "Para mantener la PGU se considera su residencia en Chile. Si planea "
                    "permanecer fuera del país o ya regresó, le recomendamos consultar su caso "
                    "antes de que su pago se vea afectado."
                ),
                "boton": "Revisar mi situación",
                "paso_siguiente": (
                    "Le recomendamos consultar su caso en ChileAtiende (sitio web, 101 o "
                    "sucursal) e informar sus fechas de viaje. El IPS revisará la información y "
                    "resolverá si su PGU se mantiene."
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
        "paso_siguiente": (
            "Presente su solicitud de PGU en ChileAtiende (sitio web, 101 o sucursal) con su "
            "cédula de identidad."
        ),
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
            "más vulnerables, que complementa su remuneración."
        ),
        "por_que_te_conviene": (
            "Le permite aumentar sus ingresos mientras trabaja, sin cambiar de empleo."
        ),
        "boton": "Postular al subsidio",
        "requisitos": [
            {"campo": "edad", "op": ">=", "valor": 18, "texto": "Tener 18 años o más"},
            {"campo": "edad", "op": "<=", "valor": 24, "texto": "Tener 24 años o menos"},
            {"campo": "trabaja", "op": "==", "valor": True, "texto": "Estar trabajando"},
            _rsh(40),
        ],
        "anticipar_dias": 30,
        "paso_siguiente": "Postule al Subsidio al Empleo Joven en ChileAtiende o en SENCE.",
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
        "por_que_te_conviene": "Contribuye a los gastos de crianza desde los primeros meses.",
        "boton": "Solicitar el beneficio",
        "requisitos": [
            {"campo": "num_hijos", "op": ">=", "valor": 1, "texto": "Tener hijos a cargo"},
            _rsh(60),
        ],
        "paso_siguiente": (
            "Solicite el SUF en su municipalidad presentando el certificado de nacimiento."
        ),
        "fuente": _unverified("Subsidio Único Familiar"),
    },
    {
        "beneficio_id": "bono_por_hijo",
        "nombre": "Bono por Hijo",
        "evento": "Mujer con hijos que cumple 65 años",
        "descripcion": (
            "Es un bono que aumenta la pensión de las mujeres por cada hijo nacido vivo o adoptado."
        ),
        "por_que_te_conviene": "Al cumplir 65 años se suma a su pensión de forma permanente.",
        "boton": "Solicitar el beneficio",
        "requisitos": [
            {"campo": "sexo", "op": "==", "valor": "F", "texto": "Ser mujer"},
            {"campo": "edad", "op": ">=", "valor": 65, "texto": "Tener 65 años o más"},
            {"campo": "num_hijos", "op": ">=", "valor": 1, "texto": "Tener al menos un hijo"},
        ],
        "anticipar_dias": 90,
        "paso_siguiente": "Solicite el Bono por Hijo en el IPS o en ChileAtiende.",
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
        "por_que_te_conviene": "Incrementa mensualmente los ingresos de su grupo familiar.",
        "boton": "Solicitar el beneficio",
        "requisitos": [
            {
                "campo": "estado_civil",
                "op": "in",
                "valor": ["casado", "AUC"],
                "texto": "Estar casado o con Acuerdo de Unión Civil",
            },
            {"campo": "trabaja", "op": "==", "valor": True, "texto": "Estar trabajando"},
            _rsh(60),
        ],
        "paso_siguiente": (
            "Solicite a su empleador o caja de compensación la tramitación de la asignación."
        ),
        "fuente": _unverified("Asignación Familiar"),
    },
    {
        "beneficio_id": "bodas_de_oro",
        "nombre": "Bono Bodas de Oro",
        "evento": "Cumplir 50 años de matrimonio",
        "descripcion": "Es un bono para matrimonios que cumplen 50 años de casados.",
        "por_que_te_conviene": "Es un reconocimiento en dinero para cada cónyuge.",
        "boton": "Solicitar el beneficio",
        "requisitos": [
            {
                "campo": "anios_casado",
                "op": ">=",
                "valor": 50,
                "texto": "Cumplir 50 años de matrimonio",
            },
            _rsh(80),
        ],
        "paso_siguiente": "Solicite el Bono Bodas de Oro en ChileAtiende junto a su cónyuge.",
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
        "por_que_te_conviene": (
            "Cubre su tratamiento y sus días de licencia médica durante su recuperación."
        ),
        "boton": "Solicitar orientación",
        "requisitos": [
            {
                "campo": "accidente_laboral",
                "op": "==",
                "valor": True,
                "texto": "Haber tenido un accidente del trabajo o de trayecto",
            },
            {"campo": "trabaja", "op": "==", "valor": True, "texto": "Estar trabajando"},
        ],
        "paso_siguiente": (
            "Acuda a su mutualidad o al ISL con la denuncia individual del accidente (DIAT)."
        ),
        "fuente": _unverified("Seguro laboral Ley 16.744"),
    },
    {
        "beneficio_id": "subsidio_electrico",
        "nombre": "Subsidio Eléctrico",
        "evento": "Cambio de tramo en el Registro Social de Hogares",
        "descripcion": (
            "Es un descuento en la cuenta de electricidad para los hogares más vulnerables según "
            "el Registro Social de Hogares."
        ),
        "por_que_te_conviene": (
            "Le permite reducir el pago de su cuenta de electricidad mientras dure el subsidio."
        ),
        "boton": "Postular al subsidio",
        "requisitos": [_rsh(80)],
        "paso_siguiente": "Postule al Subsidio Eléctrico en ChileAtiende.",
        "fuente": _unverified("Subsidio Eléctrico"),
    },
]
