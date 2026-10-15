"""Conversational style without changing deterministic benefit rules."""

import re
import unicodedata

CHAT_STYLE = """Estilo de conversación:
Responde al sentido del último mensaje, teniendo en cuenta la conversación disponible.
Habla con calidez, en español natural, sin fingir ser una persona o un funcionario.
No repitas la misma bienvenida, menú de temas, petición de permiso ni frase de cierre.
Si hay frustración o una grosería, responde con calma y reconoce lo que sí comprendes;
no sermonees, no devuelvas el insulto ni conviertas todo en una explicación sobre PGU.
Distingue una queja que contiene una pregunta real de un insulto sin consulta: contesta
la pregunta real si la hay. Si el mensaje es ambiguo o ininteligible, no inventes una
interpretación: haz una sola pregunta breve para aclararlo. Si se repite, pide un
ejemplo concreto o sugiere reformular, en lugar de repetir textualmente tu respuesta.
Las intervenciones sociales suelen necesitar una o dos frases, no un diagnóstico ni
una lista de requisitos. No uses frases corporativas ni 'como inteligencia artificial'.
Mantén intactas las reglas de consentimiento, fuentes y decisiones institucionales.
"""


class ConversationalClient:
    def __init__(self, client):
        self.client = client

    def converse(self, messages, **options):
        options["system"] = [*options.get("system", []), {"text": CHAT_STYLE}]
        return self.client.converse(messages, **options)


def clarification(history):
    replies = sum(m.get("rol") == "assistant" for m in history)
    return (
        "No alcancé a entender ese mensaje. ¿Me lo cuentas de otra forma?",
        "Todavía no me queda clara tu duda. ¿Puedes darme un ejemplo concreto?",
        "Probemos de otra manera: ¿qué necesitas resolver hoy?",
    )[replies % 3]


def social_fallback(question, history):
    q = "".join(
        c for c in unicodedata.normalize("NFD", question.lower()) if unicodedata.category(c) != "Mn"
    )
    # Never hide a real question because it includes a swear word.
    substantive = re.search(
        r"\b(pgu|pension|beneficio|documento|requisito|cuando|cuanto|como)\b", q
    )
    if substantive:
        return None
    if any(term in q for term in ("frustr", "estres", "no entiendo", "me da rabia", "harto")):
        return "Podemos ir con calma, de a una cosa. ¿Qué parte te está complicando más?"
    if (
        re.search(r"\b(weon|huevon|weona|mierda|puta|idiota|imbecil|inutil)\b", q)
        or "no sirves" in q
    ):
        replies = sum(m.get("rol") == "assistant" for m in history)
        return (
            "Si algo de mi respuesta no te sirvió, dime qué estuvo mal y lo revisamos.",
            "Podemos retomar. ¿Qué esperabas que te ayudara a resolver?",
        )[replies % 2]
    letters = re.sub(r"[^a-z]", "", q)
    noise = re.fullmatch(r"(?:asdf[a-z]*|qwerty[a-z]*|(?:bla|blah){2,})", letters)
    if not letters or noise or (len(letters) >= 5 and not re.search(r"[aeiou]", letters)):
        return clarification(history)
    return None
