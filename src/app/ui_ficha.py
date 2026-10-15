"""Ficha del beneficiario: everything known about one person, in one page.

For officers and social workers. Reads the same sources as every other view
(rules, cases, Mi Gobierno, funnel); it never writes.
"""

import pandas as pd
import streamlit as st
from ruta import reglas as rules
from ruta.datos import cargar_perfiles
from ruta.fechas import fmt
from ruta.ficha import build

STEP_LABELS = {
    "completado": "✅ Completado",
    "disponible": "👉 Disponible",
    "bloqueado": "🔒 Requiere el paso anterior",
    "en_espera": "📅 Desde la fecha indicada",
}
REQUIREMENT_ICONS = {
    rules.CUMPLE: "✅",
    rules.NO_CUMPLE: "❌",
    rules.FALTA: "⚠️",
    rules.PENDIENTE: "⏳",
}
INVITATION_LABELS = {
    "no_invitado": "No invitada",
    "invitado": "Invitada, sin respuesta",
    "aceptado": "Aceptó el acompañamiento",
    "rechazado": "Declinó",
}
FUNNEL_STATUS = {
    "active": "Sin contacto confirmado",
    "contacted": "Contactada · pendiente de trámite",
    "started": "Inició el trámite",
    "declined": "Declinó",
}


def _choose(diags) -> str:
    alive = sorted(
        (d for d in diags.values() if d.vivo), key=lambda d: (not d.invitar, -d.hitos.edad)
    )
    options = {f"{d.run} · {d.nombre} · {d.hitos.edad} años": d.run for d in alive}
    return options[st.selectbox("Beneficiario", list(options), key="ficha_person")]


def render(diags) -> None:
    st.header("Ficha del beneficiario")
    st.caption(
        "Todo lo que se sabe de una persona en una sola página, para ejecutivos y trabajadores "
        "sociales: identidad, contacto, consentimiento, evaluación, ruta, documentos y colador. "
        "Datos sintéticos de demostración; el organismo valida y resuelve."
    )
    run = _choose(diags)
    f = build(diags[run], cargar_perfiles()[run])

    if f.alert["level"] == 4:
        st.error(f"🚨 ALERTA DE BENEFICIO · {f.alert['label']}")
    elif f.alert["level"]:
        st.warning(f"Alerta de beneficio · {f.alert['label']}")

    left, right = st.columns(2)
    with left.container(border=True):
        st.markdown("**Identidad** · Registro Civil (dataset A)")
        i = f.identity
        st.write(f"**{i['name']}** · RUN {i['formatted_run']}")
        st.write(f"Nacimiento {i['birth_date']} · {i['age']} años · Sexo {i['sex']}")
        st.caption(f"Segmento de campaña: {i['segment']}")
    with right.container(border=True):
        st.markdown(f"**Contacto** · {f.contact_source}")
        c, missing = f.contact, "Sin información"
        st.write(f"📧 {c.email or missing}")
        st.write(f"📞 {c.phone or missing}")
        st.write(f"🏢 {c.employer or missing}")
        st.write(f"📍 {c.address or missing} · {c.commune}, {c.province}, {c.region}")
        st.caption(
            "Ficticio: dominio example.com y teléfonos con bloque 0000. No se contacta a nadie."
        )

    with st.container(border=True):
        st.markdown("**Consentimiento**")
        case = f.case
        st.write(
            f"Invitación: {INVITATION_LABELS.get(case['invitation'], case['invitation'])}"
            + (f" · canal {case['invitation_channel']}" if case["invitation_channel"] else "")
        )
        st.write(
            "Autorización para consultar antecedentes: "
            + (f"✅ otorgada ({case['authorized_at']})" if case["authorized"] else "❌ no otorgada")
        )

    with st.container(border=True):
        st.markdown("**Evaluación** · orientación preliminar, no adjudicación")
        p = f.pgu
        st.write(f"PGU: **{p['result']}** — {p['reason']}")
        if p["estimated_amount"] and p["result"] in (rules.ELEGIBLE, rules.PROXIMO):
            st.write(f"Monto orientativo: ${p['estimated_amount']:,.0f}".replace(",", "."))
        st.write(f"Jubilación: **{f.retirement['result']}** — {f.retirement['reason']}")
        with st.expander("Requisitos PGU y fuentes"):
            for req in p["requirements"]:
                icon = REQUIREMENT_ICONS.get(req["estado"], "•")
                st.write(f"{icon} **{req['nombre']}** — {req['detalle']}")
                st.caption(req["fuente"])

    with st.container(border=True):
        st.markdown("**Ruta del trámite**")
        if f.next_step:
            st.info(f"Próximo paso: **{f.next_step['titulo']}** — {f.next_step['donde']}")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Trámite": s["tramite"],
                        "Paso": s["titulo"],
                        "Estado": STEP_LABELS.get(s["state"], s["state"]),
                        "Desde": fmt(s["disponible_desde"]),
                    }
                    for s in f.route
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )

    with st.container(border=True):
        st.markdown("**Documentos y declaración** · Mi Gobierno")
        if f.documents is None:
            st.caption("Requiere la autorización de la persona.")
        else:
            if f.documents:
                for doc in f.documents:
                    st.write(f"📎 {doc['kind']}: {doc['name']} ({doc['size'] // 1024} KB)")
            else:
                st.write("Sin documentos adjuntos.")
            if f.declaration:
                st.write("Declaración: " + ", ".join(f"{k}: {v}" for k, v in f.declaration.items()))
            st.caption("Un archivo adjunto no está validado ni cambia la elegibilidad.")

    with st.container(border=True):
        st.markdown("**Colador de contacto**")
        if f.funnel is None:
            st.caption("No forma parte de la campaña simulada actual.")
        else:
            fn = f.funnel
            st.write(
                f"Etapa {fn['stage']} · {fn['stage_label']} · "
                f"{FUNNEL_STATUS.get(fn['status'], fn['status'])} · {fn['attempts']} intentos"
            )
            st.caption(f"Motivo de la alerta: {fn['reason']}")
            if fn["events"]:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {"Fecha": e["at"][:16], "Etapa": e["stage"], "Evento": e["kind"]}
                            for e in fn["events"]
                        ]
                    ),
                    hide_index=True,
                    use_container_width=True,
                )

    with st.expander(f"Historial por canal ({len(f.events)} eventos)"):
        if f.events:
            st.dataframe(pd.DataFrame(f.events), hide_index=True, use_container_width=True)
        else:
            st.caption("Sin eventos registrados.")
