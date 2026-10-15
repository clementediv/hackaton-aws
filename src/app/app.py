"""ChileAtiende a Tiempo — MVP Jubilación + PGU.

Ejecutar:  .venv\\Scripts\\streamlit run app.py
"""
import json

import pandas as pd
import streamlit as st

import ui_persona
import ui_government
import ui_ficha
from ui_embudo import render_campaign_lab
import portal
from ruta import asistente, casos, config
from ruta import reglas as R
from ruta.datos import cargar_perfiles
from ruta.fechas import fmt
from ruta.rutas import estado_pasos, generar_ruta, proximo_paso

st.set_page_config(page_title="ChileAtiende · Ayuda para tus trámites", page_icon="🧭", layout="wide",
                   initial_sidebar_state="collapsed")

ICONO_REQ = {R.CUMPLE: "✅", R.NO_CUMPLE: "❌", R.FALTA: "⚠️", R.PENDIENTE: "⏳"}
ICONO_PASO = {"completado": "✅", "disponible": "👉", "bloqueado": "🔒", "en_espera": "📅"}
ETIQUETA_PASO = {"completado": "Completado", "disponible": "Puedes hacerlo ahora",
                 "bloqueado": "Requiere el paso anterior", "en_espera": "Disponible desde la fecha indicada"}


@st.cache_data
def diagnosticos() -> dict[str, R.Diagnostico]:
    return {run: R.diagnosticar(p) for run, p in cargar_perfiles().items()}


def tabla_diagnosticos(diags: dict[str, R.Diagnostico]) -> pd.DataFrame:
    return pd.DataFrame([{
        "run": d.run, "nombre": d.nombre, "edad": d.hitos.edad, "sexo": d.hitos.sexo,
        "segmento": d.segmento, "invitar": d.invitar, "pgu": d.pgu.resultado,
        "jubilacion": d.jubilacion.resultado, "motivo": d.razon_invitacion,
        "monto_pgu_orientativo": d.pgu.monto_estimado if d.pgu.resultado in (R.ELEGIBLE, R.PROXIMO) else None,
    } for d in diags.values()])


def casos_demo(diags: dict[str, R.Diagnostico]) -> dict[str, str]:
    """Un caso representativo por escenario del PPT."""
    elegir = lambda f: next((d.run for d in diags.values() if f(d)), None)
    demo = {
        "Rosa: mujer a un año de jubilar": elegir(lambda d: d.hitos.sexo == "F" and d.jubilacion.resultado == "proximo"),
        "En ventana de solicitud PGU (64a9m)": elegir(lambda d: d.pgu.resultado == R.PROXIMO and d.hitos.edad == 64),
        "65+ que podría solicitar PGU": elegir(lambda d: d.pgu.resultado == R.ELEGIBLE and d.pgu.pension_base > 0),
        "PGU suspendida por antecedente faltante": elegir(lambda d: d.pgu.resultado == R.ANTECEDENTE_FALTANTE and d.pgu.pgu_registro),
        "Sin Registro Social de Hogares": elegir(lambda d: d.pgu.resultado == R.ANTECEDENTE_FALTANTE and d.pgu.pgu_registro is None),
        "No cumple residencia (vive en el extranjero)": elegir(lambda d: d.pgu.resultado == R.NO_ELEGIBLE and "extranjero" in d.pgu.requisitos[2].detalle),
    }
    return {k: v for k, v in demo.items() if v}


# --------------------------------------------------------------------------
def vista_mapa(diags):
    st.header("Mapa de calor y campañas")
    render_campaign_lab(cargar_perfiles())


