"""Visual post-alert journey and repeat use for social workers."""

from html import escape
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from ruta import engagement, trazabilidad

STAGES = [
    ("Alerta registrada", "Personas únicas de la campaña"),
    ("Ingresó al sistema", "Acceso identificado después de la alerta"),
    ("Aceptó condiciones", "Autorización registrada después de ingresar"),
    ("Avanzó en un trámite", "Paso declarado de un beneficio disponible"),
]


def duration(hours):
    if hours is None:
        return "Sin registro"
    if hours < 1:
        return f"{round(hours * 60)} min"
    if hours < 48:
        return f"{hours:g} h"
    return f"{hours / 24:.1f} días"


def date_label(value):
    if value is None:
        return "Aún sin registro"
    return (
        value.replace(tzinfo=ZoneInfo("UTC"))
        .astimezone(ZoneInfo("America/Santiago"))
        .strftime("%d/%m · %H:%M")
    )


def render(state, db_file, *, demo=False, profiles=None):
    if demo:
        engagement.seed_demo(db_file, state, profiles)
    events = trazabilidad.load_events(db_file)
    data = engagement.report(state["people"], events, state["clock"]["now"] if demo else None)
    rows, counts = data["people"], data["counts"]
    st.markdown("### De la alerta al próximo paso")
    st.caption(
        "Escenario de uso simulado · No son resultados de personas reales."
        if demo
        else "Actividad registrada en Mi Gobierno para esta campaña."
    )
    total = counts[0]
    st.html(
        '<div class="trace-journey">'
        + "".join(
            f'<div class="trace-stage"><span class="trace-index">{index + 1}</span>'
            f'<h4>{label}</h4><div class="trace-count">{count}</div>'
            f'<div class="trace-bar"><span style="width:{100 * count / total if total else 0}%">'
            "</span></div>"
            f"<b>{round(100 * count / total) if total else 0}% de las alertadas</b>"
            f"<p>{description}</p></div>"
            for index, ((label, description), count) in enumerate(zip(STAGES, counts, strict=True))
        )
        + "</div>"
    )
    st.caption(
        "Mirar el proceso no cuenta como realizar un trámite. El avance es declarado, "
        "no una resolución del organismo. La meta ≥75% en plazo sigue pendiente de validación."
    )
    entered = counts[1]
    metrics = [
        (
            "Volvieron a ingresar",
            str(data["returning"]),
            f"De {entered} personas que ingresaron",
            "",
        ),
        (
            "Tiempo entre accesos",
            duration(data["median_return_hours"]),
            "Mediana del último intervalo por persona",
            "",
        ),
        ("Consultas al proceso", str(data["views"]), "Vistas registradas al abrir o volver", ""),
        (
            "Sin volver hace 7+ días",
            str(
                sum(
                    row["away_days"] >= 7
                    for row in rows
                    if row["away_days"] is not None and row["status"] != "declined"
                )
            ),
            "Revisar si necesitan acompañamiento",
            "amber",
        ),
    ]
    st.markdown("### ¿Siguen usando la plataforma?")
    st.html(
        '<div class="staff-stats">'
        + "".join(
            f'<div class="staff-stat {tone}"><div class="label">{label}</div>'
            f'<div class="number">{escape(value)}</div><div class="note">{note}</div></div>'
            for label, value, note, tone in metrics
        )
        + "</div>"
    )
    chart, retention = st.columns([2.2, 1], gap="large")
    with chart:
        st.markdown("#### Personas que ingresaron · últimos 14 días")
        st.bar_chart(pd.DataFrame(data["daily"]).set_index("Día"), color="#0f69b4", height=230)
    with retention:
        st.markdown("#### Volvieron durante los primeros…")
        for item in data["retention"]:
            text = f"{item['percent']}%" if item["percent"] is not None else "Por observar"
            st.html(
                '<div class="trace-retention">'
                f"<strong>{item['days']} días</strong><b>{text}</b>"
                f"<small>{item['returned']} de {item['eligible']} personas con "
                "ese período completo de seguimiento</small></div>"
            )
    st.caption(
        "Cada ingreso corresponde a una sesión identificada; las recargas no suman sesiones. "
        "El intervalo se mide entre ingresos, no como tiempo de lectura. "
        "Las ventanas de 7 y 30 días excluyen a quienes aún no tienen suficiente seguimiento."
    )
    if not rows:
        st.info("Aún no hay alertas con fecha para construir el recorrido.")
        return
    st.markdown("### El recorrido de una persona")
    options = {
        row["run"]: f"{row['name']} · {row['run']}"
        for row in sorted(
            rows, key=lambda row: (row["progress"] is None, row["sessions"] < 2, row["name"])
        )
    }
    selected = st.selectbox(
        "Persona", list(options), format_func=options.get, key="staff_trace_person"
    )
    person = next(row for row in rows if row["run"] == selected)
    st.html(
        '<div class="trace-person">'
        + "".join(
            f'<div class="trace-milestone {"done" if person[field] else "waiting"}">'
            f"<span>{'✓' if person[field] else '○'}</span><div><b>{label}</b>"
            f"<small>{date_label(person[field])}</small></div></div>"
            for (label, _), field in zip(
                STAGES, ("alert", "entered", "consent", "progress"), strict=True
            )
        )
        + "</div>"
    )
    columns = st.columns(3)
    columns[0].metric("Sesiones", person["sessions"])
    columns[1].metric("Último acceso", date_label(person["last_login"]))
    columns[2].metric("Última consulta al proceso", date_label(person["last_view"]))
    if person["sessions"] > 1:
        st.info(f"Volvió después de {duration(person['return_hours'])} entre sus últimos accesos.")
    elif person["entered"]:
        st.info("Ingresó una vez; aún no se registra una reconexión.")
    else:
        st.info("Aún no se registra su ingreso después de la alerta.")
    visits = person["logins"]
    if visits:
        st.html(
            '<div class="trace-visits">'
            + "".join(
                f"<div><span>{index + 1}</span>"
                f"<b>{'Primer ingreso' if index == 0 else 'Volvió'}</b>"
                f"<small>{date_label(at)}</small></div>"
                for index, at in enumerate(visits)
            )
            + "</div>"
        )
    with st.expander("Continuidad por persona y detalle del registro"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Persona": row["name"],
                        "Ingresos": row["sessions"],
                        "Último acceso": date_label(row["last_login"]),
                        "Consultas al proceso": row["views"],
                        "Días sin ingresar": row["away_days"],
                        "Avance declarado": "Sí" if row["progress"] else "Sin registro",
                    }
                    for row in sorted(rows, key=lambda r: (-(r["away_days"] or 0), r["name"]))
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
        extra = []
        if st.checkbox("Incluir historial de contacto AWS", key="staff_trace_aws"):
            import ui_aws
            from ruta import aws_contactos

            available, message = ui_aws.status()
            if available:
                extra = trazabilidad.aws_events(aws_contactos.load_history(selected))
            else:
                st.caption(message)
        audit = trazabilidad.timeline(selected, events, extra)
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Fecha": event["fecha"],
                        "Canal": event["canal"],
                        "Qué ocurrió": event["evento"],
                        "Detalle": event["detalle"],
                        "Origen": event["origen"],
                    }
                    for event in audit
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.download_button(
            "Descargar registro de auditoría (CSV)",
            trazabilidad.audit_csv(events),
            file_name="trazabilidad-casos.csv",
            mime="text/csv",
            key="staff_trace_csv",
        )
