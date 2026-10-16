"""Motor de reglas: hitos, orientación PGU, orientación de jubilación.

Todo es determinista y trazable. El resultado es una ORIENTACIÓN preliminar:
la decisión oficial la toman la AFP / IPS / organismo correspondiente.
"""
from dataclasses import asdict, dataclass, field
from datetime import date

from . import config
from .fechas import cumple, edad, meses_entre, sumar_meses

# Estados de un requisito
CUMPLE, NO_CUMPLE, FALTA, PENDIENTE = "cumple", "no_cumple", "falta_antecedente", "pendiente"

# Resultados PGU (orden = precedencia)
EXCLUIDO = "excluido"                    # fallecido: no se contacta
YA_RECIBE = "ya_recibe"                  # PGU vigente
FUTURO = "futuro"                        # falta más de 12 meses para los 65
NO_ELEGIBLE = "no_elegible"              # incumple un requisito verificable
ANTECEDENTE_FALTANTE = "antecedente_faltante"
PROXIMO = "proximo"                      # cumple 65 dentro de 12 meses, resto en orden
ELEGIBLE = "elegible"                    # orientación: podría solicitar


@dataclass
class Requisito:
    id: str
    nombre: str
    estado: str
    detalle: str
    fuente: str


@dataclass
class Hitos:
    edad: int
    sexo: str
    edad_legal: int
    fecha_invitacion_jubilacion: date
    fecha_edad_legal: date
    fecha_apertura_pgu: date
    fecha_acceso_pgu: date
    fecha_tramo_75: date


@dataclass
class EvaluacionPGU:
    resultado: str
    motivo: str
    requisitos: list[Requisito]
    pension_base: int
    pension_base_origen: str
    monto_max: int
    monto_estimado: int
    pgu_registro: dict | None          # último registro PGU (vigente/suspendido/terminado)


@dataclass
class EvaluacionJubilacion:
    resultado: str                     # futuro | proximo | puede_pensionarse | pensionado | sin_afp | excluido
    motivo: str
    afiliado_afp: bool
    afp: str | None
    pafe_estimada: int | None
    pensiones_vigentes: list[dict] = field(default_factory=list)


@dataclass
class Diagnostico:
    run: str
    nombre: str
    vivo: bool
    hitos: Hitos
    pgu: EvaluacionPGU
    jubilacion: EvaluacionJubilacion
    segmento: str                      # para la campaña de invitación
    invitar: bool
    razon_invitacion: str

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
def calcular_hitos(perfil: dict, ref: date = config.FECHA_REFERENCIA) -> Hitos:
    rc = perfil["registro_civil"]
    fn = date.fromisoformat(rc["fecha_nacimiento"])
    edad_legal = config.EDAD_LEGAL_VEJEZ[rc["sexo"]]
    f_legal = cumple(fn, edad_legal)
    a, m = config.PGU["apertura_solicitud"]
    return Hitos(
        edad=edad(fn, ref),
        sexo=rc["sexo"],
        edad_legal=edad_legal,
        fecha_invitacion_jubilacion=sumar_meses(f_legal, -config.MESES_INVITACION_ANTICIPADA),
        fecha_edad_legal=f_legal,
        fecha_apertura_pgu=cumple(fn, a, m),
        fecha_acceso_pgu=cumple(fn, config.PGU["edad_acceso"]),
        fecha_tramo_75=cumple(fn, config.PGU["edad_tramo_superior"]),
    )


def _pensiones_vigentes(perfil: dict) -> list[dict]:
    return [
        p for p in perfil.get("pensiones_beneficios") or []
        if p["tipo_registro"] == "pension" and p["estado"] == "vigente"
    ]


def _registro_pgu(perfil: dict) -> dict | None:
    pgus = [p for p in perfil.get("pensiones_beneficios") or [] if p.get("tipo_beneficio") == "PGU"]
    if not pgus:
        return None
    orden = {"vigente": 0, "suspendido": 1, "terminado": 2}
    return sorted(pgus, key=lambda p: orden.get(p["estado"], 9))[0]


def monto_pgu(pension_base: int, edad_anios: int) -> tuple[int, int]:
    """Devuelve (monto_max, monto_estimado) según la fórmula de la ficha PGU."""
    p = config.PGU
    maximo = p["monto_max_75_mas"] if edad_anios >= p["edad_tramo_superior"] else p["monto_max_65_74"]
    if pension_base <= p["pension_inferior"]:
        return maximo, maximo
    if pension_base >= p["pension_superior"]:
        return maximo, 0
    factor = (p["pension_superior"] - pension_base) / (p["pension_superior"] - p["pension_inferior"])
    return maximo, round(maximo * factor)


