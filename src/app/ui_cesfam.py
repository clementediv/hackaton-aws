"""Simulated CESFAM front desk and the officer's referral inbox.

The CESFAM only sees whether to refer the person to ChileAtiende; the case
summary goes to the officer. Design: 20-arquitectura/cesfam-derivacion.md.
"""

import streamlit as st
import ui_aws
from ruta import derivaciones
from ruta.datos import cargar_perfiles
from ruta.demo_auth import normalize_run
from ruta.ficha import build

ORIGIN = "CESFAM"


def _case(run: str, diags) -> tuple[str | None, list[dict]]:
    """(internal reason for a maximum alert, summary for the officer)."""
    contacts = ui_aws.person_contacts(run)
    ficha = build(diags[run], cargar_perfiles()[run]) if run in diags else None
    reason = derivaciones.max_alert(ficha.alert if ficha else None, contacts)
    return reason, derivaciones.summarize(ficha, contacts, reason or "")


def _examples(diags) -> list[str]:
    runs = derivaciones.funnel_max_runs() + ui_aws.field_runs()
    return [r for r in dict.fromkeys(runs) if r in diags and diags[r].vivo][:5]


def render(diags) -> None:
    st.header("Punto de atención CESFAM")
    st.caption(
        "Simulación de lo que ve un funcionario de un CESFAM al registrar una atención. "
        "Solo indica si debe derivar a ChileAtiende: no muestra beneficios, montos ni motivos. "
        "La base legal de esta alerta está por validar."
    )
    typed = st.text_input(
        "RUN de la persona que se atiende", key="cesfam_run", placeholder="12.345.678-5"
    )
    if done := st.session_state.pop("cesfam_done", None):
        st.success(done)
    if not typed.strip():
        if examples := _examples(diags):
            st.caption("Para la demo, personas con alerta máxima: " + " · ".join(examples))
        return
    try:
        run = normalize_run(typed)
    except ValueError as error:
        st.error(str(error))
        return
    reason, summary = _case(run, diags)
    if not reason:
        st.success("Sin avisos de ChileAtiende para esta persona.")
        return
    with st.container(border=True, key="cesfam_alert"):
        st.markdown("### 🔔 Derivar a ChileAtiende")
        st.write(
            "Esta persona tiene un aviso pendiente de ChileAtiende. Invítela a llamar al 101 "
            "o a acercarse a una sucursal, o derive el caso para que un ejecutivo la contacte."
        )
        if any(r["status"] == derivaciones.PENDING for r in derivaciones.for_run(run)):
            st.info("Caso ya derivado: un ejecutivo de ChileAtiende lo tiene pendiente.")
        elif st.button("Derivar a ChileAtiende", type="primary", key="cesfam_refer"):
            derivaciones.refer(run, ORIGIN, reason, summary)
            st.session_state["cesfam_done"] = "Caso derivado. Un ejecutivo lo verá con su resumen."
            st.rerun()


def _summary(rows: list[dict]) -> None:
    st.markdown("\n".join(f"- **{r['label']}:** {r['value']}" for r in rows))


def render_inbox(officer: str, channel: str) -> str | None:
    """Pending referrals in «Atención del caso»; returns the RUN the officer chose."""
    items = derivaciones.pending()
    if not items:
        return None
    chosen = None
    with st.expander(f"📥 Derivaciones pendientes ({len(items)})", expanded=True):
        for r in items:
            with st.container(border=True):
                when = r["created_at"][:16].replace("T", " ")
                st.markdown(f"**RUN {r['run']}** · desde {r['origin']} · {when}")
                _summary(r["summary"])
                if st.button("Atender", key=f"attend_referral_{r['id']}"):
                    chosen = derivaciones.attend(r["id"], officer, channel)
    return chosen


def render_case_referral(run: str) -> None:
    """Latest referral of the person being attended, with its frozen summary."""
    items = derivaciones.for_run(run)
    if not items:
        return
    r = items[0]
    state = (
        f"atendida por {r['attended_by']}" if r["status"] == derivaciones.ATTENDED else "pendiente"
    )
    with st.expander(
        f"Derivado desde {r['origin']} el {r['created_at'][:10]} · {state}", expanded=False
    ):
        _summary(r["summary"])
