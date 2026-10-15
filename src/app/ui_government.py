"""Mi Gobierno: consented personal workspace, documents and benefit journeys."""

from html import escape
from pathlib import Path

import streamlit as st
import ui_persona
from ruta import asistente, casos, config, demo_auth, government
from ruta import reglas as rules
from ruta.contacto import generate_contacts
from ruta.datos import cargar_perfiles
from ruta.fechas import fmt
from ruta.rutas import estado_pasos, generar_ruta, proximo_paso

CANAL = "Web ChileAtiende"
ASSETS = Path(__file__).resolve().parent / "assets"


def _money(value: int) -> str:
    return f"${value:,.0f}".replace(",", ".")


def _choose_person(diags):
    run = st.session_state.get("government_login_run")
    if run not in diags or not diags[run].vivo:
        return None
    d = diags[run]
    st.session_state["government_person"] = run
    with st.sidebar:
        st.markdown("### Mi Gobierno")
        st.write(d.nombre)
        st.caption("Sesión de demostración")
        st.button("Cerrar sesión", on_click=_logout, key="government_logout")
    return d


def _logout() -> None:
    for key in list(st.session_state):
        if key.startswith(("government_", "gov_", "chat-", "assistant_consent_")):
            del st.session_state[key]


def _submit_login(diags) -> None:
    password = st.session_state.pop("gov_login_password", "")
    try:
        allowed = {run for run, d in diags.items() if d.vivo}
        run = demo_auth.authenticate(st.session_state.get("gov_login_rut", ""), password, allowed)
    except ValueError as error:
        st.session_state["gov_login_error"] = str(error)
        return
    st.session_state["government_login_run"] = run
    st.session_state[f"government_view_{run}"] = "Beneficios"
    st.session_state.pop("gov_login_error", None)


