"""Motor de rutas: convierte un diagnóstico en pasos concretos con dependencias.

Pasos de tipo "persona" los completa la persona; los de tipo "organismo" solo
cambian cuando el organismo reporta su estado (en el MVP se simula).
"""
from dataclasses import asdict, dataclass, field
from datetime import date

from . import config
from . import reglas as R
from .fechas import fmt

F = config.FUENTES


@dataclass
class Paso:
    id: str
    tramite: str                  # "Jubilación" | "PGU" | "Antecedentes" | "Seguimiento"
    titulo: str
    que_hacer: str
    donde: str
    documentos: list[str] = field(default_factory=list)
    depende_de: list[str] = field(default_factory=list)
    disponible_desde: date | None = None
    tipo: str = "persona"         # persona | organismo
    fuente: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


CANAL_CHILEATIENDE = "chileatiende.gob.cl con ClaveÚnica, Call center 101 o sucursal ChileAtiende"


def _ruta_jubilacion(d: R.Diagnostico) -> list[Paso]:
    j, h = d.jubilacion, d.hitos
    if j.resultado not in ("proximo", "puede_pensionarse"):
        return []
    desde = h.fecha_edad_legal
    return [
        Paso("J1", "Jubilación", "Revisar tu saldo y pensión estimada",
             f"Pide tu cartola y una simulación de pensión en {j.afp}. "
             + (f"Hoy la pensión autofinanciada estimada es ${j.pafe_estimada:,.0f} (valor simulado).".replace(",", ".")
                if j.pafe_estimada else ""),
             f"{j.afp} (sitio web, app o sucursal)", ["Cédula de identidad", "ClaveÚnica o clave AFP"],
             fuente=F["spensiones"]),
        Paso("J2", "Jubilación", "Solicitar la pensión de vejez en tu AFP",
             f"Desde el {fmt(desde)} puedes pedirla. Es voluntario: también puedes seguir trabajando.",
             f"{j.afp}", ["Cédula de identidad"], depende_de=["J1"], disponible_desde=desde,
             fuente=F["spensiones"]),
        Paso("J3", "Jubilación", "Revisar ofertas (SCOMP) y elegir modalidad",
             "La AFP te entrega el Certificado de Ofertas. Compara retiro programado y renta vitalicia antes de decidir.",
             "AFP / asesor previsional", ["Certificado de Ofertas SCOMP"], depende_de=["J2"],
             fuente=F["spensiones"]),
        Paso("J4", "Jubilación", "La AFP o compañía resuelve tu pensión",
             "El organismo informa la resolución y la fecha del primer pago.",
             "AFP / Compañía de seguros", depende_de=["J3"], tipo="organismo", fuente=F["spensiones"]),
    ]


def _ruta_antecedentes(d: R.Diagnostico) -> list[Paso]:
    pasos: list[Paso] = []
    req = {r.id: r for r in d.pgu.requisitos}
    if req["pfp"].estado == R.FALTA:
        sin_rsh = "No tiene" in req["pfp"].detalle
        pasos.append(Paso(
            "A1", "Antecedentes",
            "Ingresar al Registro Social de Hogares" if sin_rsh else "Completar o actualizar tu Registro Social de Hogares",
            "Sin el RSH no se puede calcular el Puntaje de Focalización Previsional, que se usa para la PGU."
            if sin_rsh else "Tu RSH no tiene información suficiente para calcular el PFP. Actualiza los datos de tu hogar.",
            "registrosocial.gob.cl con ClaveÚnica o tu municipalidad",
            ["Cédula de identidad de los integrantes del hogar", "ClaveÚnica"], fuente=F["rsh"]))
        pasos.append(Paso("A2", "Antecedentes", "La municipalidad / Ministerio confirma tu RSH",
                          "Cuando el RSH quede vigente, retomamos tu ruta de PGU sin empezar de cero.",
                          "Municipalidad / Ministerio de Desarrollo Social", depende_de=["A1"],
                          tipo="organismo", fuente=F["rsh"]))
    if req["residencia"].estado == R.FALTA:
        pasos.append(Paso("A3", "Antecedentes", "Reunir antecedentes de residencia en Chile",
                          "No encontramos tu registro de entradas y salidas. Solicita tu certificado de viajes "
                          "y tenlo a mano al pedir la PGU.",
                          "PDI (certificado de viajes) y luego ChileAtiende", ["Cédula de identidad"],
                          fuente=F["pdi"]))
    return pasos