def evaluar_pgu(perfil: dict, ref: date = config.FECHA_REFERENCIA) -> EvaluacionPGU:
    p = config.PGU
    rc, rsh, res = perfil["registro_civil"], perfil.get("rsh"), perfil.get("residencia")
    hitos = calcular_hitos(perfil, ref)
    reqs: list[Requisito] = []

    # 1. Edad
    if hitos.edad >= p["edad_acceso"]:
        reqs.append(Requisito("edad", "Tener 65 años o más", CUMPLE, f"Tiene {hitos.edad} años.", "Registro Civil"))
    elif ref >= hitos.fecha_apertura_pgu:
        reqs.append(Requisito("edad", "Tener 65 años o más", PENDIENTE,
                              f"Tiene {hitos.edad} años. Ya puede solicitar (desde los 64 años y 9 meses); "
                              f"el acceso es desde el {hitos.fecha_acceso_pgu:%d-%m-%Y}.", "Registro Civil"))
    else:
        reqs.append(Requisito("edad", "Tener 65 años o más", PENDIENTE,
                              f"Tiene {hitos.edad} años. Podrá solicitar desde el {hitos.fecha_apertura_pgu:%d-%m-%Y}.",
                              "Registro Civil"))

    # 2. Focalización (PFP / RSH)
    if rsh is None:
        reqs.append(Requisito("pfp", "No pertenecer al 10% de mayores ingresos", FALTA,
                              "No tiene Registro Social de Hogares; sin él no se puede evaluar el Puntaje de Focalización Previsional.",
                              "RSH"))
    elif not rsh.get("info_pfp_disponible") or rsh.get("pfp_percentil") is None:
        reqs.append(Requisito("pfp", "No pertenecer al 10% de mayores ingresos", FALTA,
                              "Tiene RSH, pero sin información suficiente para calcular el PFP.", "RSH"))
    elif rsh["pfp_percentil"] > p["pfp_percentil_max"]:
        reqs.append(Requisito("pfp", "No pertenecer al 10% de mayores ingresos", NO_CUMPLE,
                              f'Percentil PFP {rsh["pfp_percentil"]:.0f} (> {p["pfp_percentil_max"]}).', "RSH"))
    else:
        reqs.append(Requisito("pfp", "No pertenecer al 10% de mayores ingresos", CUMPLE,
                              f'Percentil PFP {rsh["pfp_percentil"]:.0f} (≤ {p["pfp_percentil_max"]}).', "RSH"))

    # 3. Residencia
    if res is None:
        reqs.append(Requisito("residencia", "Residencia: 20 años desde los 20 y 4 de los últimos 5", FALTA,
                              "No hay registro de residencia ni movimientos migratorios.", "Residencia / PDI"))
    else:
        det = (f'{res["anios_residencia_desde_20"]} años desde los 20 y {res["anios_residencia_ultimos_5"]} '
               f'de los últimos 5; {res["dias_fuera_pais_ultimos_5"]} días fuera del país.')
        if res["residencia_actual"] != "Chile":
            det += " Actualmente reside en el extranjero."
        estado = CUMPLE if res["resultado"] == "cumple" else NO_CUMPLE
        reqs.append(Requisito("residencia", "Residencia: 20 años desde los 20 y 4 de los últimos 5", estado,
                              det, "Residencia / PDI"))

    # 4. Pensión base
    vigentes = _pensiones_vigentes(perfil)
    prev = perfil.get("prevision")
    if vigentes:
        base, origen = sum(v["monto"] for v in vigentes), "pensiones vigentes registradas"
    elif prev and prev.get("pafe_estimada"):
        base, origen = int(prev["pafe_estimada"]), "pensión autofinanciada estimada (aún no se pensiona)"
    else:
        base, origen = 0, "sin pensiones registradas"
    maximo, estimado = monto_pgu(base, max(hitos.edad, p["edad_acceso"]))
    if base >= p["pension_superior"]:
        reqs.append(Requisito("pension_base", "Pensión base bajo el límite", NO_CUMPLE,
                              f"Pensión base ${base:,.0f} ({origen}) ≥ ${p['pension_superior']:,.0f}.".replace(",", "."),
                              "AFP / Compañías / IPS"))
    else:
        reqs.append(Requisito("pension_base", "Pensión base bajo el límite", CUMPLE,
                              f"Pensión base ${base:,.0f} ({origen}).".replace(",", "."), "AFP / Compañías / IPS"))

    # Resultado con precedencia documentada
    reg = _registro_pgu(perfil)
    estados = {r.id: r.estado for r in reqs}
    if rc["estado"] == "fallecido":
        res_, motivo = EXCLUIDO, "Persona fallecida según Registro Civil: se excluye de toda campaña."
    elif reg and reg["estado"] == "vigente":
        res_, motivo = YA_RECIBE, "Ya recibe la PGU."
    elif hitos.edad < p["edad_acceso"] and meses_entre(ref, hitos.fecha_acceso_pgu) > 12:
        res_, motivo = FUTURO, f"Cumple 65 el {hitos.fecha_acceso_pgu:%d-%m-%Y}."
    elif NO_CUMPLE in estados.values():
        fallas = [r.nombre for r in reqs if r.estado == NO_CUMPLE]
        res_, motivo = NO_ELEGIBLE, "No cumple: " + "; ".join(fallas) + "."
    elif FALTA in estados.values():
        faltan = [r.id for r in reqs if r.estado == FALTA]
        res_, motivo = ANTECEDENTE_FALTANTE, "Falta antecedente: " + ", ".join(faltan) + "."
        if reg and reg["estado"] == "suspendido":
            motivo = "PGU suspendida. " + motivo
    elif estados["edad"] == PENDIENTE:
        res_, motivo = PROXIMO, f"Cumple 65 el {hitos.fecha_acceso_pgu:%d-%m-%Y}; el resto de los antecedentes está en orden."
    else:
        res_, motivo = ELEGIBLE, "Según los antecedentes disponibles podría solicitar la PGU."
        if reg and reg["estado"] == "suspendido":
            motivo = "PGU suspendida, pero hoy los antecedentes están completos: puede pedir revisión."

    return EvaluacionPGU(res_, motivo, reqs, base, origen, maximo, estimado, reg)


