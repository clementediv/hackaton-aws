"""ChileAtiende portal shell and the MVP help section."""

import base64
import re
import time
import unicodedata
from html import escape
from pathlib import Path
from urllib.parse import quote

import streamlit as st

BASE_URL = "https://www.chileatiende.gob.cl"
LOGO = Path(__file__).resolve().parent / "assets/logo-chileatiende.svg"
# Shown under the logo, as in the emails sent by the proactive detection.
INSTITUTION = "Instituto de Previsión Social"


def _portal_styles() -> str:
    return (
        "<style>"
        + (LOGO.parent / "fonts.css").read_text(encoding="utf-8")
        + (LOGO.parent / "portal.css").read_text(encoding="utf-8")
        + (LOGO.parent / "motion.css").read_text(encoding="utf-8")
        + (LOGO.parent / "public-chat.css").read_text(encoding="utf-8")
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


CITIZEN_SECTIONS = ["Inicio", "Mi Gobierno", "Asistente de IA"]
# Back-office tools are reached from the demonstration sidebar.
EXECUTIVE_SECTIONS = [
    "Mapa de calor y campañas",
    "Detectar e invitar",
    "Ficha del beneficiario",
    "Contactos AWS",
    "Atención del caso",
    "Medición",
]


def render_header(*, chat_page: bool = False) -> str:
    st.markdown(_portal_styles(), unsafe_allow_html=True)
    if st.query_params.get("vista") == "ejecutivos" and not st.session_state.get(
        "staff_deeplink_loaded"
    ):
        st.session_state["staff_deeplink_loaded"] = True
        _open_staff()
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
            f'<div class="portal-brand"><a href="{BASE_URL}" target="_blank" '
            f'rel="noopener noreferrer"><img class="portal-logo" alt="ChileAtiende" '
            f'src="data:image/svg+xml;base64,{logo}"></a>'
            f'<span class="portal-institution">{INSTITUTION}</span></div>',
            unsafe_allow_html=True,
        )
        with search:
            render_search()
        with utilities:
            st.link_button("Red de atención", BASE_URL + "/ayuda", use_container_width=True)
            st.button(
                "Para ejecutivos", on_click=_open_staff, key="open_staff_header",
                use_container_width=True,
            )
    selected = st.radio(
        "Secciones del portal",
        CITIZEN_SECTIONS,
        index=2 if chat_page else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="chat_portal_section" if chat_page else "portal_section",
        on_change=_navigate_from_chat if chat_page else _leave_executive,
    )
    st.sidebar.button("Vista ejecutivo", key="open_executive", on_click=_open_executive)
    if st.session_state.get("portal_staff_workspace"):
        return "Portal ejecutivo"
    return "Vista ejecutivo" if st.session_state.get("portal_executive") else selected or "Inicio"


def _open_staff() -> None:
    st.session_state["portal_staff_workspace"] = True
    st.session_state.pop("portal_executive", None)
    st.session_state["portal_section"] = None


def _open_executive() -> None:
    st.session_state.pop("portal_staff_workspace", None)
    st.session_state["portal_executive"] = True
    st.session_state["portal_section"] = None


def _navigate_from_chat() -> None:
    section = st.session_state["chat_portal_section"]
    if section != "Asistente de IA":
        st.session_state["portal_next_section"] = section


def _leave_executive() -> None:
    st.session_state.pop("portal_executive", None)
    st.session_state.pop("portal_staff_workspace", None)
    st.query_params.pop("vista", None)


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
    st.session_state["public_chat_pending"] = question
    st.switch_page(st.Page(render_chat_page, title="Asistente ChileAtiende", url_path="chat"))


