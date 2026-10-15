"""Visual test harness for the same persistent backend used by the CLI."""

import json
import os
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
from ruta.colador import ACTIVE, CONTACTED, STAGES, Funnel
from ruta.contacto import generate_contacts
from ui_campanas import render_campaigns

STATUS_LABELS = {
    "active": "Sin contacto confirmado",
    "contacted": "Contactado · pendiente de trámite",
    "started": "Trámite iniciado",
    "declined": "Declinó",
}
EVENT_LABELS = {
    "signal": "Nueva alerta agregada al caso",
    "entered": "Entró a la etapa",
    "skipped": "Canal no disponible: se salta",
    "attempt": "Intento simulado",
    "queued": "Pendiente de campaña presencial",
    "started": "Inició trámite",
    "contacted": "Contacto confirmado: se detiene el escalamiento",
    "declined": "Declinó: se detiene",
    "opened": "Abrió correo (sin inicio)",
    "answered": "Respondió al contacto",
}


LAB_SCENARIOS = {
    "Sin respuestas · mapa de campañas": "funnel-demo-rm.db",
    "Embudo con respuestas": "funnel-demo-contacto-ejemplo.db",
}


def render_campaign_lab(profiles):
    """Scenario picker over separate demo databases; shared by the lab and the app tab."""
    override = os.getenv("FUNNEL_DEMO_DB")
    filename = LAB_SCENARIOS["Embudo con respuestas"]
    if not override:
        scenario = st.selectbox(
            "Ejemplo precargado",
            list(LAB_SCENARIOS),
            key="lab_scenario",
            on_change=lambda: st.session_state.pop("funnel_demo_path", None),
        )
        filename = LAB_SCENARIOS[scenario]
        if scenario.startswith("Sin respuestas"):
            st.info(
                "Este ejemplo omite respuestas para mostrar el mapa: "
                "los pendientes no son contactos efectivos."
            )
    default_path = Path(override or Path(__file__).resolve().parent / filename)
    if st.button("Nueva simulación (conservar la anterior)", key="lab_new_simulation"):
        st.session_state["funnel_demo_path"] = str(
            default_path.with_name(f"funnel-demo-{uuid4().hex[:8]}.db")
        )
        st.rerun()
    render_funnel(profiles, st.session_state.get("funnel_demo_path", default_path))