def evaluar_jubilacion(perfil: dict, ref: date = config.FECHA_REFERENCIA) -> EvaluacionJubilacion:
    rc, prev = perfil["registro_civil"], perfil.get("prevision")
    hitos = calcular_hitos(perfil, ref)
    vigentes = _pensiones_vigentes(perfil)
    vejez = [v for v in vigentes if v["tipo_pension"] in ("vejez", "sistema_antiguo")]
    afp = prev["afp"] if prev else None
    pafe = int(prev["pafe_estimada"]) if prev and prev.get("pafe_estimada") else None
    kw = dict(afiliado_afp=prev is not None, afp=afp, pafe_estimada=pafe, pensiones_vigentes=vigentes)

    if rc["estado"] == "fallecido":
        return EvaluacionJubilacion("excluido", "Persona fallecida.", **kw)
    if vejez:
        return EvaluacionJubilacion("pensionado", "Ya tiene pensión de vejez vigente.", **kw)
    if prev is None:
        return EvaluacionJubilacion("sin_afp", "Nunca estuvo afiliada a una AFP: no hay pensión de vejez que tramitar; la PGU es la vía principal.", **kw)
    if ref >= hitos.fecha_edad_legal:
        return EvaluacionJubilacion("puede_pensionarse",
                                    f"Cumplió la edad legal ({hitos.edad_legal}) el {hitos.fecha_edad_legal:%d-%m-%Y} y no registra pensión de vejez. Pensionarse es voluntario.", **kw)
    if ref >= hitos.fecha_invitacion_jubilacion:
        return EvaluacionJubilacion("proximo",
                                    f"Cumple la edad legal ({hitos.edad_legal}) el {hitos.fecha_edad_legal:%d-%m-%Y}.", **kw)
    return EvaluacionJubilacion("futuro", f"Edad legal el {hitos.fecha_edad_legal:%d-%m-%Y}.", **kw)


def _segmento(pgu: EvaluacionPGU, jub: EvaluacionJubilacion) -> tuple[str, bool, str]:
    """Segmento de campaña: a quién invitar y por qué (paso 1 'Detectar' del PPT)."""
    if pgu.resultado == EXCLUIDO:
        return "Excluido (fallecido)", False, "No se contacta."
    if pgu.resultado == ANTECEDENTE_FALTANTE:
        return "PGU: falta antecedente", True, pgu.motivo
    if pgu.resultado == ELEGIBLE:
        return "PGU: podría solicitar", True, "65+ (o en ventana de solicitud) sin PGU vigente y con antecedentes en orden."
    if pgu.resultado == PROXIMO:
        return "PGU: próximo a 65", True, pgu.motivo
    if jub.resultado == "proximo":
        return "Jubilación: a un año de la edad legal", True, jub.motivo
    if jub.resultado == "puede_pensionarse":
        return "Jubilación: en edad legal sin pensión", True, jub.motivo
    if pgu.resultado == YA_RECIBE:
        return "Ya recibe PGU", False, "Solo seguimiento."
    if pgu.resultado == NO_ELEGIBLE:
        return "PGU: no cumple hoy", False, pgu.motivo
    return "Sin hito cercano", False, "Sin hito en los próximos 12 meses."


def diagnosticar(perfil: dict, ref: date = config.FECHA_REFERENCIA) -> Diagnostico:
    from .datos import nombre_completo
    pgu, jub = evaluar_pgu(perfil, ref), evaluar_jubilacion(perfil, ref)
    seg, invitar, razon = _segmento(pgu, jub)
    return Diagnostico(
        run=perfil["run"], nombre=nombre_completo(perfil),
        vivo=perfil["registro_civil"]["estado"] != "fallecido",
        hitos=calcular_hitos(perfil, ref), pgu=pgu, jubilacion=jub,
        segmento=seg, invitar=invitar, razon_invitacion=razon,
    )
