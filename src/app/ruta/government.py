"""Personal workspace data and deterministic benefit actions for the local demo."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from . import casos, config
from . import reglas as rules
from .rutas import generar_ruta

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024

EDUCATION_CALENDAR_SOURCE = "https://postulacion.beneficiosestudiantiles.cl/fuas/index.php"


def benefit_timeline(benefit: str, diagnosis=None, reference: date | None = None) -> dict:
    """Separate personal progress from published dates; no submission is inferred."""
    reference = reference or config.FECHA_REFERENCIA
    current = {"title": "Postulación", "status": "Faltan datos", "tone": "pending"}
    review = {"title": "En revisión", "status": "Aún no inicia", "tone": "upcoming"}
    result = {"title": "Resultado", "status": "Sin resultado todavía", "tone": "upcoming"}
    if benefit == "pgu":
        if diagnosis is None:
            raise ValueError("La línea de tiempo PGU necesita un diagnóstico.")
        opening = diagnosis.hitos.fecha_apertura_pgu
        current["date"] = (
            f"Desde el {opening:%d-%m-%Y}" if reference < opening else "Durante todo el año"
        )
        current["detail"] = "Fechas para postular · no hay una fecha anual de cierre."
        current["status"] = {
            rules.ELEGIBLE: "Todo listo para postular",
            rules.ANTECEDENTE_FALTANTE: "Faltan datos",
            rules.NO_ELEGIBLE: "Hoy no cumples los requisitos",
            rules.FUTURO: "Disponible más adelante",
            rules.PROXIMO: "Preparar solicitud",
            rules.YA_RECIBE: "Ya recibes este beneficio",
        }.get(diagnosis.pgu.resultado, "No disponible")
        if diagnosis.pgu.resultado == rules.ELEGIBLE:
            current["tone"] = "ready"
        review.update(date="Fecha por confirmar", detail="El IPS revisa tu solicitud al recibirla.")
        result.update(
            date="Fecha por confirmar",
            detail=(
                "Aquí verás si fue aprobado, rechazado o cancelado cuando exista una resolución."
            ),
        )
        if diagnosis.pgu.resultado == rules.YA_RECIBE:
            current["tone"] = "ready"
            review.update(
                status="Finalizada",
                tone="ready",
                date="Fecha no informada",
                detail="El registro compartido indica una PGU vigente.",
            )
            result.update(
                status="Beneficio vigente",
                tone="ready",
                date="Fecha no informada",
                detail="Ya recibes la PGU según los antecedentes compartidos.",
            )
        source = config.FUENTE_PGU
        note = "Estar listo para postular no significa que el IPS haya aprobado el beneficio."
    elif benefit in ("fuas", "gratuidad", "becas"):
        current.update(
            date="1 al 22 de octubre de 2026",
            detail="Fechas para postular · primer periodo FUAS, año académico 2027.",
        )
        if reference > date(2026, 10, 22):
            current["detail"] += " Este periodo ya cerró; consulta nuevas fechas en Mineduc."
        review.update(
            date="17 de diciembre de 2026",
            detail="Publicación del nivel socioeconómico. Preselección: 15 de enero de 2027.",
        )
        result.update(
            date="10 de marzo de 2027",
            detail="Fecha de asignación. Aquí verás si fue aprobado, rechazado o cancelado.",
        )
        source = EDUCATION_CALENDAR_SOURCE
        note = (
            "Fechas del calendario Mineduc, no una confirmación de tu postulación. "
            "FUAS es el formulario para acceder a beneficios."
        )
    else:
        raise ValueError("Beneficio sin línea de tiempo.")
    return {"steps": (current, review, result), "source": source, "note": note}


# Extend this list to add another row. These entries have no eligibility engine yet.
# FUAS is an application form, not a cash benefit.
EDUCATION_OPTIONS = (
    {
        "id": "fuas",
        "title": "FUAS · Acceso a beneficios estudiantiles",
        "description": "Formulario para acceder a gratuidad, becas y créditos. No es un pago.",
        "missing": (
            "Tu situación de estudios actual.",
            "Los integrantes e ingresos de tu grupo familiar declarados en FUAS.",
            "Si completaste el FUAS y tienes su comprobante de inscripción.",
        ),
        "source": "https://postulacion.beneficiosestudiantiles.cl/fuas/index.php",
    },
    {
        "id": "gratuidad",
        "title": "Gratuidad en educación superior",
        "description": "Apoyo para financiar tus estudios en una institución adscrita.",
        "missing": (
            "Tu evaluación socioeconómica de Mineduc a partir del FUAS.",
            "La institución y carrera donde te matriculas.",
            "Tu historial de estudios, títulos previos y beneficios anteriores.",
            "Nacionalidad o antecedentes de residencia, según corresponda.",
        ),
        "source": "https://portal.beneficiosestudiantiles.cl/gratuidad",
    },
    {
        "id": "becas",
        "title": "Becas de educación superior",
        "description": "Ayudas para financiar el arancel, según cada beca y tu situación.",
        "missing": (
            "La beca que quieres revisar y si ingresas o ya cursas una carrera.",
            "Tu información socioeconómica y antecedentes FUAS.",
            "Tus antecedentes académicos: NEM o PAES, según la beca.",
            "La institución, carrera y matrícula para revisar sus requisitos.",
        ),
        "source": "https://portal.beneficiosestudiantiles.cl/becas/becas-de-arancel",
    },
)
DOCUMENT_TYPES = (
    "Registro Social de Hogares",
    "Cédula de identidad",
    "Licencia de conducir",
    "Antecedentes",
    "Comprobante de ingresos",
    "Comprobante FUAS",
    "Certificado de matrícula",
    "Antecedentes académicos",
    "Certificado de residencia",
)

# Shared document types used to prepare applications; uploads remain unverified.
BENEFIT_DOCUMENTS = {
    "pgu": ("Cédula de identidad", "Registro Social de Hogares", "Certificado de residencia"),
    "fuas": (
        "Cédula de identidad",
        "Registro Social de Hogares",
        "Comprobante de ingresos",
        "Comprobante FUAS",
    ),
    "gratuidad": ("Registro Social de Hogares", "Comprobante FUAS", "Certificado de matrícula"),
    "becas": (
        "Registro Social de Hogares",
        "Comprobante FUAS",
        "Certificado de matrícula",
        "Antecedentes académicos",
    ),
}


@contextmanager
def _connection():
    with sqlite3.connect(config.DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS government_profiles (
                run TEXT PRIMARY KEY, data TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS government_documents (
                run TEXT NOT NULL, kind TEXT NOT NULL, name TEXT NOT NULL,
                size INTEGER NOT NULL, digest TEXT NOT NULL, content BLOB NOT NULL,
                PRIMARY KEY (run, kind)
            );
        """)
        yield connection