def _login(diags) -> None:
    demo_people = sorted(
        (d for d in diags.values() if d.vivo),
        key=lambda d: (d.pgu.resultado != rules.ELEGIBLE, d.nombre),
    )
    sample = demo_people[0]
    sample_run = cargar_perfiles()[sample.run]["registro_civil"]["run_formateado"]
    with st.container(key="government_login"):
        intro, form = st.columns([1.15, 1], gap="large", vertical_alignment="center")
        with intro:
            st.markdown(
                '<div class="gov-login-intro"><span class="gov-eyebrow">MI GOBIERNO</span>'
                "<h1>Tus beneficios,<br>con tu información.</h1>"
                "<p>Ingresa para descubrir los apoyos que podrían corresponderte "
                "y continuar tus trámites paso a paso.</p>"
                "<ul><li>Beneficios según tu situación</li>"
                "<li>Tus documentos en un solo lugar</li>"
                "<li>Ayuda en cada paso</li></ul></div>",
                unsafe_allow_html=True,
            )
        with form, st.container(border=False, key="government_login_card"):
            st.markdown("### Ingresa a Mi Gobierno")
            st.caption("Acceso de demostración · perfiles y clave ficticios")
            with st.form("gov_login_form"):
                st.text_input(
                    "RUN", placeholder="Ej.: " + sample_run, key="gov_login_rut", max_chars=16
                )
                st.text_input(
                    "ClaveÚnica de demostración",
                    type="password",
                    placeholder="Ingresa la clave ficticia",
                    key="gov_login_password",
                    max_chars=128,
                )
                st.form_submit_button(
                    "Ingresar a Mi Gobierno",
                    type="primary",
                    use_container_width=True,
                    on_click=_submit_login,
                    args=(diags,),
                )
            if error := st.session_state.get("gov_login_error"):
                st.error(error)
            st.markdown(
                '<div class="gov-login-example"><b>Prueba el portal</b>'
                f"<span>RUN: <strong>{escape(sample_run)}</strong></span>"
                f"<span>Clave ficticia: <strong>{demo_auth.DEMO_PASSWORD}</strong></span>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.caption("Usa solo estos datos ficticios. Esta demo no está conectada a ClaveÚnica.")
    with st.expander("Probar con otro perfil ficticio"):
        selected = st.selectbox(
            "Perfil de ejemplo",
            [d.run for d in demo_people],
            format_func=lambda run: f"{diags[run].nombre} · {run}",
            key="gov_demo_example",
        )
        st.code(f"RUN: {selected}\nClave de demostración: {demo_auth.DEMO_PASSWORD}", language=None)


def render(diags) -> None:
    st.markdown(
        f"<style>{(ASSETS / 'government.css').read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )
    d = _choose_person(diags)
    if d is None:
        _login(diags)
        return
    case = casos.obtener_caso(d.run)
    profile = cargar_perfiles()[d.run]
    page = st.radio(
        "Secciones de Mi Gobierno",
        ["Beneficios", "Datos personales"],
        horizontal=True,
        label_visibility="collapsed",
        key=f"government_view_{d.run}",
    )
    if not case["autorizacion"]:
        if page == "Datos personales":
            _identity(d, profile)
            _consent(d)
        else:
            _benefits_page(d, authorized=False)
        return
    benefit = st.session_state.get(f"government_route_{d.run}")
    if page == "Datos personales":
        _personal_page(d, profile)
    elif benefit:
        _journey(d, case, benefit)
    else:
        _benefits_page(d, authorized=True)
    st.caption(
        f"Datos sintéticos · Evaluación del prototipo al {fmt(config.FECHA_REFERENCIA)}. "
        "Las recomendaciones no son una resolución ni un pago concedido."
    )


def _benefits_page(d, authorized: bool) -> None:
    benefits, chat = st.columns([2.4, 1], gap="large")
    with benefits:
        if authorized:
            _benefits(d)
        else:
            _consent(d)
    with chat:
        case = casos.obtener_caso(d.run)
        route = generar_ruta(d)
        states = estado_pasos(route, case["completados"])
        context = asistente.construir_contexto(
            d, route, states, proximo_paso(route, states), authorized
        )
        ui_persona._asistente(d, d.run, CANAL, context)


def _personal_page(d, profile) -> None:
    _identity(d, profile, authorized=True)
    with st.expander("02. Domicilio y contacto"):
        _contact_details(d, profile)
    with st.expander("03. Documentos", expanded=True):
        _documents(d)
    with st.expander("04. Información laboral"):
        _personal(d, profile)
    with st.expander("05. Previsión y salud · Acceso restringido"):
        _health_and_pension(d, profile)


def _revoke(run: str) -> None:
    if not st.session_state.get(f"gov_revoke_confirmation_{run}"):
        return
    government.delete_personal_data(run)
    casos.autorizar(run, False, CANAL)
    for key in list(st.session_state):
        if run in key and (key.startswith("gov_") or key.startswith("government_")):
            del st.session_state[key]
    st.session_state.pop(f"chat-{run}", None)


def _consent(d) -> None:
    with st.container(border=True, key="gov_consent"):
        st.markdown("### Descubre qué beneficios podrían corresponderte")
        st.write("Reúne tu información en un solo lugar y recibe una ruta según tu situación.")
        st.markdown(
            "**Con tu autorización revisaremos:** Registro Social de Hogares, residencia, "
            "previsión y pensiones. Podrás adjuntar documentos y revocar este permiso."
        )
        st.caption("Demo con datos sintéticos. No ingreses credenciales ni documentos reales.")
        accepted = st.checkbox(
            "Acepto el acompañamiento y autorizo consultar mis antecedentes",
            key=f"gov_consent_{d.run}",
        )
        st.button(
            "Activar Mi Gobierno",
            type="primary",
            disabled=not accepted,
            on_click=_activate,
            args=(d.run,),
        )


def _activate(run: str) -> None:
    casos.responder_invitacion(run, True, CANAL)
    casos.autorizar(run, True, CANAL)


def _set_revoke_confirmation(run: str, value: bool) -> None:
    st.session_state[f"gov_revoke_confirmation_{run}"] = value


def _set_route(run: str, benefit: str | None) -> None:
    if benefit:
        st.session_state[f"government_route_{run}"] = benefit
    else:
        st.session_state.pop(f"government_route_{run}", None)


@st.dialog("¿Estás seguro de que quieres revocar la autorización?")
def _confirm_revoke(run: str) -> None:
    if not st.session_state.get(f"gov_revoke_confirmation_{run}"):
        st.rerun()
    st.write(
        "Se eliminarán todos tus documentos adjuntos y la información económica que declaraste."
    )
    st.warning(
        "Si te arrepientes y vuelves a autorizar, tendrás que volver a adjuntar "
        "todos tus documentos."
    )
    st.button(
        "Cancelar y conservar mis datos",
        key=f"gov_revoke_cancel_{run}",
        use_container_width=True,
        on_click=_set_revoke_confirmation,
        args=(run, False),
    )
    st.button(
        "Sí, revocar y eliminar mis documentos",
        key=f"gov_revoke_confirm_{run}",
        type="primary",
        use_container_width=True,
        on_click=_revoke,
        args=(run,),
    )


def _permissions(run: str, authorized: bool) -> None:
    if authorized and st.button(
        "Revocar autorización",
        key=f"gov_revoke_{run}",
        use_container_width=True,
        on_click=_set_revoke_confirmation,
        args=(run, True),
    ):
        _confirm_revoke(run)


def _private_field(value: str, label: str) -> str:
    """Native accessible reveal control; masks the value visually by default."""
    return (
        '<details class="gov-private"><summary '
        f'aria-label="Mostrar u ocultar {escape(label)}" title="Mostrar u ocultar {escape(label)}">'
        '<span class="gov-private-mask">****</span>'
        f'<span class="gov-private-value">{escape(value)}</span>'
        '<svg class="gov-private-eye" viewBox="0 0 24 24" aria-hidden="true" '
        'fill="none" stroke="currentColor" stroke-width="1.6">'
        '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/>'
        '<circle cx="12" cy="12" r="3"/>'
        '<path class="gov-private-slash" d="m3 3 18 18"/></svg></summary></details>'
    )


def _identity(d, profile, authorized: bool = False) -> None:
    rc = profile["registro_civil"]
    document_number = str(rc.get("numero_documento") or "Sin información")
    personal_fields = (
        ("Fecha de nacimiento", rc["fecha_nacimiento"]),
        ("Nacionalidad", "CHILENA"),
        ("Sexo", rc["sexo"]),
        ("Estado civil", rc.get("estado_civil", "Sin información").replace("_", " ").capitalize()),
    )
    personal_html = "".join(
        f'<div class="gov-id-row"><span>{escape(label)}</span><b>{escape(value)}</b></div>'
        for label, value in personal_fields
    )
    with st.container(key="gov_identity_header"):
        heading, permissions = st.columns([4, 1.2], vertical_alignment="center")
        heading.markdown('<h2 class="gov-simple-heading">Tus datos</h2>', unsafe_allow_html=True)
        with permissions:
            _permissions(d.run, authorized)
    st.markdown(
        '<h3 class="gov-numbered-heading">01. Identidad personal</h3>', unsafe_allow_html=True
    )
    st.markdown(
        '<div class="gov-identity">'
        '<div class="gov-id-card" role="group" aria-label="Carnet ficticio con tus datos">'
        '<div class="gov-id-card-top"><div class="gov-id-document-type">CÉDULA DE<br>'
        'IDENTIDAD</div><div class="gov-id-country"><span>REPÚBLICA DE CHILE</span>'
        "<b>MI GOBIERNO · IDENTIDAD PERSONAL</b></div>"
        '<span class="gov-id-demo">DEMO</span></div>'
        '<div class="gov-id-card-body"><div class="gov-id-portrait-column">'
        '<div class="gov-id-portrait">'
        '<svg viewBox="0 0 80 100" role="img" aria-label="Silueta de demostración">'
        '<circle cx="40" cy="33" r="17" fill="currentColor"/>'
        '<path d="M8 96V84a32 32 0 0 1 64 0v12Z" fill="currentColor"/></svg>'
        "<span>IMAGEN DE EJEMPLO</span></div>"
        '<div class="gov-id-card-run"><span>RUN</span>'
        f"{_private_field(rc['run_formateado'], 'RUN')}</div></div>"
        '<div class="gov-id-fields">'
        f"<span>APELLIDOS</span><b>{escape(rc['apellido_paterno'])} "
        f"{escape(rc['apellido_materno'])}</b><span>NOMBRES</span>"
        f'<b>{escape(rc["nombres"])}</b><div class="gov-id-pair"><div>'
        "<span>NACIONALIDAD</span>"
        "<b>CHILENA</b></div>"
        f"<div><span>SEXO</span><b>{escape(rc['sexo'])}</b></div></div>"
        '<div class="gov-id-pair"><div><span>FECHA DE NACIMIENTO</span>'
        f"<b>{escape(rc['fecha_nacimiento'])}</b></div>"
        "<div><span>NÚMERO DOCUMENTO</span>"
        f"{_private_field(document_number, 'número de documento')}"
        "</div></div>"
        '<div class="gov-id-pair"><div><span>FECHA DE EMISIÓN</span>'
        f"<b>{escape(rc.get('fecha_emision') or '15 OCT 2025')}</b></div>"
        "<div><span>FECHA DE VENCIMIENTO</span>"
        f"<b>{escape(rc.get('fecha_vencimiento') or '15 OCT 2035')}</b></div></div>"
        '<div class="gov-id-signature"><span>FIRMA DEL TITULAR</span>'
        f'<b class="gov-signature-example">{escape(d.nombre.split()[0])} '
        f"{escape(rc['apellido_paterno'])}</b></div></div></div>"
        "</div>"
        '<div class="gov-identity-details">'
        f'<h3>{escape(d.nombre)}</h3><div class="gov-identity-run">RUN '
        f"{_private_field(rc['run_formateado'], 'RUN')}</div>"
        f'<div class="gov-personal-grid">{personal_html}</div></div></div>',
        unsafe_allow_html=True,
    )


def _contact_details(d, profile) -> None:
    contact = generate_contacts({d.run: profile}, territory="metropolitana")[d.run]
    rc = profile["registro_civil"]
    email = f"{d.nombre.split()[0].lower()}.{rc['apellido_paterno'].lower()}@example.com"
    fields = (
        ("Dirección", contact.address),
        ("Comuna", contact.commune),
        ("Región", contact.region),
        ("Correo electrónico", email),
        ("Teléfono", "+56 9 0000 0000"),
    )
    html = "".join(
        f'<div class="gov-id-row"><span>{escape(label)}</span><b>{escape(value)}</b></div>'
        for label, value in fields
    )
    st.markdown(
        f'<div class="gov-personal-grid gov-contact-grid">{html}</div>', unsafe_allow_html=True
    )


def _health_and_pension(d, profile) -> None:
    if not casos.obtener_caso(d.run)["autorizacion"]:
        st.info("Autoriza la consulta de antecedentes para acceder a esta sección.")
        return
    st.caption("Información personal de acceso restringido.")
    if st.toggle("Mostrar datos de previsión y salud", key=f"gov_restricted_{d.run}"):
        health, pension = st.columns(2)
        health.markdown("**Sistema de salud**")
        health.write("Sin información en el perfil")
        pension.markdown("**Afiliación previsional**")
        pension.write(
            (profile.get("prevision") or {}).get("afp") or "Sin información de afiliación"
        )


def _benefits(d) -> None:
    st.markdown(
        '<h2 class="gov-simple-heading">Beneficios que podrías cobrar</h2>',
        unsafe_allow_html=True,
    )
    status, action, enabled = government.pgu_action(d)
    tone = "ready" if d.pgu.resultado == rules.ELEGIBLE else "pending"
    if d.pgu.resultado in (rules.NO_ELEGIBLE, rules.FUTURO):
        tone = "unavailable"
    with st.container(border=True, key="gov_pgu"):
        info, control = st.columns([4, 1.3], vertical_alignment="center")
        with info:
            st.markdown(
                '<h3 class="gov-benefit-title">Pensión Garantizada Universal</h3>'
                f'<span class="gov-status {tone}">{escape(status)}</span>',
                unsafe_allow_html=True,
            )
            if d.pgu.resultado == rules.ELEGIBLE:
                st.caption(
                    f"{_money(d.pgu.monto_estimado)} al mes estimados · El IPS confirma el pago"
                )
        with control:
            st.button(
                action,
                type="primary",
                key="gov_pgu_action",
                disabled=not enabled,
                use_container_width=True,
                on_click=_set_route,
                args=(d.run, "PGU"),
            )
        with st.expander("Ver requisitos y detalles"):
            st.write(d.pgu.motivo)
            for requirement in d.pgu.requisitos:
                label = {
                    rules.CUMPLE: "Cumple",
                    rules.NO_CUMPLE: "No cumple",
                    rules.FALTA: "Falta información",
                    rules.PENDIENTE: "Más adelante",
                }
                st.markdown(f"**{requirement.nombre}** · {label[requirement.estado]}")
                st.caption(requirement.detalle + " Fuente: " + requirement.fuente)
            st.link_button("Consultar requisitos oficiales ↗", config.FUENTE_PGU)
            _requirement_documents(d.run, "pgu")
    for option in government.EDUCATION_OPTIONS:
        _pending_benefit(d.run, option)


def _pending_benefit(run: str, option: dict) -> None:
    with st.container(border=True, key=f"gov_benefit_{option['id']}"):
        info, control = st.columns([4, 1.3], vertical_alignment="center")
        with info:
            st.markdown(
                f'<h3 class="gov-benefit-title">{escape(option["title"])}</h3>'
                '<span class="gov-status pending">Faltan datos para verificar</span>',
                unsafe_allow_html=True,
            )
            st.caption(option["description"])
        state_key = f"gov_missing_{run}_{option['id']}"
        with control:
            if st.button(
                "Ver datos faltantes", key=f"gov_check_{option['id']}", use_container_width=True
            ):
                st.session_state[state_key] = not st.session_state.get(state_key, False)
        with st.expander(
            "Ver requisitos y adjuntar documentos", expanded=bool(st.session_state.get(state_key))
        ):
            st.markdown("**Para revisar si puedes acceder, necesitamos conocer:**")
            for missing in option["missing"]:
                st.markdown("- " + missing)
            st.caption(
                "Estos beneficios aún no tienen una evaluación integrada en Mi Gobierno. "
                "Los datos deben verificarse con Mineduc antes de confirmar si corresponden."
            )
            st.link_button("Revisar en Mineduc ↗", option["source"])
            _requirement_documents(run, option["id"])


def _personal(d, profile) -> None:
    st.caption("Profesión, ocupación, situación laboral y actividad económica.")
    rsh = profile.get("rsh")
    st.markdown("#### Registro Social de Hogares")
    if rsh:
        st.write(
            f"Tramo CSE: **{rsh['cse_tramo']}%** · "
            f"Integrantes: **{rsh['num_integrantes']}** · "
            f"Actualización: **{rsh['fecha_actualizacion']}**"
        )
        st.caption("El tramo CSE no equivale al Puntaje de Focalización Previsional de la PGU.")
    else:
        st.info("No hay RSH en el perfil. Puedes adjuntarlo en Mis documentos.")
    saved = government.load_profile(d.run)
    st.markdown("#### Mi situación económica")
    st.caption(
        "Información declarada por ti. Se guarda para preparar tu caso; "
        "no sustituye antecedentes oficiales ni cambia por sí sola tu evaluación."
    )
    with st.form(f"gov_personal_{d.run}"):
        profession = st.text_input(
            "Profesión",
            value=saved.get("profession", ""),
            placeholder="Registra tu profesión",
            max_chars=160,
        )
        occupation = st.text_input(
            "Ocupación",
            value=saved.get("occupation", ""),
            placeholder="¿A qué te dedicas actualmente?",
            max_chars=160,
        )
        activity = st.text_input(
            "Actividad económica",
            value=saved.get("economic_activity", ""),
            placeholder="Rubro o actividad",
            max_chars=200,
        )
        options = [
            "Prefiero no indicar",
            "Trabajo dependiente",
            "Trabajo independiente",
            "Sin trabajo",
            "Pensionado/a",
            "Estudiante",
        ]
        employment = st.selectbox(
            "Situación laboral", options, index=options.index(saved.get("employment", options[0]))
        )
        income = st.number_input(
            "Ingresos mensuales del hogar ($)",
            min_value=0,
            value=int(saved.get("monthly_income", 0)),
            step=10000,
        )
        size = st.number_input(
            "Personas en el hogar",
            min_value=1,
            max_value=100,
            value=int(saved.get("household_size", (rsh or {}).get("num_integrantes", 1))),
        )
        notes = st.text_area(
            "Antecedentes que quieras agregar", value=saved.get("notes", ""), max_chars=4000
        )
        if st.form_submit_button("Guardar mi información", type="primary"):
            government.save_profile(
                d.run,
                {
                    "employment": employment,
                    "monthly_income": income,
                    "household_size": size,
                    "notes": notes,
                    "profession": profession,
                    "occupation": occupation,
                    "economic_activity": activity,
                },
            )
            st.success("Información guardada. Pendiente de validación.")


def _documents(d) -> None:
    st.caption(
        "Adjunta una sola vez. Tus documentos estarán disponibles en todos los beneficios "
        "que los necesiten."
    )
    _document_tiles(d.run, government.DOCUMENT_TYPES, "personal")


def _requirement_documents(run: str, benefit: str) -> None:
    st.markdown("**Documentos para preparar este trámite**")
    st.caption(
        "Puedes adjuntarlos aquí o en Datos personales. Se reutilizan entre beneficios; "
        "adjuntar no confirma el cumplimiento de un requisito."
    )
    _document_tiles(run, government.BENEFIT_DOCUMENTS[benefit], benefit)


def _document_tiles(run: str, kinds, namespace: str) -> None:
    saved = {document["kind"]: document for document in government.list_documents(run)}
    for start in range(0, len(kinds), 3):
        columns = st.columns(3, gap="medium")
        for column, kind in zip(columns, kinds[start : start + 3], strict=False):
            with column:
                _document_slot(run, kind, saved.get(kind), namespace)
    st.caption("PDF, JPG o PNG · máximo 10 MB por documento.")


def _document_slot(run: str, kind: str, document: dict | None, namespace: str) -> None:
    index = government.DOCUMENT_TYPES.index(kind)
    context = f"{namespace}_{index}"
    with st.container(border=True, key=f"gov_document_slot_{context}"):
        st.markdown(
            '<div class="gov-document-title"><span aria-hidden="true">▤</span>'
            f"<b>{escape(kind)}</b></div>",
            unsafe_allow_html=True,
        )
        if document:
            st.text(document["name"])
            st.caption(
                "Disponible para este beneficio · pendiente de revisión"
                if namespace != "personal"
                else "Adjunto · disponible para tus beneficios"
            )
        else:
            st.caption("Falta adjuntar")
        with st.popover("Reemplazar" if document else "Adjuntar", use_container_width=True):
            st.markdown(f"**{kind}**")
            with st.form(f"gov_document_{run}_{context}", clear_on_submit=True):
                upload = st.file_uploader(
                    f"Adjuntar {kind}",
                    key=f"gov_upload_{run}_{context}",
                    type=["pdf", "jpg", "jpeg", "png"],
                )
                if st.form_submit_button("Guardar documento"):
                    if upload is None:
                        st.warning("Selecciona un archivo para adjuntar.")
                    else:
                        try:
                            government.save_document(run, kind, upload.name, upload.getvalue())
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
        if document:
            if st.button("Eliminar", key=f"gov_delete_{run}_{context}"):
                government.delete_document(run, kind)
                st.rerun()
            st.caption("Eliminarlo lo retira de todos los beneficios que lo usan.")


def _journey(d, case, benefit) -> None:
    st.button("← Volver a Mi Gobierno", on_click=_set_route, args=(d.run, None))
    _, _, allowed = government.pgu_action(d)
    if benefit != "PGU" or not allowed:
        st.info("Este beneficio no está disponible para iniciar con tus antecedentes actuales.")
        return
    route = government.benefit_route(d, benefit)
    states = estado_pasos(route, case["completados"])
    next_step = proximo_paso(route, states)
    completed = sum(states[step.id] == "completado" for step in route)
    st.markdown(
        '<span class="gov-eyebrow">TU RUTA PARA RECIBIR EL BENEFICIO</span>', unsafe_allow_html=True
    )
    st.subheader("Pensión Garantizada Universal · paso a paso")
    st.progress(
        completed / len(route) if route else 0,
        text=f"{completed} de {len(route)} pasos completados",
    )
    main, chat = st.columns([2, 1], gap="large")
    with main:
        for index, step in enumerate(route, 1):
            state = states[step.id]
            labels = {
                "completado": "Completado",
                "disponible": "Tu próximo paso",
                "bloqueado": "Pendiente del paso anterior",
                "en_espera": "Disponible más adelante",
            }
            with st.expander(
                f"{index}. {step.titulo} · {labels[state]}",
                expanded=bool(next_step and step.id == next_step.id),
            ):
                st.write(step.que_hacer)
                st.markdown("**Dónde:** " + step.donde)
                if step.documentos:
                    st.markdown("**Necesitas:** " + ", ".join(step.documentos))
                if step.disponible_desde:
                    st.write("Disponible desde: " + fmt(step.disponible_desde))
                if step.fuente:
                    st.link_button("Consultar el sitio oficial ↗", step.fuente)
                if step.tipo == "organismo":
                    st.info(
                        "La resolución y el pago los confirma el organismo. "
                        "Esta demo no presenta solicitudes ni ejecuta pagos."
                    )
                    if state == "completado":
                        st.caption("Este paso fue completado en la simulación de la demo.")
                elif state == "disponible":
                    if st.button("Ya completé este paso", key=f"gov_step_{d.run}_{step.id}"):
                        casos.completar_paso(d.run, step.id, CANAL, step.titulo)
                        st.rerun()
    with chat:
        context = asistente.construir_contexto(d, route, states, next_step, True)
        ui_persona._asistente(d, d.run, CANAL, context)
