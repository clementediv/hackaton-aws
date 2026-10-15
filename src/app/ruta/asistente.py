"""Asistente: explica la ruta en lenguaje claro.

- Con BEDROCK_MODEL_ID configurado usa Amazon Bedrock (API Converse).
- Sin él, responde con plantillas a partir del mismo contexto estructurado.
En ambos casos solo usa hechos calculados por el motor de reglas: no decide ni inventa.
"""
import re
import unicodedata

from . import config
from . import reglas as R
from .fechas import fmt
from .rutas import Paso

def _peso(n: int | float | None) -> str:
    return "—" if n is None else f"${n:,.0f}".replace(",", ".")


def construir_contexto(d: R.Diagnostico, ruta: list[Paso], estados: dict, prox: Paso | None,
                       autorizado: bool) -> dict:
    h = d.hitos
    ctx = {
        "nombre": d.nombre.split()[0],
        "edad": h.edad,
        "hitos": {
            "edad_legal_vejez": h.edad_legal,
            "fecha_edad_legal": fmt(h.fecha_edad_legal),
            "fecha_apertura_solicitud_pgu": fmt(h.fecha_apertura_pgu),
            "fecha_acceso_pgu_65": fmt(h.fecha_acceso_pgu),
        },
        "autorizado": autorizado,
        "fuente_pgu": config.FUENTE_PGU,
    }
    if autorizado:
        ctx["run"] = d.run
        ctx["pgu"] = {
            "resultado_orientativo": d.pgu.resultado,
            "motivo": d.pgu.motivo,
            "requisitos": [{"requisito": r.nombre, "estado": r.estado, "detalle": r.detalle} for r in d.pgu.requisitos],
            "monto_orientativo": _peso(d.pgu.monto_estimado),
        }
        ctx["jubilacion"] = {"resultado": d.jubilacion.resultado, "motivo": d.jubilacion.motivo, "afp": d.jubilacion.afp}
        ctx["ruta"] = [{"paso": p.titulo, "estado": estados[p.id], "que_hacer": p.que_hacer,
                        "donde": p.donde, "documentos": p.documentos, "fuente": p.fuente} for p in ruta]
        ctx["proximo_paso"] = prox.titulo if prox else None
    return ctx


# --------------------------------------------------------------------------
def _bedrock(pregunta: str, ctx: dict, historial: list[dict]) -> str:
    from .chatbot import answer

    return answer(pregunta, ctx, historial)