def _ruta_pgu(d: R.Diagnostico, previos: list[str]) -> list[Paso]:
    pgu, h = d.pgu, d.hitos
    if pgu.resultado not in (R.ELEGIBLE, R.PROXIMO, R.ANTECEDENTE_FALTANTE):
        return []
    reg = pgu.pgu_registro
    suspendida = reg is not None and reg["estado"] == "suspendido"
    monto = f"${pgu.monto_estimado:,.0f}".replace(",", ".")
    pasos = [
        Paso("G0", "PGU", "Entender la PGU y tu monto orientativo",
             f"La PGU es un aporte mensual del Estado desde los 65 años. Con tu pensión base de "
             f"${pgu.pension_base:,.0f} ".replace(",", ".") + f"el monto orientativo sería {monto} al mes. "
             "El monto definitivo lo calcula el IPS.",
             "Este asistente / ficha ChileAtiende", fuente=F["pgu"]),
        Paso("G1", "PGU",
             "Pedir la reanudación de tu PGU" if suspendida else "Solicitar la PGU",
             ("Tu PGU está suspendida. Una vez resuelto el antecedente faltante, pide que se revise."
              if suspendida else
              f"Puedes solicitarla desde el {fmt(h.fecha_apertura_pgu)} (64 años y 9 meses); se paga desde los 65 si cumples los requisitos."),
             CANAL_CHILEATIENDE, ["Cédula de identidad", "ClaveÚnica (si es en línea)"],
             depende_de=["G0", *previos],
             disponible_desde=None if suspendida else h.fecha_apertura_pgu, fuente=F["pgu"]),
        Paso("G2", "PGU", "El IPS evalúa y comunica su resolución",
             "El IPS valida requisitos con las fuentes oficiales y responde. Te avisaremos el resultado y el siguiente paso.",
             "IPS / ChileAtiende", depende_de=["G1"], tipo="organismo", fuente=F["pgu"]),
    ]
    return pasos


def _ruta_cierre(d: R.Diagnostico) -> list[Paso]:
    """Paso 6 del PPT: cerrar y anticipar el próximo hito."""
    h, pgu = d.hitos, d.pgu
    if pgu.resultado == R.YA_RECIBE:
        return [Paso("S1", "Seguimiento", "Revisar tu pago de PGU",
                     f"Recibes la PGU. A los 75 años ({fmt(h.fecha_tramo_75)}) el monto máximo sube a "
                     f"${config.PGU['monto_max_75_mas']:,.0f}.".replace(",", ".") if h.edad < 75 else
                     "Recibes la PGU con el monto máximo del tramo 75+.",
                     "ChileAtiende", fuente=F["pgu_aumento"])]
    if pgu.resultado == R.NO_ELEGIBLE:
        fallas = [r for r in pgu.requisitos if r.estado == R.NO_CUMPLE]
        consejos = []
        for r in fallas:
            if r.id == "pfp":
                consejos.append("Si los ingresos de tu hogar cambian, actualiza tu RSH y volvemos a revisar.")
            elif r.id == "residencia":
                consejos.append("Si tienes periodos de residencia no registrados, consúltalo en ChileAtiende.")
            elif r.id == "pension_base":
                consejos.append("Tu pensión base supera el límite de la PGU.")
        return [Paso("S2", "Seguimiento", "Entender por qué hoy no corresponde la PGU",
                     " ".join(consejos) + " Esto es una orientación: el IPS es quien resuelve.",
                     "ChileAtiende", fuente=F["pgu"])]
    if pgu.resultado == R.FUTURO and d.jubilacion.resultado == "futuro":
        return [Paso("S3", "Seguimiento", "Te avisaremos a tiempo",
                     f"Te contactaremos el {fmt(h.fecha_invitacion_jubilacion)} para preparar tu jubilación "
                     f"y el {fmt(h.fecha_apertura_pgu)} para la PGU.", "ChileAtiende", tipo="organismo")]
    return []


def generar_ruta(d: R.Diagnostico) -> list[Paso]:
    if not d.vivo:
        return []
    jub = _ruta_jubilacion(d)
    ant = _ruta_antecedentes(d)
    # Bloqueantes de la PGU: confirmación del RSH (A2) y certificado de residencia (A3).
    bloqueantes = [p.id for p in ant if p.id in ("A2", "A3")]
    return jub + ant + _ruta_pgu(d, bloqueantes) + _ruta_cierre(d)


def estado_pasos(ruta: list[Paso], completados: set[str], ref: date = config.FECHA_REFERENCIA) -> dict[str, str]:
    """completado | disponible | bloqueado | en_espera (fecha futura)."""
    out = {}
    for p in ruta:
        if p.id in completados:
            out[p.id] = "completado"
        elif any(dep not in completados for dep in p.depende_de):
            out[p.id] = "bloqueado"
        elif p.disponible_desde and p.disponible_desde > ref:
            out[p.id] = "en_espera"
        else:
            out[p.id] = "disponible"
    return out


def proximo_paso(ruta: list[Paso], estados: dict[str, str]) -> Paso | None:
    for p in ruta:
        if estados[p.id] == "disponible":
            return p
    for p in ruta:
        if estados[p.id] == "en_espera":
            return p
    return None
