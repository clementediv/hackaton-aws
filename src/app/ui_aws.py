"""Contactos AWS: what the proactive detection on AWS detected, sent and recorded.

The Lambdas detect, send and escalate. The app shows it to the officer, lets
them simulate a life event (it only changes the person's data), shows the
citizen in Mi Gobierno what was sent to them, and records answers given in the
app so AWS stops escalating. Design: 20-arquitectura/app-aws-conectada.md.
"""

import logging
import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from ruta import aws_contactos as aws

YES = "✓"
log = logging.getLogger(__name__)
MARITAL = {
    "Sin cambio": None,
    "Casado(a)": "casado",
    "Acuerdo de Unión Civil": "AUC",
    "Soltero(a)": "soltero",
}


@st.cache_data(ttl=20, show_spinner="Leyendo contactos desde AWS…")
def _contacts() -> list[dict]:
    return aws.load_contacts()


@st.cache_data(ttl=20, show_spinner=False)
def _person_contacts(run: str) -> list[dict]:
    return aws.contacts_for(run)


@st.cache_data(ttl=300, show_spinner=False)
def _people() -> list[dict]:
    return aws.load_people()


def _clear() -> None:
    _contacts.clear()
    _person_contacts.clear()
    _history.clear()


def sync_answer(run: str, accepted: bool, channel: str) -> None:
    """Listener of `casos.responder_invitacion`: the answer also stops AWS.
    The app keeps working when AWS is unavailable; the error goes to the log."""
    try:
        if aws.sync_invitation(run, accepted, channel):
            _clear()
    except Exception:  # noqa: BLE001 - the answer is already saved in the app
        log.warning("No se pudo registrar en AWS la respuesta de %s", run, exc_info=True)


def _when(iso: str) -> str:
    """UTC ISO timestamp → Chilean date."""
    try:
        return (datetime.fromisoformat(iso) - timedelta(hours=3)).strftime("%d-%m-%Y")
    except (TypeError, ValueError):
        return ""


def _answer(run: str, benefit_id: str, answer: str) -> None:
    try:
        aws.record_answer(run, benefit_id, answer, "Mi Gobierno")
    except Exception:  # noqa: BLE001
        log.warning("No se pudo registrar en AWS la respuesta de %s", run, exc_info=True)
        st.session_state["aws_answer_error"] = True
    _clear()


def citizen_notices(run: str) -> None:
    """In Mi Gobierno: what ChileAtiende sent this person and how they answered.
    Says nothing when AWS is unavailable; that warning is for the officer only."""
    ok, _ = status()
    if not ok:
        return
    try:
        contacts = _person_contacts(run)
    except Exception:  # noqa: BLE001
        log.warning("No se pudieron leer los contactos AWS de %s", run, exc_info=True)
        return
    if st.session_state.pop("aws_answer_error", False):
        st.warning("No pudimos registrar tu respuesta. Inténtalo de nuevo en unos minutos.")
    for c in contacts:
        channels = []
        if c.get("email_enviado"):
            channels.append(f"un email el {_when(c.get('email_enviado_en', ''))}")
        if c.get("sms_enviado"):
            channels.append("un SMS")
        sent = " y ".join(channels) or "un aviso"
        with st.container(border=True, key=f"gov_aws_{c['beneficio_id'].replace(':', '_')}"):
            st.markdown(f"**{c['titulo']}**")
            st.caption(f"ChileAtiende te envió {sent}.")
            if c.get("por_que"):
                st.write(c["por_que"])
            if c.get("estado") == "aceptado":
                st.success(f"Aceptaste la orientación el {_when(c.get('respuesta_en', ''))}.")
                if c.get("paso_siguiente"):
                    st.write(f"**Tu próximo paso:** {c['paso_siguiente']}")
            elif c.get("estado") == "rechazado":
                st.info("Nos dijiste que no te interesa. No volveremos a escribirte por esto.")
            else:
                yes, no, _ = st.columns([1.3, 1, 2])
                key = c["beneficio_id"].replace(":", "_")
                yes.button(
                    "Quiero orientación",
                    type="primary",
                    key=f"gov_aws_yes_{key}",
                    on_click=_answer,
                    args=(run, c["beneficio_id"], "acepto"),
                )
                no.button(
                    "No me interesa",
                    key=f"gov_aws_no_{key}",
                    on_click=_answer,
                    args=(run, c["beneficio_id"], "rechazo"),
                )


@st.cache_data(ttl=60, show_spinner=False)
def status() -> tuple[bool, str]:
    """Cached so pages that only show a section do not call AWS on every rerun."""
    return aws.check()


@st.cache_data(ttl=20, show_spinner=False)
def _history(run: str) -> list[dict]:
    return aws.load_history(run)


