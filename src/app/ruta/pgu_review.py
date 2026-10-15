"""Personal PGU review from consented profiles and saved route progress."""

import re
import unicodedata

from . import config, reglas
from .rutas import estado_pasos, generar_ruta, proximo_paso


def is_personal_pgu_question(question: str, *, pgu_context=False) -> bool:
    text = "".join(
        c for c in unicodedata.normalize("NFD", question.lower())
        if unicodedata.category(c) != "Mn"
    )
    return (bool(re.search(r"\bpgu\b", text)) or pgu_context) and any(term in text for term in (
        "soy apt", "soy elegible", "puedo", "podria", "cumplo", "me corresponde",
        "tengo derecho", "mi caso", "mi pgu", "me falta", "me faltan", "mis pasos",
        "en que paso", "en que etapa", "revisar si", "revisar mi",
        "que falta", "que datos", "que informacion", "no tengo informacion",
    ))


def review_pgu(run, case, load_profiles):
    """Never load a profile without both a session identity and consent."""
    if not run:
        return (
            "Sí, podemos revisar si podrías optar a la PGU y en qué paso estás. "
            "Todavía no tengo tus antecedentes vinculados a esta conversación. "
            "Primero ingresa a Mi Gobierno y autoriza su consulta. "
            "Si falta información, te indicaré cuál debes completar allí antes de evaluar. "
            "Esta demo usa el RUN de prueba mostrado en el acceso y la clave demo2026; "
            "no ingreses datos reales aquí."
        )
    if not case or not case.get("autorizacion"):
        return (
            "Para revisar tu PGU necesito tu autorización. En Mi Gobierno, acepta el "
            "acompañamiento y autoriza consultar tus antecedentes. Después podré revisar "
            "los requisitos, tus pasos completados y qué información falta. "
            "Sin esa autorización aún no puedo confirmar si cumples los requisitos."
        )
    profile = load_profiles().get(run)
    if profile is None:
        return (
            "No encontré un perfil de prueba asociado a tu sesión. Ingresa nuevamente "
            "a Mi Gobierno con uno de los perfiles de demostración para vincular tus antecedentes. "
            "Todavía no puedo evaluar tu PGU."
        )
    diagnosis = reglas.diagnosticar(profile)
    labels = {
        reglas.ELEGIBLE: "Podrías solicitar la PGU según los requisitos evaluados.",
        reglas.ANTECEDENTE_FALTANTE: "Faltan antecedentes para completar tu evaluación de PGU.",
        reglas.NO_ELEGIBLE: "Actualmente no cumples alguno de los requisitos evaluados de PGU.",
        reglas.PROXIMO: "Todavía no cumples la edad para recibir la PGU; puedes preparar tu ruta.",
        reglas.FUTURO: "Tu acceso a la PGU corresponde a una etapa futura según tu edad.",
        reglas.YA_RECIBE: "Tu perfil registra una PGU vigente.",
        reglas.EXCLUIDO: "Este perfil no permite continuar una solicitud de PGU.",
    }
    text = [labels[diagnosis.pgu.resultado], diagnosis.pgu.motivo]
    missing = [r for r in diagnosis.pgu.requisitos if r.estado == reglas.FALTA]
    if missing:
        text.append("**Antecedentes que faltan:**\n" + "\n".join(
            f"- {r.nombre}: {r.detalle}" for r in missing
        ))
        text.append(
            "Completa o adjunta esos antecedentes en Mi Gobierno, en los requisitos de PGU. "
            "Adjuntar un documento no confirma por sí solo el requisito: debe verificarse."
        )
    route = [p for p in generar_ruta(diagnosis) if p.tramite in {"PGU", "Antecedentes"}]
    states = estado_pasos(route, case.get("completados", set()))
    if route:
        completed = sum(states[p.id] == "completado" for p in route)
        text.append(f"**Tu avance guardado:** {completed} de {len(route)} pasos completados.")
        next_step = proximo_paso(route, states)
        if next_step:
            text.append(f"**Próximo paso:** {next_step.titulo}. {next_step.que_hacer}")
        else:
            text.append(
                "No hay pasos pendientes en esta ruta. Revisa el seguimiento en Mi Gobierno."
            )
    text.append(
        f"Evaluación preliminar sobre datos sintéticos al {config.FECHA_REFERENCIA:%d/%m/%Y}; "
        f"el IPS valida y resuelve. [Fuente: ChileAtiende]({config.FUENTE_PGU})."
    )
    return "\n\n".join(text)
