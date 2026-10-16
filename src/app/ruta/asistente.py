"""Asistente: explica la ruta en lenguaje claro.

- Con BEDROCK_MODEL_ID configurado usa Amazon Bedrock (API Converse).
- Sin él, responde con plantillas a partir del mismo contexto estructurado.
En ambos casos solo usa hechos calculados por el motor de reglas: no decide ni inventa.
"""

import re
import time
import unicodedata
from itertools import chain

from . import config
from . import reglas as R
from .conversation import boundary_reply, clarification, friendly_sources, social_fallback
from .fechas import fmt
from .knowledge import grounded_fallback
from .rutas import Paso


def responder_publico(pregunta: str, historial: list[dict], *, stream=False):
    """General orientation without reading profiles or authorized personal routes."""
    if boundary := boundary_reply(pregunta):
        return (_template_stream(boundary) if stream else boundary), "plantillas"
    source = f"[ChileAtiende]({config.FUENTES['chileatiende']})"
    topics = {
        "pgu": (
            "La PGU es la Pensión Garantizada Universal. Puedes revisar sus requisitos y cómo solicitarla en la ficha oficial. Para revisar tu situación, entra a Mi Gobierno y autoriza la consulta de tus antecedentes.",
            f"[Ficha PGU]({config.FUENTE_PGU})",
        ),
        "document": (
            "Los documentos dependen del beneficio. En Mi Gobierno, abre tu beneficio y revisa los antecedentes indicados en cada paso. ¿Qué beneficio quieres consultar?",
            source,
        ),
        "beca": (
            "Puedes consultar becas y beneficios estudiantiles en el portal oficial. En Mi Gobierno encontrarás qué antecedentes falta reunir; esta demo todavía no evalúa esos beneficios.",
            "[Beneficios Estudiantiles](https://portal.beneficiosestudiantiles.cl/)",
        ),
        "gratuidad": (
            "Revisa la información de gratuidad en el portal oficial de Beneficios Estudiantiles. Esta demo todavía no determina si te corresponde.",
            "[Beneficios Estudiantiles](https://portal.beneficiosestudiantiles.cl/)",
        ),
        "empez": (
            "Puedes comenzar en Mi Gobierno: ingresa, autoriza consultar tus antecedentes y revisa tu próximo paso. ¿Buscas orientación sobre pensiones o estudios?",
            source,
        ),
    }
    introduction = (
        "Soy el asistente de IA de ChileAtiende. "
        "Te ayudo con trámites, beneficios y los documentos que necesitas."
    )
    question = _norm(pregunta)
    identity_question = any(
        phrase in question
        for phrase in (
            "quien eres",
            "que eres",
            "que haces",
            "que puedes hacer",
            "que puede hacer",
            "para que sirves",
            "para que sirve",
            "como me puedes ayudar",
            "como puedes ayudar",
            "en que me puedes ayudar",
            "eres una ia",
            "eres un asistente",
            "eres una inteligencia",
            "eres inteligencia artificial",
            "presentate",
            "tu funcion",
            "tus funciones",
            "ayudas con tramites",
            "ayudar con tramites",
        )
    )
    if identity_question:
        fallback = introduction
        return (_template_stream(fallback) if stream else fallback), "plantillas"
    elif question.strip(" ¡!¿?.") in {"hola", "buenas", "buenos dias"}:
        fallback = "¡Hola! Te ayudo con trámites y beneficios. ¿Qué necesitas?"
        return (_template_stream(fallback) if stream else fallback), "plantillas"
    elif "gracias" in question:
        fallback = "¡De nada! Puedes seguir preguntándome aquí cuando lo necesites."
    else:
        topic = next((key for key in topics if key in question), None)
        if topic is None and len(question.split()) <= 8:
            previous = " ".join(_norm(m["texto"]) for m in historial[-4:] if m["rol"] == "user")
            topic = next((key for key in topics if key in previous), None)
        text, citation = (
            topics[topic]
            if topic
            else (
                clarification(historial),
                source,
            )
        )
        fallback = f"{text}\n\nFuente: {citation}."
    if (
        not identity_question
        and question.strip(" ¡!¿?.") not in {"hola", "buenas", "buenos dias"}
        and (conversational := social_fallback(pregunta, historial))
    ):
        fallback = conversational + f"\n\nFuente: {source}."
    elif "gracias" not in question and (grounded := grounded_fallback(pregunta, historial)):
        fallback = grounded
    if config.BEDROCK_MODEL_ID:
        try:
            from .chatbot import answer_general

            options = {"public_history": historial, "public_guidance": fallback}
            if stream:
                chunks = answer_general(pregunta, stream=True, **options)
                first = next(chunks)
                return chain([first], chunks), "bedrock"
            return answer_general(pregunta, **options), "bedrock"
        except Exception:
            pass
    fallback = friendly_sources(fallback)
    return (_template_stream(fallback) if stream else fallback), "plantillas"