def _flag(value) -> str:
    return YES if value else ""


def _email_cell(c: dict) -> str:
    if not c.get("email_enviado"):
        return ""
    return "Simulado" if c.get("email_simulado") else "✓ Real"


def render(diags=None) -> None:
    st.header("Contactos proactivos (AWS)")
    st.caption(
        "Lo que la detección automática en AWS encontró y contactó: cuando cambia un dato de una "
        "persona, el sistema revisa si podría recibir un beneficio, le envía un email y, si no "
        "responde, sigue por SMS y equipo en terreno. Abrir el email no detiene el contacto; "
        "responder sí. Datos sintéticos; los resultados son aparentes y el IPS resuelve."
    )
    ok, message = status()
    if not ok:
        st.warning(
            f"{message} Esta vista lee DynamoDB con el perfil `hackaton` (ver `infra/README.md`)."
        )
        return
    if st.button("Actualizar ahora", key="aws_refresh"):
        status.clear()
        _clear()
    _event_simulator()
    contacts = _contacts()
    if not contacts:
        st.info("Todavía no hay contactos. Cargue datos con `scripts/proactivo.py cargar`.")
        return

    s = aws.summary(contacts)
    row = st.columns(4)
    row[0].metric("Personas detectadas", s["personas"], help=f"{s['contactos']} contactos")
    row[1].metric("Emails reales enviados", s["emails_reales"], help="Solo casillas verificadas")
    row[2].metric("Emails simulados", s["emails_simulados"], help="Casillas @example.com")
    row[3].metric("Abrieron / entraron", f"{s['abiertos']} / {s['entraron']}")
    row = st.columns(4)
    row[0].metric("SMS (simulados)", s["sms"])
    row[1].metric("En terreno", s["terreno"], help="Sin respuesta por canales remotos")
    row[2].metric("Aceptaron", s["aceptan"])
    row[3].metric("Rechazaron", s["rechazan"])

    left, right = st.columns(2)
    with left:
        st.markdown("**En qué etapa está cada contacto**")
        st.bar_chart(pd.Series(s["por_estado"]).sort_values(), horizontal=True)
    with right:
        st.markdown("**Por beneficio**")
        st.bar_chart(pd.Series(s["por_beneficio"]).sort_values(), horizontal=True)

    st.subheader("Contactos")
    f1, f2, f3 = st.columns([2, 2, 1])
    states = f1.multiselect("Estado", sorted(s["por_estado"]), key="aws_states")
    benefits = f2.multiselect("Beneficio", sorted(s["por_beneficio"]), key="aws_benefits")
    only_real = f3.toggle("Solo emails reales", key="aws_real")
    rows = [
        c
        for c in contacts
        if (not states or c["estado_texto"] in states)
        and (not benefits or c.get("beneficio") in benefits)
        and (not only_real or (c.get("email_enviado") and not c.get("email_simulado")))
    ]
    table = pd.DataFrame(
        [
            {
                "RUN": c["run"],
                "Nombre": c["nombre"],
                "Beneficio": c.get("beneficio", ""),
                "Tipo": c["tipo_texto"],
                "Estado": c["estado_texto"],
                "Email": _email_cell(c),
                "Abrió": _flag(c.get("email_abierto")),
                "Entró": _flag(c.get("email_click") or c.get("sms_click")),
                "SMS": _flag(c.get("sms_enviado")),
                "Terreno": _flag(c.get("terreno")),
                "Respuesta": c.get("respuesta", ""),
                "Detectado": c.get("detectado_en", "")[:16].replace("T", " "),
            }
            for c in rows
        ]
    )
    st.dataframe(table, hide_index=True, use_container_width=True, height=320)
    st.caption(f"{len(rows)} de {len(contacts)} contactos. Horas en UTC.")

    st.subheader("Detalle de una persona")
    people = {f"{c['run']} · {c['nombre']}": c["run"] for c in rows}
    if not people:
        return
    run = people[st.selectbox("Persona", list(people), key="aws_person")]
    render_person(run, [c for c in contacts if c["run"] == run])


def _age(person: dict) -> str:
    try:
        born = datetime.fromisoformat(person["fecha_nacimiento"]).date()
    except (KeyError, TypeError, ValueError):
        return ""
    today = aws.today_chile()
    years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return f"{years} años"