def _require_consent(run: str) -> None:
    if not casos.obtener_caso(run)["autorizacion"]:
        raise PermissionError("Autoriza el uso de antecedentes antes de continuar.")


def load_profile(run: str) -> dict:
    _require_consent(run)
    with _connection() as connection:
        row = connection.execute(
            "SELECT data FROM government_profiles WHERE run=?", (run,)
        ).fetchone()
    return json.loads(row["data"]) if row else {}


def save_profile(run: str, data: dict) -> None:
    _require_consent(run)
    # Self-reported fields never overwrite the institutional dataset or its eligibility rules.
    allowed = {
        key: data[key]
        for key in (
            "employment",
            "monthly_income",
            "household_size",
            "notes",
            "profession",
            "occupation",
            "economic_activity",
            "email",
        )
        if key in data
    }
    with _connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO government_profiles(run,data) VALUES (?,?)",
            (run, json.dumps(allowed, ensure_ascii=False)),
        )


def save_document(run: str, kind: str, name: str, content: bytes) -> None:
    _require_consent(run)
    if kind not in DOCUMENT_TYPES:
        raise ValueError("Tipo de documento no permitido.")
    if not content or len(content) > MAX_DOCUMENT_BYTES:
        raise ValueError("El documento debe pesar entre 1 byte y 10 MB.")
    suffix = Path(name).suffix.lower()
    valid = (
        (suffix == ".pdf" and content.startswith(b"%PDF-"))
        or (suffix in (".jpg", ".jpeg") and content.startswith(b"\xff\xd8\xff"))
        or (suffix == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
    )
    if not valid:
        raise ValueError("Adjunta un PDF, JPG o PNG válido.")
    name = name.replace("\\", "/").rsplit("/", 1)[-1][:160]
    with _connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO government_documents VALUES (?,?,?,?,?,?)",
            (run, kind, name, len(content), hashlib.sha256(content).hexdigest(), content),
        )


def list_documents(run: str) -> list[dict]:
    _require_consent(run)
    with _connection() as connection:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT kind,name,size,digest FROM government_documents WHERE run=? ORDER BY kind",
                (run,),
            )
        ]


def delete_document(run: str, kind: str) -> None:
    _require_consent(run)
    with _connection() as connection:
        connection.execute("DELETE FROM government_documents WHERE run=? AND kind=?", (run, kind))


def delete_personal_data(run: str) -> None:
    with _connection() as connection:
        connection.execute("DELETE FROM government_documents WHERE run=?", (run,))
        connection.execute("DELETE FROM government_profiles WHERE run=?", (run,))


def pgu_action(diagnosis: rules.Diagnostico) -> tuple[str, str, bool]:
    """Status, action label and permission to open a PGU preparation route."""
    status = diagnosis.pgu.resultado
    if not diagnosis.vivo:
        return "No corresponde", "No disponible", False
    if status == rules.ELEGIBLE:
        return "Cumples los requisitos evaluados", "Cobrar beneficio", True
    if status == rules.PROXIMO:
        if config.FECHA_REFERENCIA >= diagnosis.hitos.fecha_apertura_pgu:
            return "Puedes iniciar tu solicitud", "Preparar solicitud", True
        return "Disponible más adelante", "Preparar mi beneficio", True
    if status == rules.ANTECEDENTE_FALTANTE:
        return "Faltan antecedentes", "Completar antecedentes", True
    if status == rules.YA_RECIBE:
        return "Ya lo recibes", "Consultar mi pago", True
    if status == rules.NO_ELEGIBLE:
        return "Hoy no cumples los requisitos", "No disponible", False
    return "Aún no cumples la edad", "No disponible", False


def benefit_route(diagnosis: rules.Diagnostico, benefit: str):
    """Keep the selected benefit and its dependency closure, preserving original step IDs."""
    route = generar_ruta(diagnosis)
    targets = {step.id for step in route if step.tramite == benefit}
    if benefit == "PGU" and diagnosis.pgu.resultado == rules.YA_RECIBE:
        targets.update(step.id for step in route if step.id == "S1")
    while True:
        dependencies = {
            dependency for step in route if step.id in targets for dependency in step.depende_de
        }
        if dependencies <= targets:
            break
        targets |= dependencies
    return [step for step in route if step.id in targets]