WORD_DELAY_SECONDS = 0.025


def _template_stream(text):
    """Progressive display for the offline template mode."""
    for word in re.findall(r"\S+\s*", text):
        yield word
        time.sleep(WORD_DELAY_SECONDS)


def _peso(n: int | float | None) -> str:
    return "—" if n is None else f"${n:,.0f}".replace(",", ".")


def construir_contexto(
    d: R.Diagnostico, ruta: list[Paso], estados: dict, prox: Paso | None, autorizado: bool
) -> dict:
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
            "requisitos": [
                {"requisito": r.nombre, "estado": r.estado, "detalle": r.detalle}
                for r in d.pgu.requisitos
            ],
            "monto_orientativo": _peso(d.pgu.monto_estimado),
        }
        ctx["jubilacion"] = {
            "resultado": d.jubilacion.resultado,
            "motivo": d.jubilacion.motivo,
            "afp": d.jubilacion.afp,
        }
        ctx["ruta"] = [
            {
                "paso": p.titulo,
                "estado": estados[p.id],
                "que_hacer": p.que_hacer,
                "donde": p.donde,
                "documentos": p.documentos,
                "fuente": p.fuente,
            }
            for p in ruta
        ]
        ctx["proximo_paso"] = prox.titulo if prox else None
    return ctx


# --------------------------------------------------------------------------
def _bedrock(pregunta: str, ctx: dict, historial: list[dict]) -> str:
    from .chatbot import answer

    return answer(pregunta, ctx, historial)


def _norm(t: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn"
    )


def _consulta_personal(question: str) -> bool:
    """Identify a request about the person's case, never determine eligibility."""
    q = _norm(question)
    return any(
        term in q
        for term in (
            "puedo",
            "podria",
            "podre",
            "cumplo",
            "mi caso",
            "corresponde",
            "mis datos",
            "cuanto",
            "monto",
            "tengo derecho",
            "tendre derecho",
            "soy elegible",
            "califico",
            "puedo acceder",
            "puedo recibir",
            "puedo tener",
            "optar a",
            "para mi",
        )
    )


