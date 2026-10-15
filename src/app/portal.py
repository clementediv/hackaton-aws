"""ChileAtiende portal shell and the MVP help section."""

import base64
import unicodedata
from html import escape
from pathlib import Path
from time import monotonic
from urllib.parse import quote

import streamlit as st

BASE_URL = "https://www.chileatiende.gob.cl"
LOGO = Path(__file__).resolve().parent / "assets/logo-chileatiende.svg"


def _portal_styles() -> str:
    return (
        "<style>"
        + (LOGO.parent / "fonts.css").read_text(encoding="utf-8")
        + (LOGO.parent / "portal.css").read_text(encoding="utf-8")
        + "</style>"
    )

# Labels/URLs verified in the HTML of the official portal on 2026-10-14.
SERVICES = (
    ("Jubilación", "Pensiones, PGU y orientación para tu jubilación.", "/temas/jubilacion"),
    ("Certificados", "Nacimiento, estudios y antecedentes.", "/temas/certificados"),
    (
        "Subsidio Familiar",
        "Consulta la información oficial sobre el SUF.",
        "/fichas/33112-subsidio-familiar-suf",
    ),
    (
        "Pagos por cobrar",
        "Revisa la ficha de pagos por cobrar del IPS.",
        "/fichas/114831-pagos-por-cobrar-del-instituto-de-prevision-social-ips",
    ),
)


CITIZEN_SECTIONS = ["Inicio", "Mi Gobierno"]
# Back-office tools are reached from the demonstration sidebar.
EXECUTIVE_SECTIONS = [
    "Mapa de calor y campañas",
    "Detectar e invitar",
    "Ficha del beneficiario",
    "Contactos AWS",
    "Atención del caso",
    "Medición",
]


def render_header() -> str:
    st.markdown(_portal_styles(), unsafe_allow_html=True)
    # Preserve the destination of sessions opened before the tools were grouped.
    previous = st.session_state.get("portal_section")
    if previous in EXECUTIVE_SECTIONS and previous != "Atención del caso":
        st.session_state["executive_section"] = previous
        st.session_state["portal_section"] = "Vista ejecutivo"
    if st.session_state.get("portal_section") == "Vista ejecutivo":
        _open_executive()
    if st.session_state.get("portal_section") in ("Trámites", "Mi ruta", "Ayuda para tus trámites"):
        st.session_state["portal_section"] = "Mi Gobierno"
    logo = base64.b64encode(LOGO.read_bytes()).decode("ascii")
    with st.container(key="portal_header"):
        brand, search, utilities = st.columns([1.2, 2.8, 1.2], vertical_alignment="center")
        brand.markdown(
            f'<a href="{BASE_URL}" target="_blank" rel="noopener noreferrer">'
            f'<img class="portal-logo" alt="ChileAtiende" '
            f'src="data:image/svg+xml;base64,{logo}"></a>',
            unsafe_allow_html=True,
        )
        with search:
            render_search()
        with utilities:
            st.link_button("Red de atención", BASE_URL + "/ayuda", use_container_width=True)
    selected = st.radio(
        "Secciones del portal",
        CITIZEN_SECTIONS,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="portal_section",
        on_change=_leave_executive,
    )
    st.sidebar.button("Vista ejecutivo", key="open_executive", on_click=_open_executive)
    return "Vista ejecutivo" if st.session_state.get("portal_executive") else selected or "Inicio"


def _open_executive() -> None:
    st.session_state["portal_executive"] = True
    st.session_state["portal_section"] = None


def _leave_executive() -> None:
    st.session_state.pop("portal_executive", None)


def hero(section: str) -> None:
    if section not in ("Inicio", "Mi Gobierno"):
        st.markdown(
            f'<div class="portal-breadcrumb"><a href="{BASE_URL}">Inicio</a>'
            f" &nbsp;›&nbsp; {escape(section)}</div>",
            unsafe_allow_html=True,
        )
    if text := st.session_state.get("portal_query"):
        matches = search_services(text)
        st.caption(f"Resultados para “{text}”")
        for title, _description, path in matches:
            st.link_button(title, BASE_URL + path)
        if not matches:
            st.info("Puedes continuar tu búsqueda en el portal oficial.")
        st.link_button(
            "Ver todos los resultados en ChileAtiende", BASE_URL + "/buscar?query=" + quote(text)
        )


def render_search() -> None:
    with st.form("portal_search", border=False):
        query_col, button_col = st.columns([4, 1.3], vertical_alignment="center")
        query = query_col.text_input(
            "¿Qué trámite necesitas?",
            placeholder="Buscar trámites y beneficios",
            label_visibility="collapsed",
        )
        submitted = button_col.form_submit_button("Buscar", use_container_width=True)
    if submitted and query.strip():
        st.session_state["portal_query"] = query.strip()


def search_services(query: str) -> list[tuple[str, str, str]]:
    def normalize(value):
        return "".join(
            char
            for char in unicodedata.normalize("NFD", value.lower())
            if not unicodedata.combining(char)
        )

    tokens = normalize(query).split()
    return [
        entry
        for entry in SERVICES
        if all(token in normalize(entry[0] + " " + entry[1]) for token in tokens)
    ]


