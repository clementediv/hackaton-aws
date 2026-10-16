"""Human-facing officer workspace, separate from the developer lab."""

import json
import os
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
from ruta import config, staff_auth
from ruta.colador import Funnel
from ruta.ejecutivos import DEMO_DB, STATUS, case_rows, demo_snapshot, next_action
from ruta.report_heatmap import campaign_context
from ui_campanas import campaign_map

ASSETS = Path(__file__).parent / "assets"
VIEWS = ["Seguimiento de casos", "Campañas en terreno", "Trazabilidad", "Reportería institucional"]
EVENTS = {
    "attempt": "Se intentó contactar",
    "contacted": "Contacto confirmado",
    "answered": "La persona respondió",
    "opened": "Abrió el correo",
    "started": "Inició su trámite",
    "declined": "Declinó el acompañamiento",
    "queued": "Pendiente de atención en terreno",
    "skipped": "Canal sin datos de contacto",
    "entered": "Inicio de seguimiento por este canal",
    "signal": "Nueva alerta en el caso",
}
CHANNELS = {1: "Correo electrónico", 2: "Llamada", 3: "Contacto laboral", 4: "Terreno"}


def _sign_out():
    for key in list(st.session_state):
        if key.startswith("staff_") and key != "staff_deeplink_loaded":
            del st.session_state[key]


def _sign_in():
    password = st.session_state.pop("staff_login_password", "")
    try:
        email = staff_auth.authenticate(st.session_state.get("staff_login_email", ""), password)
    except ValueError as error:
        st.session_state["staff_login_error"] = str(error)
        return
    _sign_out()
    st.session_state["staff_authenticated_user"] = email


def require_login():
    """Gate both officer entry points before reading a campaign snapshot."""
    st.html("<style>" + (ASSETS / "executive.css").read_text(encoding="utf-8") + "</style>")
    email = st.session_state.get("staff_authenticated_user")
    account = staff_auth.DEMO_ACCOUNTS.get(email)
    if account:
        identity, actions = st.columns([3, 1], vertical_alignment="center")
        identity.caption(f"{account['name']} · {account['role']} · Sesión de demostración")
        actions.button("Cerrar sesión de ejecutivo", key="staff_logout", on_click=_sign_out)
        return True
    with st.container(key="staff_login"):
        intro, form = st.columns([1.15, 1], gap="large", vertical_alignment="top")
        intro.html(
            '<div class="staff-login-intro"><div class="staff-eyebrow">PARA EJECUTIVOS</div>'
            "<h1>Acompañar comienza<br>con saber quién espera.</h1>"
            "<p>Revisa los casos alertados, orienta el próximo paso y organiza "
            "la atención en terreno desde un solo lugar.</p></div>"
        )
        with form, st.container(key="staff_login_card"):
            st.markdown("### Ingresa al portal de ejecutivos")
            with st.form("staff_login_form", clear_on_submit=True):
                st.text_input(
                    "Correo",
                    key="staff_login_email",
                    placeholder="ejecutivo.rm@example.com",
                    max_chars=120,
                )
                st.text_input("Clave", type="password", key="staff_login_password", max_chars=120)
                st.form_submit_button(
                    "Ingresar como ejecutivo",
                    type="primary",
                    use_container_width=True,
                    on_click=_sign_in,
                )
            if error := st.session_state.get("staff_login_error"):
                st.error(error)
            with st.expander("Datos de acceso de demostración", expanded=True):
                selected = st.selectbox(
                    "Cuenta ficticia",
                    list(staff_auth.DEMO_ACCOUNTS),
                    key="staff_demo_account",
                    format_func=lambda value: staff_auth.DEMO_ACCOUNTS[value]["name"],
                )
                st.code(f"Correo: {selected}\nClave: {staff_auth.DEMO_PASSWORD}", language=None)
                st.caption(
                    "Cuentas ficticias para probar el portal. Usa solo estos datos de ejemplo."
                )
    return False


def _cards(state):
    totals = state["totals"]
    cards = [
        ("Personas alertadas", totals["detected"], "Personas únicas en esta campaña", ""),
        ("Por contactar", totals["active"], "Aún no confirman una respuesta", "amber"),
        ("Esperan orientación", totals["contacted"], "Respondieron; necesitan acompañamiento", ""),
        ("Iniciaron su trámite", totals["started"], "El acompañamiento continúa", "green"),
    ]
    st.html(
        '<div class="staff-stats">'
        + "".join(
            f'<div class="staff-stat {tone}"><div class="label">{label}</div>'
            f'<div class="number">{count}</div><div class="note">{note}</div></div>'
            for label, count, note, tone in cards
        )
        + "</div>"
    )