def vista_panel(diags):
    st.header("1 · Detectar e invitar")
    st.caption(f"Evaluación de los {len(diags)} perfiles del dataset A al {fmt(config.FECHA_REFERENCIA)}. "
               "Solo se usan datos autorizados para detectar el hito; las personas fallecidas quedan excluidas.")
    df = tabla_diagnosticos(diags)
    a_invitar = df[df.invitar]
    c = st.columns(5)
    c[0].metric("Personas a invitar", len(a_invitar))
    c[1].metric("PGU: podría solicitar", int((df.pgu == R.ELEGIBLE).sum()))
    c[2].metric("PGU: falta antecedente", int((df.segmento == "PGU: falta antecedente").sum()))
    c[3].metric("Próximos a 65", int((df.pgu == R.PROXIMO).sum()))
    c[4].metric("A un año de la edad legal", int((df.jubilacion == "proximo").sum()))
    monto = df.loc[df.pgu == R.ELEGIBLE, "monto_pgu_orientativo"].sum()
    st.info(f"PGU potencialmente no cobrada detectada: **{int((df.pgu == R.ELEGIBLE).sum())} personas**, "
            f"≈ **${monto:,.0f} al mes** (orientativo; el IPS resuelve).".replace(",", "."))

    st.subheader("Segmentos")
    st.bar_chart(df[df.segmento != "Sin hito cercano"].segmento.value_counts())

    st.subheader("Campaña de invitación")
    segs = sorted(a_invitar.segmento.unique())
    sel = st.multiselect("Segmentos a invitar", segs, default=segs)
    canal = st.selectbox("Canal de la invitación", config.CANALES[:3])
    objetivo = a_invitar[a_invitar.segmento.isin(sel)]
    estado_inv = {c["run"]: c["invitacion"] for c in casos.todos_los_casos()}
    objetivo = objetivo.assign(invitacion=objetivo.run.map(estado_inv).fillna("no_invitado"))
    st.dataframe(objetivo[["run", "nombre", "edad", "sexo", "segmento", "motivo", "invitacion"]],
                 hide_index=True, use_container_width=True)
    if st.button(f"Enviar invitación a {int((objetivo.invitacion == 'no_invitado').sum())} personas", type="primary"):
        n = casos.invitar(objetivo.run.tolist(), canal)
        st.session_state["aviso"] = f"{n} invitaciones enviadas por {canal} (simulado)."
        st.rerun()
    if aviso := st.session_state.pop("aviso", None):
        st.success(aviso)
    with st.expander("Ver ejemplo de mensaje de invitación"):
        if len(objetivo):
            st.write(asistente.mensaje_invitacion(diags[objetivo.run.iloc[0]]))