def _plantilla(pregunta: str, ctx: dict) -> str:
    q = re.sub(r"\b(mierda|puta|puto|weon|huevon)\b", "", _norm(pregunta))
    q = " ".join(q.split())
    greeting = re.sub(r"[^\w\s]", "", q).strip()
    if greeting in {
        "hola",
        "hola que tal",
        "hola como estas",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
    }:
        return (
            f"¡Hola, {ctx['nombre']}! ¿En qué te ayudo hoy? "
            "Puedes contarme tu duda o decirme qué parte del trámite quieres revisar."
        )
    if greeting in {"gracias", "muchas gracias", "ok gracias"}:
        return "¡De nada! Si te queda alguna duda sobre el trámite, cuéntame."
    # General questions do not require reading a personal profile.
    source = f" Fuente de orientación del MVP: {ctx.get('fuente_pgu', config.FUENTE_PGU)}."
    general = any(
        term in q
        for term in (
            "que es",
            "que significa",
            "explica",
            "explicame",
            "para que sirve",
            "como funciona",
        )
    )
    if q.strip(" ¿?¡!.") == "pgu" or (general and ("pgu" in q or "pension garantizada" in q)):
        return (
            "La PGU significa Pensión Garantizada Universal. Es un aporte mensual del Estado "
            "para personas de 65 años o más que cumplen los requisitos establecidos. "
            "Es un beneficio distinto de la pensión de una AFP; "
            "el IPS revisa los antecedentes y decide. "
            "Puedo explicarte los requisitos generales sin consultar tus datos; "
            "para revisar tu situación personal necesitas autorizar los antecedentes." + source
        )
    if general and "afp" in q:
        return (
            "Una AFP administra los ahorros previsionales destinados a financiar tu pensión. "
            "La PGU es un beneficio distinto, cuya evaluación corresponde al IPS. "
            "¿Quieres entender la diferencia o revisar los pasos para pensionarte? "
            f"Fuente: {config.FUENTES['spensiones']}."
        )
    if "scomp" in q:
        return (
            "SCOMP es el Sistema de Consultas y Ofertas de Montos de Pensión. "
            "Permite comparar ofertas antes de elegir una modalidad de pensión. "
            f"Fuente: {config.FUENTES['spensiones']}."
        )
    if general and ("rsh" in q or "registro social" in q):
        return (
            "El Registro Social de Hogares reúne información de tu hogar que se utiliza "
            "para acceder a beneficios y programas del Estado. "
            f"Puedes revisarlo en {config.FUENTES['rsh']}. "
            "Para explicar el registro no necesito consultar tus antecedentes personales."
        )
    h = ctx["hitos"]
    if not ctx["autorizado"] and q.strip():
        if _consulta_personal(pregunta):
            return (
                "Para revisar si te corresponde la PGU o estimar tu monto necesito que "
                "autorices la consulta de antecedentes aquí, en Mi Gobierno: marca la casilla "
                "«Acepto el acompañamiento y autorizo consultar mis antecedentes» y pulsa "
                "«Activar Mi Gobierno». "
                "Aún no puedo confirmar si cumples los requisitos; la decisión final es del IPS. "
                "Mientras tanto puedo explicarte qué es la PGU y cómo funciona." + source
            )
        return (
            "¿Qué parte te gustaría entender? Puedo explicarte qué es la PGU, "
            "qué es una AFP o cómo continuar con la autorización. "
            "Cuéntame tu duda; para información general no necesitas autorizar tus datos." + source
        )
    if not ctx["autorizado"]:
        return (
            f"Hola {ctx['nombre']}. Según tu fecha de nacimiento, tu edad legal de vejez es a los "
            f"{h['edad_legal_vejez']} ({h['fecha_edad_legal']}) y podrás pedir la PGU desde el "
            f"{h['fecha_apertura_solicitud_pgu']}. Para revisar qué te corresponde y qué te falta, "
            "necesito tu autorización para consultar tus antecedentes."
        )
    pgu, ruta = ctx["pgu"], ctx["ruta"]
    prox = ctx.get("proximo_paso")
    cierre = f" Tu próximo paso: «{prox}»." if prox else ""
    if any(k in q for k in ("cuanto", "monto", "plata", "dinero")):
        res = pgu["resultado_orientativo"]
        if res == R.NO_ELEGIBLE:
            return (
                "Con los antecedentes disponibles, hoy no se cumplen todos los requisitos de la PGU, "
                "así que no podemos estimarte un monto. " + pgu["motivo"] + cierre
            )
        if res == R.ANTECEDENTE_FALTANTE:
            return (
                "Para estimar tu PGU primero necesitamos el antecedente que falta. "
                f"Si todo queda en orden, el monto orientativo sería {pgu['monto_orientativo']} al mes."
                + cierre
            )
        if res == R.FUTURO:
            return (
                f"La PGU se paga desde los 65 ({h['fecha_acceso_pgu_65']}). Hoy el máximo es "
                f"{_peso(config.PGU['monto_max_65_74'])} al mes; el monto depende de tu pensión en ese momento."
                + cierre
            )
        return (
            f"Con los antecedentes disponibles, el monto orientativo de tu PGU sería {pgu['monto_orientativo']} al mes. "
            "El monto definitivo lo calcula el IPS." + cierre
        )
    if any(k in q for k in ("documento", "papel", "necesito", "llevar")):
        docs = sorted({doc for p in ruta if p["estado"] != "completado" for doc in p["documentos"]})
        return (
            "Para los pasos pendientes necesitarás: "
            + (", ".join(docs) if docs else "nada adicional por ahora")
            + "."
            + cierre
        )
    if any(k in q for k in ("cuando", "fecha", "plazo")):
        return (
            f"Edad legal de vejez: {h['fecha_edad_legal']}. Solicitud PGU desde: {h['fecha_apertura_solicitud_pgu']}. "
            f"Acceso a la PGU: {h['fecha_acceso_pgu_65']}." + cierre
        )
    if any(k in q for k in ("donde", "canal", "oficina", "sucursal")):
        p = next((p for p in ruta if p["paso"] == prox), None)
        return (
            f"Para «{p['paso']}»: {p['donde']}." if p else "Puedes consultar en ChileAtiende (101)."
        )
    if any(k in q for k in ("cumplo", "puedo", "requisito", "corresponde", "falta")):
        lineas = [
            f"• {r['requisito']}: {r['estado'].replace('_', ' ')}. {r['detalle']}"
            for r in pgu["requisitos"]
        ]
        return (
            "Esto es lo que vemos en tus antecedentes (orientación, no resolución):\n"
            + "\n".join(lineas)
            + "\n"
            + pgu["motivo"]
            + cierre
        )
    return (
        "¿Qué te gustaría revisar? Puedo ayudarte con los requisitos, el monto orientativo, "
        "los documentos o los pasos de tu trámite. Cuéntame un poco más para orientarte."
    )


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
        partes.append(
            f"Además, el {ctx['hitos']['fecha_edad_legal']} cumples la edad legal de vejez: es buen momento para revisar tu pensión en {jub['afp']}."
        )
    elif jub["resultado"] == "puede_pensionarse":
        partes.append(
            f"Ya tienes la edad legal de vejez y no registras pensión: puedes solicitarla en {jub['afp']} si lo decides."
        )
    if ctx.get("proximo_paso"):
        partes.append(f"Tu próximo paso: «{ctx['proximo_paso']}».")
    return " ".join(p for p in partes if p)