def _norm(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def _plantilla(pregunta: str, ctx: dict) -> str:
    q = _norm(pregunta)
    greeting = re.sub(r"[^\w\s]", "", q).strip()
    if greeting in {"hola", "hola que tal", "hola como estas", "buenas", "buenos dias", "buenas tardes", "buenas noches"}:
        return (f"¡Hola, {ctx['nombre']}! ¿En qué te ayudo hoy? "
                "Puedes contarme tu duda o decirme qué parte del trámite quieres revisar.")
    if greeting in {"gracias", "muchas gracias", "ok gracias"}:
        return "¡De nada! Si te queda alguna duda sobre el trámite, cuéntame."
    h = ctx["hitos"]
    if not ctx["autorizado"]:
        return (f"Hola {ctx['nombre']}. Según tu fecha de nacimiento, tu edad legal de vejez es a los "
                f"{h['edad_legal_vejez']} ({h['fecha_edad_legal']}) y podrás pedir la PGU desde el "
                f"{h['fecha_apertura_solicitud_pgu']}. Para revisar qué te corresponde y qué te falta, "
                "necesito tu autorización para consultar tus antecedentes.")
    pgu, ruta = ctx["pgu"], ctx["ruta"]
    prox = ctx.get("proximo_paso")
    cierre = f" Tu próximo paso: «{prox}»." if prox else ""
    if "que es" in q and "pgu" in q or "pgu" == q.strip():
        return ("La PGU (Pensión Garantizada Universal) es un aporte mensual del Estado para personas de 65 años o más "
                "que no están en el 10% de mayores ingresos, cumplen residencia y tienen una pensión base bajo el límite. "
                f"Se suma a tu pensión de AFP. Fuente: {ctx['fuente_pgu']}.{cierre}")
    if "afp" in q and "que es" in q:
        return "La AFP administra tus ahorros previsionales; con ellos se calcula tu pensión de vejez." + cierre
    if "scomp" in q:
        return ("SCOMP es el sistema donde comparas ofertas de pensión (retiro programado o renta vitalicia) "
                "antes de elegir. Tu AFP te entrega el certificado." + cierre)
    if "rsh" in q or "registro social" in q:
        return ("El Registro Social de Hogares reúne información de tu hogar y permite calcular el puntaje usado "
                "para la PGU. Se gestiona en registrosocial.gob.cl o en tu municipalidad." + cierre)
    if any(k in q for k in ("cuanto", "monto", "plata", "dinero")):
        res = pgu["resultado_orientativo"]
        if res == R.NO_ELEGIBLE:
            return ("Con los antecedentes disponibles, hoy no se cumplen todos los requisitos de la PGU, "
                    "así que no podemos estimarte un monto. " + pgu["motivo"] + cierre)
        if res == R.ANTECEDENTE_FALTANTE:
            return ("Para estimar tu PGU primero necesitamos el antecedente que falta. "
                    f"Si todo queda en orden, el monto orientativo sería {pgu['monto_orientativo']} al mes." + cierre)
        if res == R.FUTURO:
            return (f"La PGU se paga desde los 65 ({h['fecha_acceso_pgu_65']}). Hoy el máximo es "
                    f"{_peso(config.PGU['monto_max_65_74'])} al mes; el monto depende de tu pensión en ese momento." + cierre)
        return (f"Con los antecedentes disponibles, el monto orientativo de tu PGU sería {pgu['monto_orientativo']} al mes. "
                "El monto definitivo lo calcula el IPS." + cierre)
    if any(k in q for k in ("documento", "papel", "necesito", "llevar")):
        docs = sorted({doc for p in ruta if p["estado"] != "completado" for doc in p["documentos"]})
        return ("Para los pasos pendientes necesitarás: " + (", ".join(docs) if docs else "nada adicional por ahora") + "." + cierre)
    if any(k in q for k in ("cuando", "fecha", "plazo")):
        return (f"Edad legal de vejez: {h['fecha_edad_legal']}. Solicitud PGU desde: {h['fecha_apertura_solicitud_pgu']}. "
                f"Acceso a la PGU: {h['fecha_acceso_pgu_65']}." + cierre)
    if any(k in q for k in ("donde", "canal", "oficina", "sucursal")):
        p = next((p for p in ruta if p["paso"] == prox), None)
        return (f"Para «{p['paso']}»: {p['donde']}." if p else "Puedes consultar en ChileAtiende (101).") 
    if any(k in q for k in ("cumplo", "puedo", "requisito", "corresponde", "falta")):
        lineas = [f"• {r['requisito']}: {r['estado'].replace('_', ' ')}. {r['detalle']}" for r in pgu["requisitos"]]
        return ("Esto es lo que vemos en tus antecedentes (orientación, no resolución):\n" + "\n".join(lineas) + "\n" + pgu["motivo"] + cierre)
    return ("¿Qué te gustaría revisar? Puedo ayudarte con los requisitos, el monto orientativo, "
            "los documentos o los pasos de tu trámite. Cuéntame un poco más para orientarte.")


def explicar_resumen(ctx: dict) -> str:
    """Explicación inicial de la ruta (sin LLM)."""
    if not ctx["autorizado"]:
        return _plantilla("", ctx)
    pgu, jub = ctx["pgu"], ctx["jubilacion"]
    textos = {
        R.ELEGIBLE: f"Según tus antecedentes, podrías solicitar la PGU (monto orientativo {pgu['monto_orientativo']}).",
        R.PROXIMO: f"Te acercas a los 65: tus antecedentes están en orden para preparar la solicitud de PGU (monto orientativo {pgu['monto_orientativo']}).",
        R.ANTECEDENTE_FALTANTE: "Para orientarte sobre la PGU nos falta un antecedente. Te mostramos cómo conseguirlo y después seguimos.",
        R.NO_ELEGIBLE: "Con los antecedentes disponibles, hoy no se cumplen todos los requisitos de la PGU. Te explicamos por qué y qué podría cambiar.",
        R.YA_RECIBE: "Ya recibes la PGU. Te acompañamos con el seguimiento de tus pagos.",
        R.FUTURO: "Aún falta para la PGU.",
    }
    partes = [f"Hola {ctx['nombre']}.", textos.get(pgu["resultado_orientativo"], "")]
    if jub["resultado"] == "proximo":
        partes.append(f"Además, el {ctx['hitos']['fecha_edad_legal']} cumples la edad legal de vejez: es buen momento para revisar tu pensión en {jub['afp']}.")
    elif jub["resultado"] == "puede_pensionarse":
        partes.append(f"Ya tienes la edad legal de vejez y no registras pensión: puedes solicitarla en {jub['afp']} si lo decides.")
    if ctx.get("proximo_paso"):
        partes.append(f"Tu próximo paso: «{ctx['proximo_paso']}».")
    return " ".join(p for p in partes if p)


def responder(pregunta: str, ctx: dict, historial: list[dict]) -> tuple[str, str]:
    """Devuelve (respuesta, motor) donde motor es 'bedrock' o 'plantillas'."""
    # A revoked consent must not forward previously authorized chat to the LLM.
    if not ctx["autorizado"]:
        return _plantilla(pregunta, ctx), "plantillas"
    if config.BEDROCK_MODEL_ID:
        try:
            return _bedrock(pregunta, ctx, historial), "bedrock"
        except Exception as e:  # sin credenciales / modelo no habilitado: degradar sin romper la demo
            return _plantilla(pregunta, ctx) + f"\n\n_(Bedrock no disponible: {type(e).__name__}; respuesta por plantillas)_", "plantillas"
    return _plantilla(pregunta, ctx), "plantillas"


def mensaje_invitacion(d: R.Diagnostico) -> str:
    """Paso 2 'Invitar': explica por qué se contacta, usando solo datos de Registro Civil."""
    h, nombre = d.hitos, d.nombre.split()[0]
    if d.segmento.startswith("Jubilación"):
        motivo = f"el {fmt(h.fecha_edad_legal)} cumples {h.edad_legal} años, la edad legal para pensionarte por vejez"
    else:
        motivo = (f"desde el {fmt(h.fecha_apertura_pgu)} puedes solicitar la Pensión Garantizada Universal (PGU)"
                  if h.edad < 65 else "tienes 65 años o más y podrías revisar la Pensión Garantizada Universal (PGU)")
    return (f"Hola {nombre}, te escribe ChileAtiende. Te contactamos porque {motivo}. "
            "Podemos ayudarte a revisar qué te corresponde, qué te falta y cuáles son tus próximos pasos. "
            "Es voluntario: puedes aceptar o no este acompañamiento.")