def vista_ejecutivo(diags):
    st.header("Vista ejecutivo · detalle técnico del caso")
    st.caption("Lo que ve un ejecutivo de sucursal o call center: el mismo caso, con requisitos, fuentes e historial.")
    demo = casos_demo(diags)
    vivos = sorted((d for d in diags.values() if d.vivo), key=lambda d: (not d.invitar, -d.hitos.edad))
    opciones = {f"{d.run} · {d.nombre} · {d.hitos.edad} años · {d.segmento}": d.run for d in vivos}

    col1, col2 = st.columns([2, 1])
    atajo = col1.selectbox("Casos de demo", ["(elegir persona)"] + list(demo))
    canal = col2.selectbox("Canal desde el que atiende", config.CANALES,
                           help="Cambia el canal para mostrar que el caso conserva su contexto.")
    if atajo != "(elegir persona)":
        run = demo[atajo]
    else:
        run = opciones[st.selectbox("Persona", list(opciones))]
    d = diags[run]
    caso = casos.obtener_caso(run)

    st.subheader(f"{d.nombre} · {d.hitos.edad} años")
    st.caption(f"RUN {run} · Segmento: {d.segmento}")

    # --- Paso 2: invitación ---------------------------------------------
    with st.container(border=True):
        st.markdown("**Invitación**")
        st.write(asistente.mensaje_invitacion(d))
        if caso["invitacion"] in ("no_invitado", "invitado"):
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Acepto el acompañamiento", type="primary"):
                casos.responder_invitacion(run, True, canal)
                st.rerun()
            if b2.button("No, gracias"):
                casos.responder_invitacion(run, False, canal)
                st.rerun()
            return
        if caso["invitacion"] == "rechazado":
            st.warning("La persona declinó el acompañamiento. No se vuelve a contactar por esta campaña.")
            if st.button("Reabrir (la persona cambió de opinión)"):
                casos.responder_invitacion(run, True, canal)
                st.rerun()
            return
        st.success("Acompañamiento aceptado.")

    # --- Paso 3: autorización -------------------------------------------
    with st.container(border=True):
        st.markdown("**Autorización de uso de datos**")
        st.write("Para preparar tu ruta consultaremos, solo con esta finalidad: Registro Social de Hogares, "
                 "registro de residencia, tu AFP y pensiones o beneficios del IPS. Puedes revocarlo cuando quieras.")
        autorizado = st.toggle("Autorizo consultar estos antecedentes", value=bool(caso["autorizacion"]))
        if autorizado != bool(caso["autorizacion"]):
            casos.autorizar(run, autorizado, canal)
            st.rerun()

    ruta = generar_ruta(d)
    estados = estado_pasos(ruta, caso["completados"])
    prox = proximo_paso(ruta, estados)
    ctx = asistente.construir_contexto(d, ruta, estados, prox, autorizado)

    izq, der = st.columns([3, 2])
    with izq:
        if not autorizado:
            st.info("Sin autorización solo mostramos los hitos según tu fecha de nacimiento.")
            h = d.hitos
            st.table(pd.DataFrame({"Hito": ["Invitación a preparar jubilación", f"Edad legal de vejez ({h.edad_legal})",
                                            "Solicitud PGU (64 años 9 meses)", "Acceso PGU (65)"],
                                   "Fecha": [fmt(h.fecha_invitacion_jubilacion), fmt(h.fecha_edad_legal),
                                             fmt(h.fecha_apertura_pgu), fmt(h.fecha_acceso_pgu)]}))
        else:
            # --- Paso 4: preparar la ruta --------------------------------
            st.markdown("#### Qué sabemos y qué falta")
            st.dataframe(pd.DataFrame([{
                "": ICONO_REQ[r.estado], "Requisito PGU": r.nombre, "Estado": r.estado.replace("_", " "),
                "Detalle": r.detalle, "Fuente": r.fuente} for r in d.pgu.requisitos]),
                hide_index=True, use_container_width=True)
            st.caption(f"Orientación PGU: **{d.pgu.resultado.replace('_', ' ')}** — {d.pgu.motivo} "
                       f"· Jubilación: **{d.jubilacion.resultado.replace('_', ' ')}** — {d.jubilacion.motivo}")
            st.markdown("#### Tu ruta")
            if prox:
                st.success(f"Próximo paso: **{prox.titulo}**")
            for p in ruta:
                est = estados[p.id]
                with st.expander(f"{ICONO_PASO[est]} [{p.tramite}] {p.titulo} — {ETIQUETA_PASO[est]}",
                                 expanded=(prox is not None and p.id == prox.id)):
                    st.write(p.que_hacer)
                    st.markdown(f"**Dónde:** {p.donde}")
                    if p.documentos:
                        st.markdown("**Documentos:** " + ", ".join(p.documentos))
                    if p.disponible_desde:
                        st.markdown(f"**Desde:** {fmt(p.disponible_desde)}")
                    if p.fuente:
                        st.markdown(f"**Fuente:** {p.fuente}")
                    if est == "disponible":
                        etiqueta = "Simular respuesta del organismo" if p.tipo == "organismo" else "Marcar como hecho"
                        if st.button(etiqueta, key=f"ok-{p.id}"):
                            casos.completar_paso(run, p.id, canal, p.titulo)
                            st.rerun()
                    elif est == "en_espera" and st.button("Simular que llegó la fecha", key=f"f-{p.id}"):
                        casos.completar_paso(run, p.id, canal, p.titulo)
                        st.rerun()
                    elif est == "completado" and st.button("Reabrir", key=f"re-{p.id}"):
                        casos.deshacer_paso(run, p.id, canal)
                        st.rerun()
            if ruta and all(e == "completado" for e in estados.values()):
                st.balloons()
                st.success(f"Ruta completada. Próximo hito a anticipar: tramo 75+ de la PGU el {fmt(d.hitos.fecha_tramo_75)}.")

    # --- Paso 5: acompañar (asistente) ----------------------------------
    with der:
        st.markdown("#### Asistente")
        st.caption("Motor: " + (f"Amazon Bedrock ({config.BEDROCK_MODEL_ID})" if config.BEDROCK_MODEL_ID else
                                "plantillas (configura BEDROCK_MODEL_ID para usar IA generativa)"))
        clave = f"chat-{run}"
        if not autorizado or clave not in st.session_state:
            st.session_state[clave] = [{"rol": "assistant", "texto": asistente.explicar_resumen(ctx)}]
        for m in st.session_state[clave]:
            st.chat_message(m["rol"]).write(m["texto"])
        st.caption("Prueba: ¿qué es la PGU? · ¿cuánto recibiría? · ¿qué documentos necesito? · ¿cumplo los requisitos?")
        if pregunta := st.chat_input("Escribe tu pregunta"):
            hist = st.session_state[clave]
            resp, motor = asistente.responder(pregunta, ctx, hist)
            hist += [{"rol": "user", "texto": pregunta}, {"rol": "assistant", "texto": resp}]
            casos.registrar_evento(run, canal, "consulta_asistente", {"pregunta": pregunta, "motor": motor})
            st.rerun()

        st.markdown("#### Historial del caso (todos los canales)")
        if caso["eventos"]:
            ev = pd.DataFrame(caso["eventos"])
            ev["detalle"] = ev.detalle.fillna("").map(
                lambda s: ", ".join(f"{k}: {v}" for k, v in json.loads(s).items()) if s.startswith("{") else s)
            st.dataframe(ev, hide_index=True, use_container_width=True)
        else:
            st.caption("Sin eventos todavía.")