def _respaldo(pregunta, ctx, historial):
    reply = social_fallback(pregunta, historial)
    if reply is None:
        reply = _plantilla(pregunta, ctx)
        if reply.startswith(("¿Qué parte te gustaría entender?", "¿Qué te gustaría revisar?")):
            reply = (
                grounded_fallback(pregunta, historial) if not _consulta_personal(pregunta) else None
            ) or clarification(historial)
    if "https://" not in reply:
        reply += f"\n\nFuente de orientación: {config.FUENTES['chileatiende']}"
    return friendly_sources(reply)


def responder(
    pregunta: str, ctx: dict, historial: list[dict], *, public_history: list[dict] | None = None
) -> tuple[str, str]:
    """Devuelve (respuesta, motor) donde motor es 'bedrock' o 'plantillas'."""
    if boundary := boundary_reply(pregunta):
        return boundary, "plantillas"
    # A revoked consent must not forward previously authorized chat to the LLM.
    if not ctx["autorizado"]:
        # A personal question must get the consent step, never an invented evaluation.
        if _consulta_personal(pregunta):
            return _respaldo(pregunta, ctx, historial), "plantillas"
        q = re.sub(r"[^\w\s]", "", _norm(pregunta)).strip()
        social = q in {
            "hola",
            "hola que tal",
            "hola como estas",
            "buenas",
            "buenos dias",
            "buenas tardes",
            "buenas noches",
            "gracias",
            "muchas gracias",
            "ok gracias",
        }
        # General conversation is not limited to a fixed list of keywords.
        if config.BEDROCK_MODEL_ID and q and not social:
            try:
                from .chatbot import answer_general

                if public_history is not None:
                    return answer_general(pregunta, public_history=public_history), "bedrock"
                return answer_general(pregunta), "bedrock"
            except Exception:
                return (
                    _respaldo(pregunta, ctx, historial)
                    + "\n\n_(Bedrock no disponible; información general de respaldo.)_",
                    "plantillas",
                )
        return _respaldo(pregunta, ctx, historial), "plantillas"
    if config.BEDROCK_MODEL_ID:
        try:
            return _bedrock(pregunta, ctx, historial), "bedrock"
        except (
            Exception
        ) as e:  # sin credenciales / modelo no habilitado: degradar sin romper la demo
            return (
                _respaldo(pregunta, ctx, historial)
                + f"\n\n_(Bedrock no disponible: {type(e).__name__}; respuesta por plantillas)_",
                "plantillas",
            )
    return _respaldo(pregunta, ctx, historial), "plantillas"


def mensaje_invitacion(d: R.Diagnostico) -> str:
    """Paso 2 'Invitar': explica por qué se contacta, usando solo datos de Registro Civil."""
    h, nombre = d.hitos, d.nombre.split()[0]
    if d.segmento.startswith("Jubilación"):
        motivo = f"el {fmt(h.fecha_edad_legal)} cumples {h.edad_legal} años, la edad legal para pensionarte por vejez"
    else:
        motivo = (
            f"desde el {fmt(h.fecha_apertura_pgu)} puedes solicitar la Pensión Garantizada Universal (PGU)"
            if h.edad < 65
            else "tienes 65 años o más y podrías revisar la Pensión Garantizada Universal (PGU)"
        )
    return (
        f"Hola {nombre}, te escribe ChileAtiende. Te contactamos porque {motivo}. "
        "Podemos ayudarte a revisar qué te corresponde, qué te falta y cuáles son tus próximos pasos. "
        "Es voluntario: puedes aceptar o no este acompañamiento."
    )
