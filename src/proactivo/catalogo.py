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
        # The application opens at 64 years and 9 months.
        "anticipar_dias": 90,
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