def _tracking(state):
    totals = state["totals"]
    st.html(
        '<div class="staff-callout"><strong>El siguiente paso es acompañar.</strong><br>'
        f"{totals['contacted']} personas respondieron y aún no inician su trámite. "
        "Ayúdalas a preparar sus documentos y acordar cómo continuar.<br>"
        "<small>Una respuesta detiene los otros canales. "
        "Quienes declinaron no vuelven a contactarse.</small></div>"
    )
    st.markdown("### Así van los contactos")
    st.html(
        '<div class="staff-process">'
        + "".join(
            f'<div class="staff-step"><h3><span class="step-num">{row["stage"]}</span>'
            f"{CHANNELS[row['stage']]}</h3><strong>"
            f"{row['active'] if row['stage'] == 4 else row['confirmed']}</strong>"
            f"<p>{'pendientes de atención' if row['stage'] == 4 else 'personas que respondieron'}"
            "</p>"
            "</div>"
            for row in state["funnel"]
        )
        + "</div>"
    )
    st.caption(
        f"{totals['declined']} personas decidieron no continuar. "
        "Las cifras cuentan personas; un mismo caso puede tener varios intentos de contacto."
    )
    st.html(
        '<div class="staff-kpi"><b>Meta de avance: al menos 75%.</b> '
        "El próximo paso completado dentro del plazo aún está pendiente de medición. "
        "Responder o iniciar el trámite no demuestra por sí solo su cumplimiento.</div>"
    )
    st.markdown("### Personas que necesitan seguimiento")
    filters = st.columns([2, 1.2, 1.2])
    search = filters[0].text_input("Buscar persona", placeholder="Nombre o RUN", key="staff_search")
    status = filters[1].selectbox(
        "Estado del caso", ["Todos", *STATUS.values()], key="staff_status"
    )
    commune = filters[2].selectbox(
        "Comuna",
        ["Todas las comunas", *sorted({p["contact"]["commune"] for p in state["people"]})],
        key="staff_commune",
    )
    rows = case_rows(state, search=search, status=status, commune=commune)
    if not rows:
        st.info("No hay personas que coincidan con estos filtros.")
        return
    st.dataframe(
        pd.DataFrame(rows).rename(
            columns={
                "run": "RUN",
                "name": "Persona",
                "commune": "Comuna",
                "status": "Situación",
                "next_action": "Cómo continuar",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=300,
    )
    with st.expander("Revisar el seguimiento de una persona", expanded=False):
        options = {r["run"]: f"{r['name']} · {r['run']}" for r in rows}
        selected = st.selectbox(
            "Persona", list(options), format_func=options.get, key="staff_person"
        )
        person = next(p for p in state["people"] if p["run"] == selected)
        st.markdown(f"**{escape(person['name'])}** · {escape(person['contact']['commune'])}")
        st.info(next_action(person))
        contact = person["contact"]
        st.caption(
            f"Contacto de la campaña: {contact['email'] or 'Sin correo'} · "
            f"{contact['phone'] or 'Sin teléfono'}. "
            "No se muestran antecedentes privados del perfil."
        )
        history = [
            {
                "Fecha": e["at"].replace("T", " "),
                "Canal": CHANNELS[e["stage"]],
                "Qué ocurrió": EVENTS.get(e["kind"], "Actualización del caso"),
            }
            for e in state["events"]
            if e["run"] == selected
        ]
        st.dataframe(pd.DataFrame(history), hide_index=True, use_container_width=True)


def _campaign_db(db_path=None):
    """Database of the campaign on screen; its `eventos` log is the audit trail."""
    if db_path is not None:
        return db_path
    if st.session_state.get("staff_source", "Demostración").startswith("Demostración"):
        return os.getenv("STAFF_DEMO_DB") or DEMO_DB
    return config.DB_PATH


def _traceability(state, db_file, *, demo=False, profiles=None):
    import ui_trazabilidad

    ui_trazabilidad.render(state, db_file, demo=demo, profiles=profiles)


def _campaigns(state, profiles):
    st.markdown("### Acercar la atención a quienes todavía esperan")
    st.write(
        "El mapa identifica sectores con personas sin contacto confirmado. "
        "La propuesta se prepara automáticamente para organizar un operativo cercano."
    )
    left, right = st.columns([2.8, 1], gap="large")
    with right:
        st.markdown("#### Tu próximo operativo")
        staff = st.number_input(
            "Personal disponible", min_value=1, max_value=20, value=2, key="staff_team"
        )
        rows, locations, area = campaign_context(state, profiles, staff=int(staff))
        if area:
            info = area["properties"]
            communes = ", ".join(info["communes"])
            st.html(
                '<div class="staff-plan"><h3>Área recomendada</h3>'
                f'<div class="big">{info["people"]} personas</div>'
                f"<p>{escape(communes)}</p><small>{staff} integrantes · "
                f"{info['estimated_days']} jornada(s) estimada(s)</small></div>"
            )
            st.caption(
                f"Cobertura sugerida: {info['radius_m'] / 1000:g} km alrededor del foco. "
                "Estimación de demo: 8 atenciones por integrante al día."
            )
            st.download_button(
                "Descargar propuesta",
                json.dumps(area, ensure_ascii=False, indent=2),
                file_name="propuesta-operativo.geojson",
                mime="application/geo+json",
                use_container_width=True,
            )
        else:
            st.info(
                "No hay un grupo de al menos cinco personas cercanas para proponer un operativo."
            )
        st.caption("Valida la sede, el acceso y la disponibilidad del equipo antes de agendar.")
    with left:
        st.pydeck_chart(
            campaign_map(rows, locations, show_totals=False, campaign_area=area),
            use_container_width=True,
            height=600,
        )
        st.html(
            '<div class="staff-kpi"><b>Concentración de personas</b> &nbsp; Baja '
            '<span style="display:inline-block;width:150px;height:9px;border-radius:8px;'
            'background:linear-gradient(90deg,#38bdf8,#2dd4bf,#facc15,#fb923c,#f43f5e)"></span>'
            " Alta &nbsp; · &nbsp; Contorno amarillo: área propuesta.</div>"
        )
    st.caption(
        f"Región Metropolitana · {len(locations)} ubicaciones representadas. "
        "Se muestran solo comunas con cinco o más casos. Direcciones ficticias; "
        "fuera de la RM y grupos pequeños no aparecen. © CARTO / OpenStreetMap · límites BCN."
    )


def render(profiles, db_path=None):
    if not require_login():
        return
    with st.container(key="staff_workspace"):
        st.html(
            '<div class="staff-hero"><div><div class="staff-eyebrow">PORTAL DE EJECUTIVOS</div>'
            "<h1>Seguimiento y acompañamiento</h1>"
            "<p>Personas que necesitan apoyo, próximos pasos y atención en terreno. "
            "Toda la campaña, en un mismo lugar.</p></div>"
            '<span class="staff-badge">ChileAtiende a Tiempo</span></div>'
        )
        if db_path is None:
            source = st.selectbox(
                "Campaña",
                ["Demostración · Región Metropolitana", "Casos de la aplicación"],
                key="staff_source",
            )
            if source.startswith("Demostración"):
                state = demo_snapshot(profiles, os.getenv("STAFF_DEMO_DB"))
            else:
                state = Funnel(config.DB_PATH).snapshot()
        else:
            state = Funnel(db_path).snapshot()
        st.caption(
            "Prototipo con datos sintéticos · "
            "No agenda visitas ni envía mensajes desde esta página."
        )
        if not state["people"]:
            st.info(
                "Esta campaña aún no tiene casos alertados. "
                "Puedes explorar la campaña de demostración."
            )
        if st.session_state.get("staff_view") not in ("Trazabilidad", "Reportería institucional"):
            _cards(state)
        with st.container(key="staff_navigation"):
            view = st.radio(
                "Secciones de gestión",
                VIEWS,
                horizontal=True,
                label_visibility="collapsed",
                key="staff_view",
            )
        if not state["people"] and view != VIEWS[3]:
            return
        if view == VIEWS[0]:
            _tracking(state)
        elif view == VIEWS[1]:
            _campaigns(state, profiles)
        elif view == VIEWS[2]:
            _traceability(
                state, _campaign_db(db_path),
                demo=db_path is None and st.session_state.get("staff_source", "").startswith("Demostraci"),
                profiles=profiles,
            )

        else:
            import ui_institutional_reports

            ui_institutional_reports.render(
                state, _campaign_db(db_path),
                demo=db_path is None and st.session_state.get("staff_source", "").startswith("Demostraci"),
                profiles=profiles,
            )