def render_chat_page() -> None:
    st.session_state.pop("government_last_observed_view", None)
    from chat_feedback import TYPING_HTML, scroll_chat
    from ruta.asistente import responder_publico, _template_stream
    from ruta import casos
    from ruta.datos import cargar_perfiles
    from ruta.pgu_review import is_personal_pgu_question, review_pgu

    if st.session_state.get("portal_next_section"):
        st.switch_page(st.session_state["portal_home_page"])
    st.session_state["chat_portal_section"] = "Asistente de IA"
    render_header(chat_page=True)
    with st.container(key="public_chat_header"):
        brand, actions = st.columns([3, 1], vertical_alignment="center")
        with brand:
            st.page_link(st.session_state["portal_home_page"], label="← ChileAtiende")
        with actions:
            if st.button("Nueva conversación", key="public_chat_reset", use_container_width=True):
                st.session_state["public_chat_history"] = []
                st.session_state.pop("public_chat_pending", None)
                st.session_state.pop("public_chat_engine", None)
                st.rerun()
    run = st.session_state.get("government_login_run")
    case = casos.obtener_caso(run) if run else None
    access = (run, bool(case and case.get("autorizacion")))
    if st.session_state.get("public_chat_access") != access:
        st.session_state["public_chat_history"] = [
            m for m in st.session_state.get("public_chat_history", [])
            if m.get("scope") != "personal"
        ]
        st.session_state["public_chat_access"] = access
    with st.container(key="public_chat"):
        history = st.session_state.setdefault("public_chat_history", [])
        pending = st.session_state.pop("public_chat_pending", None)
        if not history and not pending:
            st.markdown(
                '<div class="public-chat-welcome">'
                '<h2>Hola, ¿en qué te ayudamos?</h2>'
                '<p>Encuentra tu próximo paso en trámites y beneficios del Estado.</p></div>',
                unsafe_allow_html=True,
            )
            _render_public_chat_input()
        for index, message in enumerate(history):
            with st.container(key=f"public_message_{message['rol']}_{index}"):
                st.chat_message(message["rol"]).write(message["texto"])
        if pending:
            index = len(history)
            with st.container(key=f"public_message_user_{index}"):
                st.chat_message("user").write(pending)
            with st.container(key=f"public_message_assistant_{index + 1}"):
                with st.chat_message("assistant"):
                    response = st.empty()
                    response.markdown(TYPING_HTML, unsafe_allow_html=True)
                    scroll_chat(".st-key-public_chat", f"sent:{index}:{pending}")
                    try:
                        personal = is_personal_pgu_question(
                            pending, pgu_context=bool(history and history[-1].get("scope") == "personal")
                        )
                        if personal:
                            chunks = _template_stream(review_pgu(run, case, cargar_perfiles))
                            engine = "reglas"
                        else:
                            public_history = [m for m in history if m.get("scope") != "personal"]
                            chunks, engine = responder_publico(pending, public_history, stream=True)
                    except Exception:
                        response.empty()
                        raise
                    parts = []

                    def visible_chunks():
                        try:
                            for chunk in chunks:
                                parts.append(chunk)
                                if engine == "bedrock":
                                    for word in re.findall(r"\s+|\S+\s*", chunk):
                                        yield word
                                        time.sleep(0.08)
                                else:
                                    yield chunk
                        except Exception:
                            notice = "\n\nLa respuesta se interrumpió. Puedes volver a preguntar."
                            parts.append(notice)
                            yield notice

                    response.empty()
                    st.write_stream(visible_chunks())
            history.extend([
                {"rol": "user", "texto": pending, "scope": "personal" if personal else "public"},
                {"rol": "assistant", "texto": "".join(parts),
                 "scope": "personal" if personal else "public"},
            ])
            st.session_state["public_chat_engine"] = engine
        scroll_chat(".st-key-public_chat", f"received:{history!r}")
    if history:
        if history[-1].get("scope") == "personal":
            with st.container(key="public_chat_pgu_action"):
                if st.button("Revisar o completar antecedentes en Mi Gobierno", key="chat_pgu_review"):
                    st.session_state["portal_next_section"] = "Mi Gobierno"
                    if run and case and case.get("autorizacion"):
                        st.session_state[f"government_view_{run}"] = "Beneficios"
                        st.session_state[f"government_route_{run}"] = "pgu"
                    st.switch_page(st.session_state["portal_home_page"])
        _render_public_chat_input()
    from voice import voice_input

    with st.container(key="public_chat_voice"):
        latest_reply = next((m["texto"] for m in reversed(history) if m["rol"] == "assistant"), "")
        spoken = voice_input(
            key="voice_public_chat", reply=latest_reply, message_id=str(len(history)), compact=True
        )
    if spoken:
        st.session_state["public_chat_pending"] = spoken
        st.rerun()