def render_discovery() -> None:
    """Public ChileAtiende homepage with an invitation to the personal workspace."""
    assets = LOGO.parent
    styles = (assets / "official-home.css").read_text(encoding="utf-8")
    content = (assets / "official-home.html").read_text(encoding="utf-8")
    content = content.split("</section>", 1)[1]
    _render_home_banner()
    st.html(f'<style>{styles}</style><div class="official-home">{content}</div>')


def _queue_home_question(question: str) -> None:
    st.session_state["portal_pending_question"] = question
    st.session_state["portal_next_section"] = "Mi Gobierno"
    st.rerun(scope="app")


@st.fragment(run_every="5s")
def _render_home_banner() -> None:
    now = monotonic()
    previous = st.session_state.setdefault("home_banner_last_rotation", now)
    slide = st.session_state.setdefault("home_banner_slide", "Beneficios")
    if not st.session_state.get("home_banner_chat_open") and now - previous >= 5:
        st.session_state["home_banner_slide"] = (
            "Asistente IA" if slide == "Beneficios" else "Beneficios"
        )
        st.session_state["home_banner_last_rotation"] = now
    with st.container(border=True, key="home_government"):
        active = st.session_state["home_banner_slide"]
        slide_key = "assistant" if active == "Asistente IA" else "benefits"
        with st.container(key=f"home_slide_{slide_key}"):
            if active == "Asistente IA":
                _render_home_assistant()
            else:
                _render_home_benefits()


def _render_home_benefits() -> None:
    with st.container(key="home_government_invitation"):
        st.markdown(
            '<div class="home-government">'
            "<h1>Hay beneficios que podrían<br>hacer tu día a día más fácil.</h1>"
            "<p>Descubre cuáles podrían corresponderte según tu situación. "
            "Reúne tus antecedentes y encuentra los pasos para recibirlos, "
            "en un solo lugar.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Ver mis beneficios",
            type="primary",
            key="home_government_access",
        ):
            st.session_state["portal_next_section"] = "Mi Gobierno"
            st.rerun(scope="app")


def _render_home_assistant() -> None:
    st.markdown(
        '<div class="home-government home-assistant-intro">'
        "<h1>Prueba el asistente de inteligencia artificial</h1>"
        "<p>Resuelve preguntas frecuentes sobre tr?mites y beneficios.</p></div>",
        unsafe_allow_html=True,
    )
    st.session_state["home_banner_chat_open"] = True
    with st.container(key="home_chat_preview"):
        with st.form("home_agent_question", border=False):
            question = st.text_input(
                "Escribe tu pregunta",
                key="home_agent_question_text",
                placeholder="Pregunta lo que necesites?",
                label_visibility="collapsed",
                max_chars=2000,
            )
            if st.form_submit_button("Enviar", type="primary", icon=":material/arrow_upward:"):
                if question.strip():
                    _queue_home_question(question.strip())
                else:
                    st.warning("Escribe una pregunta para continuar.")
    with st.container(key="home_chat_suggestions"):
        examples = st.columns(2)
        for index, question in enumerate(("?Qu? es la PGU?", "?Qu? documentos necesito?")):
            if examples[index].button(
                question, key=f"home_example_{index}", use_container_width=True
            ):
                _queue_home_question(question)


def open_section(section: str) -> None:
    _leave_executive()
    st.session_state["portal_section"] = section


def render_directory() -> None:
    st.markdown('<h2 class="portal-section">Trámites y beneficios</h2>', unsafe_allow_html=True)
    st.write(
        "Elige un trámite para consultar sus requisitos y canales de atención en ChileAtiende."
    )
    query = st.text_input("Filtrar trámites", placeholder="Jubilación, certificados, subsidio…")
    entries = search_services(query) if query.strip() else list(SERVICES)
    if not entries:
        st.info("No hay coincidencias en esta selección. Busca en el catálogo oficial.")
        st.link_button("Buscar en ChileAtiende ↗", BASE_URL + "/buscar?query=" + quote(query))
    columns = st.columns(2)
    for index, (title, description, path) in enumerate(entries):
        with columns[index % 2], st.container(border=True):
            st.subheader(title)
            st.write(description)
            st.link_button("Ver requisitos y dónde realizarlo ↗", BASE_URL + path)
    st.link_button("Ver todos los servicios del Estado ↗", BASE_URL + "/temas")
    st.button(
        "Necesito ayuda para elegir", on_click=open_section, args=("Mi Gobierno",)
    )


def render_footer() -> None:
    st.markdown(
        '<footer class="portal-footer"><div><b>ChileAtiende a Tiempo</b><br>'
        "Prototipo de ayuda para trámites · Hackatón AWS 2026</div>"
        f'<div><b>Servicios del Estado</b><br><a href="{BASE_URL}/temas">Explorar por temas</a>'
        f'<br><a href="{BASE_URL}/instituciones">Instituciones</a></div>'
        f'<div><b>¿Necesitas ayuda?</b><br><a href="{BASE_URL}/ayuda/atencion-telefonica">'
        "Call Center 101</a><br>"
        f'<a href="{BASE_URL}/sucursalvirtual">Videoatención</a></div></footer>',
        unsafe_allow_html=True,
    )