def render_funnel(profiles, db_path=None):
    engine = Funnel(db_path)
    state = engine.snapshot()
    st.markdown("## Embudo de contacto")
    st.info(
        "SIMULACIÓN · No se envían correos, no se realizan llamadas ni visitas. "
        "Contactos, respuestas y plazos son datos de demostración."
    )
    st.caption(
        "Fuente: contacto-y-campanas.md · Email → llamada → trabajo → presencial. "
        "Responder o aceptar detiene los siguientes canales; "
        "iniciar el trámite se registra aparte. "
        "Enviar o abrir un correo no confirma respuesta. Declinar detiene todo."
    )
    controls = st.columns([2, 1])
    mode = controls[0].radio(
        "Comportamiento de las respuestas",
        ["Respuestas simuladas", "Sin respuestas"],
        horizontal=True,
    )
    seed = controls[1].number_input(
        "Semilla de la campaña", value=20261008, min_value=0, disabled=state["clock"] is not None
    )
    simulate = mode == "Respuestas simuladas"
    if not state["clock"]:
        st.caption(
            "La detección reutiliza reglas.py sobre 500 perfiles. "
            "Escenario territorial: comunas de la Región Metropolitana, asignadas sintéticamente."
        )
        if st.button("Inicializar embudo", type="primary"):
            engine.initialize(
                profiles,
                generate_contacts(profiles, int(seed), territory="metropolitana"),
                seed=int(seed),
                simulate=simulate,
            )
            st.rerun()
        return

    st.success(
        f"Reloj simulado: {state['clock']['now'].replace('T', ' ')} · "
        f"Semilla {state['clock']['seed']}"
    )
    for col, days in zip(st.columns(4), [1, 5, 7, 19], strict=True):
        if col.button(f"Avanzar {days} {'día' if days == 1 else 'días'}", use_container_width=True):
            engine.advance(days, simulate=simulate)
            st.rerun()
    st.caption(
        "Política demo: email 7 días; llamadas en días 0, 2 y 5; trabajo 7 días. "
        "Presencial queda en cola para planificar una campaña."
    )

    totals = state["totals"]
    metrics = (
        "Detectadas",
        "Contacto confirmado",
        "Iniciaron trámite",
        "Declinaron",
        "Sin contacto",
        "En presencial",
    )
    keys = ("detected", "confirmed_contacts", "started", "declined", "active", "in_person")
    for col, label, key in zip(st.columns(6), metrics, keys, strict=True):
        col.metric(label, totals[key])
    st.caption(
        f"{len(profiles)} perfiles analizados → {totals['detected']} personas detectadas. "
        f"Distribución actual: {totals['active']} sin contacto + "
        f"{totals['contacted']} contactadas sin "
        f"inicio + {totals['started']} iniciaron + {totals['declined']} declinaron. "
        "Contacto confirmado incluye respuestas, aceptaciones y rechazos; "
        "no equivale a trámite iniciado."
    )
    denominator = totals["detected"]
    started_pct = 100 * totals["started"] / denominator if denominator else 0
    st.markdown("#### Avance del trámite · meta ≥75%")
    kpi = st.columns(2)
    kpi[0].metric("Inicios sobre detectadas (proxy)", f"{started_pct:.1f}%")
    kpi[1].metric(
        "Próximo paso válido dentro del plazo", "Sin medir", "Meta ≥75%", delta_color="off"
    )
    st.caption(
        "El inicio es solo un indicador auxiliar. Falta instrumentar la evidencia del próximo "
        "paso válido y su plazo; contacto o cambio de canal no cuentan para cumplir esa meta."
    )

    st.markdown("### Del contacto general al acompañamiento presencial")
    import altair as alt

    data = pd.DataFrame(state["funnel"])
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=6)
        .encode(
            x=alt.X("attempted:Q", title="Personas distintas con intento en cada canal"),
            y=alt.Y("label:N", sort=list(STAGES.values()), title=None),
            color=alt.Color(
                "label:N",
                legend=None,
                scale=alt.Scale(
                    domain=list(STAGES.values()), range=["#0f69b4", "#408fc9", "#78b2d9", "#eb9847"]
                ),
            ),
            tooltip=[
                alt.Tooltip("label:N", title="Etapa"),
                alt.Tooltip("attempted:Q", title="Personas con intento"),
                alt.Tooltip("attempts:Q", title="Intentos simulados"),
                alt.Tooltip("confirmed:Q", title="Contactos confirmados"),
                alt.Tooltip("active:Q", title="Siguen en esta etapa"),
            ],
        )
    )
    st.altair_chart(chart.properties(height=240), use_container_width=True)
    st.caption(
        "Personas ≠ intentos: una persona puede tener hasta tres llamadas. Llegar a una etapa "
        "o saltarla por falta de datos no significa haber sido contactada. Presencial es una "
        "cola de campaña; todavía no simula visitas."
    )
    st.dataframe(
        data.rename(
            columns={
                "label": "Etapa",
                "reached": "Pasaron por la etapa (incluye saltos)",
                "attempts": "Intentos simulados",
                "attempted": "Personas con intento",
                "skipped": "Sin datos: canal saltado",
                "confirmed": "Contactos confirmados",
                "active": "Pendientes actuales",
            }
        ).drop(columns="stage"),
        hide_index=True,
        use_container_width=True,
    )

    render_campaigns(state, profiles)

    st.markdown("### Personas y próximo contacto")
    rows = [
        {
            "RUN": person["run"],
            "Nombre": person["name"],
            "Edad": person["age"],
            "Etapa": person["stage_label"],
            "Estado": STATUS_LABELS[person["status"]],
            "Provincia simulada": person["contact"]["province"],
            "Próximo contacto": person["next_at"] or "—",
        }
        for person in state["people"]
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, height=260)

    if not state["people"]:
        return
    selected = st.selectbox("Inspeccionar persona", [person["run"] for person in state["people"]])
    person = next(person for person in state["people"] if person["run"] == selected)
    st.caption(f"{person['name']} · {person['stage_label']} · {STATUS_LABELS[person['status']]}")
    if person["contact"].get("location_source") == "synthetic-address-v1":
        contact = person["contact"]
        st.caption(
            f"Dirección ficticia: {contact['address']} · "
            f"Coordenadas simuladas: {contact['latitude']:.6f}, {contact['longitude']:.6f}"
        )
    actions = st.columns(4)
    responses = ("opened", "answered", "started", "declined")
    for col, label, response in zip(
        actions,
        ["Abrió el correo", "Confirmar contacto", "Inició su trámite", "Declinar"],
        responses,
        strict=True,
    ):
        disabled = person["status"] not in {ACTIVE, CONTACTED}
        if response in {"opened", "answered"}:
            disabled = person["status"] != ACTIVE or (response == "opened" and person["stage"] != 1)
        if col.button(label, disabled=disabled, use_container_width=True):
            engine.respond(selected, response)
            st.rerun()

    history = [
        {
            "Fecha simulada": event["at"],
            "Etapa": STAGES[event["stage"]],
            "Evento": EVENT_LABELS[event["kind"]],
            "Detalle": event["detail"].get("reason") or event["detail"].get("message", ""),
        }
        for event in state["events"]
        if event["run"] == selected
    ]
    st.dataframe(pd.DataFrame(history), hide_index=True, use_container_width=True)
    with st.expander("Ver snapshot del backend"):
        st.json(
            {"clock": state["clock"], "totals": totals, "funnel": state["funnel"], "person": person}
        )
    st.download_button(
        "Descargar estado completo (JSON sintético)",
        data=json.dumps(state, ensure_ascii=False, indent=2),
        file_name="embudo-simulado.json",
        mime="application/json",
    )
