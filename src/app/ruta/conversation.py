"""Conversational style without changing deterministic benefit rules."""

import re
import unicodedata

BOUNDARY_REPLY = (
    "Estoy aquí para orientarte sobre beneficios y trámites, como la Pensión Garantizada "
    "Universal (PGU), sus requisitos, "
    "documentos y próximos pasos. La revisión de antecedentes personales se realiza "
    "únicamente con tu autorización en Mi Gobierno. Por favor, cuéntame qué beneficio o trámite deseas "
    "consultar para poder ayudarte."
    "\n\nSi quieres saber más, puedes revisar [ChileAtiende](https://www.chileatiende.gob.cl/)."
)


def friendly_sources(text):
    """Keep citations and verification notes, phrased as an invitation to read more."""
    pattern = (
        r"(?im)(?P<start>^|(?<=[.!?])\s+)(?:\*\*)?"
        r"Fuentes?(?: de orientación(?: del MVP)?)?"
        r"(?P<note>\s*\([^\n)]*\))?\s*:\s*(?:\*\*)?(?P<reference>[^\n]+)"
    )

    def replace(match):
        reference = match["reference"].strip()
        result = match["start"] + "Si quieres saber más, puedes revisar " + reference
        if not result.endswith("."):
            result += "."
        if note := match["note"]:
            result += " Esta referencia se indica como " + note.strip(" ()") + "."
        return result

    return re.sub(pattern, replace, text)


def boundary_reply(question):
    """A stable purpose statement for abuse, keyboard noise and clear off-topic requests."""
    q = "".join(
        c for c in unicodedata.normalize("NFD", question.lower()) if unicodedata.category(c) != "Mn"
    )
    if re.search(
        r"\b(pgu|pension\w*|beneficio\w*|document\w*|requisito\w*|tramite\w*|"
        r"afp|rsh|scomp|jubilacion|beca\w*|gratuidad|autoriza\w*)\b",
        q,
    ):
        return None
    abuse = re.search(r"\b(weon|huevon|weona|mierda|puta|idiota|imbecil|inutil)\b", q)
    off_topic = re.search(r"\b(futbol|mundial|messi|horoscopo|receta|chiste)\b", q)
    letters = re.sub(r"[^a-z]", "", q)
    noise = (
        not letters
        or re.fullmatch(r"(?:asdf[a-z]*|qwerty[a-z]*|(?:bla|blah){2,})", letters)
        or len(letters) >= 5
        and not re.search(r"[aeiou]", letters)
    )
    if abuse or "no sirves" in q or off_topic or noise:
        return BOUNDARY_REPLY
    return None


CHAT_STYLE = (
    """Estilo de conversación:
Responde al sentido del último mensaje, teniendo en cuenta la conversación disponible.
Habla con calidez, en español natural, sin fingir ser una persona o un funcionario.
No repitas la misma bienvenida, menú de temas, petición de permiso ni frase de cierre.
Si una consulta legítima expresa frustración o incluye una grosería, responde con calma;
no sermonees, no devuelvas el insulto ni conviertas todo en una explicación sobre PGU.
Distingue una queja que contiene una pregunta real de un insulto sin consulta: contesta
la pregunta real si la hay. Si una consulta dentro del propósito es ambigua, no inventes
una interpretación: haz una sola pregunta breve para aclararla. Si se repite, pide un
ejemplo concreto o sugiere reformular, en lugar de repetir textualmente tu respuesta.
Las intervenciones sociales suelen necesitar una o dos frases, no un diagnóstico ni
una lista de requisitos. No uses frases corporativas ni 'como inteligencia artificial'.
Presenta las referencias de forma natural: «Si quieres saber más, puedes revisar
[título](URL)». Evita encabezados como «Fuente de orientación» o listas de fuentes
sin explicación. Conserva los enlaces y las advertencias de información no verificada.
Mantén intactas las reglas de consentimiento, fuentes y decisiones institucionales.
Para insultos sin consulta, texto ininteligible o solicitudes claramente fuera del
propósito del chat, usa exactamente la siguiente respuesta estándar, sin variaciones:
"""
    + BOUNDARY_REPLY
)


class ConversationalClient:
    def __init__(self, client, *, public_context=""):
        self.client = client
        self.public_context = public_context

    def converse(self, messages, **options):
        options["system"] = [*options.get("system", []), {"text": CHAT_STYLE}]
        if self.public_context:
            options["system"].append({"text": self.public_context})
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