def vista_kpis(diags):
    st.header("3 · Cómo lo medimos")
    st.caption("KPIs del PPT calculados sobre los casos registrados en esta demo.")
    todos = casos.todos_los_casos()
    invitados = [c for c in todos if c["invitacion"] != "no_invitado"]
    aceptados = [c for c in invitados if c["invitacion"] == "aceptado"]

    def avanzo(c):
        d = diags.get(c["run"])
        if not d:
            return False
        ruta = generar_ruta(d)
        # Completó al menos un paso válido distinto de la lectura informativa G0
        return any(p.id in c["completados"] and p.id != "G0" for p in ruta)

    completaron = [c for c in invitados if avanzo(c)]
    multicanal = [c for c in aceptados if c["n_canales"] > 1]
    pct = lambda a, b: f"{(100 * len(a) / len(b)):.0f}%" if b else "—"
    c = st.columns(4)
    c[0].metric("Invitados", len(invitados))
    c[1].metric("Aceptan acompañamiento", pct(aceptados, invitados), help="Contacto efectivo · referencia IPS 85%")
    c[2].metric("⭐ Completan el próximo paso", pct(completaron, invitados), help="KPI estrella · meta ≥ 70%")
    c[3].metric("Casos atendidos en >1 canal con contexto", len(multicanal), help="Continuidad · meta ≥ 90%")
    st.caption("Comprensión (meta ≥ 80%) requiere una encuesta breve al cerrar cada paso: queda para el piloto.")
    if st.button("Reiniciar datos de la demo"):
        casos.reiniciar()
        for k in [k for k in st.session_state if k.startswith("chat-")]:
            del st.session_state[k]
        st.rerun()


def vista_oficina(diags):
    st.header("Vista ejecutivo")
    st.caption("Gestiona campañas, revisa beneficiarios, atiende casos y consulta los resultados.")
    selected = st.radio(
        "Herramientas del ejecutivo",
        portal.EXECUTIVE_SECTIONS,
        horizontal=True,
        key="executive_section",
    )
    views = {
        "Mapa de calor y campañas": vista_mapa,
        "Detectar e invitar": vista_panel,
        "Ficha del beneficiario": ui_ficha.render,
        "Atención del caso": vista_ejecutivo,
        "Medición": vista_kpis,
    }
    views[selected](diags)


# --------------------------------------------------------------------------
diags = diagnosticos()
if next_section := st.session_state.pop("portal_next_section", None):
    st.session_state["portal_section"] = next_section
section = portal.render_header()
portal.hero(section)
with st.sidebar:
    st.title("Controles de demostración")
    st.caption("Perfiles sintéticos · El organismo valida y resuelve.")
    st.divider()
if section == "Vista ejecutivo":
    vista_oficina(diags)
elif section == "Inicio":
    portal.render_discovery()
elif section == "Mi Gobierno":
    ui_government.render(diags)
else:
    if section == "Ayuda para tus trámites":
        portal.render_help_intro()
    ui_persona.vista(diags, casos_demo(diags))
portal.render_footer()
