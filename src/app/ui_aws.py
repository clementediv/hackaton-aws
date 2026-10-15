"""Contactos AWS: what the proactive detection on AWS detected, sent and recorded.

Read-only view over DynamoDB (ca-contactos, ca-historial, ca-personas). The
Lambdas detect, send and escalate; this page only shows it to the officer.
"""

import pandas as pd
import streamlit as st
from ruta import aws_contactos as aws

YES = "✓"


@st.cache_data(ttl=20, show_spinner="Leyendo contactos desde AWS…")
def _contacts() -> list[dict]:
    return aws.load_contacts()


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
        _contacts.clear()
        _history.clear()
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