def _wait_for_detection(run: str, before: set[tuple], seconds: int = 20) -> list[dict]:
    """The detector Lambda runs from the table stream; poll until it writes."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        time.sleep(2)
        now = aws.contacts_for(run)
        if {(c["beneficio_id"], c.get("estado"), c.get("etapa")) for c in now} != before:
            return now
    return []


def _event_simulator() -> None:
    """Change a person's data in ca-personas, as the CLI `evento` does.
    Detection and the email happen in the Lambdas, not here."""
    with st.expander("Simular evento de vida", expanded=False):
        st.caption(
            "Cambia un dato de la persona en `ca-personas`. El stream de DynamoDB dispara la "
            "Lambda de detección, que envía el email real a las casillas verificadas. "
            "Demo estrella: Jorge Demo (90000002-2) cumple 65 años."
        )
        people = {f"{p['run']} · {p.get('nombre', '')} · {_age(p)}": p["run"] for p in _people()}
        with st.form("aws_event_form"):
            run = people[st.selectbox("Persona", list(people), key="aws_event_person")]
            a, b, c = st.columns(3)
            years = a.number_input("Edad (años)", 0, 120, value=None, placeholder="Sin cambio")
            months = b.number_input("y meses", 0, 11, value=0)
            children = c.number_input("Hijos", 0, 15, value=None, placeholder="Sin cambio")
            a, b, c = st.columns(3)
            marital = a.selectbox("Estado civil", list(MARITAL))
            bracket = b.number_input("Tramo RSH (%)", 0, 100, value=None, placeholder="Sin cambio")
            abroad = c.number_input(
                "Días fuera de Chile (último año)", 0, 366, value=None, placeholder="Sin cambio"
            )
            accident = st.checkbox("Sufrió un accidente laboral")
            submitted = st.form_submit_button("Aplicar evento", type="primary")
        if submitted:
            values = aws.event_values(
                age=(int(years), int(months)) if years is not None else None,
                children=None if children is None else int(children),
                marital_status=MARITAL[marital],
                accident=accident,
                rsh_bracket=None if bracket is None else int(bracket),
                days_abroad=None if abroad is None else int(abroad),
            )
            if not values:
                st.warning("Indique al menos un cambio.")
            else:
                before = {
                    (c["beneficio_id"], c.get("estado"), c.get("etapa"))
                    for c in aws.contacts_for(run)
                }
                aws.apply_event(run, values)
                _people.clear()
                with st.spinner("Esperando a la Lambda de detección…"):
                    found = _wait_for_detection(run, before)
                _clear()
                if found:
                    st.success(
                        f"Detección lista: {len(found)} contacto(s) para {run}. "
                        "Revise el detalle abajo y la casilla de correo."
                    )
                else:
                    st.info(
                        "Dato actualizado. La Lambda no abrió contactos nuevos: puede que el "
                        "cambio no habilite beneficios o que ya estuvieran abiertos."
                    )
        if st.button("Reiniciar contactos de esta persona", key="aws_event_reset"):
            run = people[st.session_state["aws_event_person"]]
            n_contacts, n_events = aws.reset_person(run)
            _clear()
            st.success(f"{run}: {n_contacts} contactos y {n_events} eventos borrados.")


def render_person(run: str, contacts: list[dict] | None = None) -> None:
    """Contacts and history of one RUN; also used inside the beneficiary record."""
    if contacts is None:
        contacts = [c for c in _contacts() if c["run"] == run]
    if not contacts:
        st.caption("La detección en AWS no ha contactado a esta persona.")
        return
    for c in contacts:
        with st.container(border=True):
            st.markdown(f"**{c.get('beneficio', '')}** · {c['tipo_texto']} · {c['estado_texto']}")
            channels = [
                f"Email: {_email_cell(c) or 'no enviado'}",
                f"abrió: {'sí' if c.get('email_abierto') else 'no'}",
                f"entró: {'sí' if c.get('email_click') or c.get('sms_click') else 'no'}",
                f"SMS: {'sí' if c.get('sms_enviado') else 'no'}",
                f"terreno: {'sí' if c.get('terreno') else 'no'}",
                f"respuesta: {c.get('respuesta', '')}",
            ]
            st.caption(" · ".join(channels))
            if c.get("motivo_persona") or c.get("motivo"):
                st.write(c.get("motivo_persona") or c.get("motivo"))
            if c.get("faltantes"):
                st.warning("Le falta: " + "; ".join(c["faltantes"]))
            if c.get("paso_siguiente"):
                st.success(f"Próximo paso: {c['paso_siguiente']}")
    events = _history(run)
    if events:
        st.markdown("**Historial**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Fecha (UTC)": e["fecha"],
                        "Beneficio": e.get("beneficio_id", "").split(":")[0],
                        "Evento": e["evento_texto"],
                        "Canal": e.get("canal", ""),
                        "Detalle": e.get("detalle", {}).get("asunto")
                        or e.get("detalle", {}).get("motivo", ""),
                    }
                    for e in events
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