def _render_public_chat_input() -> None:
    import streamlit.components.v1 as components

    with st.container(key="public_chat_placeholder_animation"):
        components.html(
            (LOGO.parent / "chat-placeholder.html").read_text(encoding="utf-8"),
            height=0,
        )
    if question := st.chat_input("Describe lo que necesitas", max_chars=2000, key="public_chat_input"):
        st.session_state["public_chat_pending"] = question
        st.rerun()


def _render_home_banner() -> None:
    with st.container(border=False, key="home_government"):
        with st.container(key="home_slide_assistant"):
            _render_home_assistant()
        with st.container(key="home_slide_benefits"):
            _render_home_benefits()


def _render_home_benefits() -> None:
    with st.container(key="home_government_invitation"):
        st.markdown(
            '<div class="home-government home-benefits-intro">'
            '<span class="home-benefit-category">EJEMPLO ILUSTRATIVO</span>'
            "<h1>Cumples todos los requisitos para la PGU</h1>"
            "<p>Tu beneficio, listo para cobrar.</p>"
            '<ul class="home-pgu-checklist" aria-label="Ejemplo ilustrativo de revisión PGU">'
            '<li style="--check-index:0"><span class="home-pgu-check" aria-hidden="true">✓</span>'
            '<span>Edad para solicitar la PGU</span></li>'
            '<li style="--check-index:1"><span class="home-pgu-check" aria-hidden="true">✓</span>'
            '<span>Antecedentes de ingresos</span></li>'
            '<li style="--check-index:2"><span class="home-pgu-check" aria-hidden="true">✓</span>'
            '<span>Residencia en Chile</span></li>'
            '<li style="--check-index:3"><span class="home-pgu-check" aria-hidden="true">✓</span>'
            '<span>Pensión base</span></li>'
            '</ul>'
            '<p class="home-benefit-note">Consulta tu revisión personal en Mi Gobierno. El IPS confirma el beneficio y su pago.</p>'
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Revisar mis requisitos",
            type="primary",
            key="home_government_access",
        ):
            st.session_state["portal_next_section"] = "Mi Gobierno"
            st.rerun(scope="app")


def _render_home_assistant() -> None:
    st.markdown(
        '<div class="home-government home-assistant-intro">'
        "<h1>Prueba el asistente de inteligencia artificial de ChileAtiende</h1>"
        "<p>Encuentra tu próximo paso en trámites y beneficios del Estado.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    examples = (
        ("¿Qué documentos necesito?", "En Mi Gobierno, abre tu beneficio y revisa los antecedentes de cada paso."),
        ("¿Por dónde empiezo?", "Ingresa a Mi Gobierno y autoriza la consulta de tus antecedentes para preparar tu ruta."),
        ("¿Puedo continuar después?", "Sí. Tu avance queda guardado para retomar desde el próximo paso pendiente."),
    )
    cards = "".join(
        f'<div class="home-answer-example" style="--example-index:{index}">'
        f'<div class="home-example-question">{escape(question)}</div>'
        '<div class="home-example-answer"><span>Asistente ChileAtiende</span>'
        '<div class="home-example-answer-text">'
        + " ".join(
            f'<span style="--word-index:{word_index}">{escape(word)}</span>'
            for word_index, word in enumerate(answer.split())
        ) + '</div></div></div>'
        for index, (question, answer) in enumerate(examples)
    )
    st.html(
        '<div class="home-answer-examples" aria-label="Ejemplos de preguntas y respuestas">'
        + cards + '</div>'
    )
    with st.container(key="home_chat_preview"):
        with st.form("home_agent_question", border=False):
            text_column, send_column = st.columns([5, 1], gap="small", vertical_alignment="center")
            question = text_column.text_input(
                "Escribe tu pregunta",
                key="home_agent_question_text",
                placeholder="Describe lo que necesitas",
                label_visibility="collapsed",
                max_chars=2000,
            )
            if send_column.form_submit_button("Enviar", type="primary", use_container_width=True):
                if question.strip():
                    _queue_home_question(question.strip())
                else:
                    st.warning("Escribe una pregunta para continuar.")


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
