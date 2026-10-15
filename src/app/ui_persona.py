"""Vista ciudadana: guía paso a paso, en lenguaje simple, una tarea a la vez.

Pantallas: 1 Invitación → 2 Autorización → 3 Tu situación → 4 Tu ruta.
Los controles de demo (persona, canal, simulaciones) viven en la barra lateral
o están rotulados como "demo" para no confundirlos con la experiencia real.
"""
from datetime import date
from html import escape

import streamlit as st

from ruta import asistente, casos, config
from ruta import reglas as R
from ruta.fechas import fmt
from ruta.rutas import Paso, estado_pasos, generar_ruta, proximo_paso

REF = config.FECHA_REFERENCIA
ETAPAS = ["Invitación", "Autorización", "Tu situación", "Tu ruta"]

CSS = """
<style>
.ca-hero{background:#0d4d82;color:#fff;padding:1.3rem 1.6rem;border-radius:6px;margin-bottom:1rem}
.ca-hero h2{color:#fff;margin:0 0 .3rem 0;font-size:1.7rem}
.ca-hero p{color:#fff;margin:0;font-size:1.1rem;opacity:.95}
.ca-card{border:1px solid #d5dde8;border-radius:6px;padding:1rem 1.2rem;background:#fff;color:#1b2733;margin-bottom:.7rem}
.ca-card h4{margin:.1rem 0 .35rem 0;color:#0F2F4F;font-size:1.15rem}
.ca-card p{margin:.2rem 0;font-size:1.05rem;line-height:1.5}
.ca-now{border:2px solid #0F69B4;background:#F3F8FD}
.ca-big{font-size:2.1rem;font-weight:700;color:#0F4C81;margin:.2rem 0}
.ca-badge{display:inline-block;padding:.15rem .65rem;border-radius:999px;font-size:.85rem;font-weight:700;margin-bottom:.3rem}
.ok{background:#E3F2E7;color:#1B5E2E}.warn{background:#FFF1DC;color:#7A4100}
.bad{background:#FCE4E4;color:#9B1C1C}.wait{background:#E4EEF9;color:#0F4C81}.lock{background:#ECEFF3;color:#3D4A57}
.ca-steps{display:flex;gap:.4rem;margin:.2rem 0 1.1rem 0;flex-wrap:wrap}
.ca-step{flex:1;min-width:105px;text-align:center;padding:.55rem .3rem;border-radius:4px;font-weight:600;font-size:.85rem;
         background:#ECEFF3;color:#3D4A57;border-bottom:4px solid #C5CDD6}
.ca-step.done{background:#E3F2E7;color:#1B5E2E;border-bottom-color:#2E7D32}
.ca-step.cur{background:#0F4C81;color:#fff;border-bottom-color:#EB3C46}
.ca-line{display:flex;gap:.8rem;align-items:flex-start;padding:.55rem 0;border-bottom:1px solid #e6ebf1;color:#1b2733}
.ca-line:last-child{border-bottom:none}
.ca-dot{font-size:1.3rem;line-height:1.4rem;width:1.6rem;text-align:center}
.ca-line b{font-size:1.02rem}.ca-line small{color:#4A5866;font-size:.92rem}
.ca-docs li{font-size:1.02rem;margin:.15rem 0}
</style>
"""

# --- Lenguaje simple para los requisitos ---------------------------------
TITULO_REQ = {"edad": "Tu edad", "pfp": "Tu Registro Social de Hogares",
              "residencia": "Tus años viviendo en Chile", "pension_base": "Tu pensión actual"}
BADGE_REQ = {R.CUMPLE: ("ok", "✔ En orden"), R.NO_CUMPLE: ("bad", "✖ No cumple"),
             R.FALTA: ("warn", "! Falta información"), R.PENDIENTE: ("wait", "⏳ Todavía no")}
BADGE_PASO = {"completado": ("ok", "✔", "Listo"), "disponible": ("wait", "👉", "Puedes hacerlo ahora"),
              "bloqueado": ("lock", "🔒", "Después del paso anterior"), "en_espera": ("wait", "📅", "Más adelante")}


def _peso(n: int) -> str:
    return f"${n:,.0f}".replace(",", ".")


def _cuando(f: date) -> str:
    dias = (f - REF).days
    if dias == 0:
        return "hoy"
    if dias < 0:
        return f"desde el {fmt(f)}"
    if dias < 45:
        return f"en {dias} días ({fmt(f)})"
    return f"en {round(dias / 30.4)} meses ({fmt(f)})"


def texto_requisito(r: R.Requisito, d: R.Diagnostico) -> str:
    h = d.hitos
    if r.id == "edad":
        if r.estado == R.CUMPLE:
            return f"Tienes {h.edad} años: ya tienes la edad para la PGU."
        if REF >= h.fecha_apertura_pgu:
            return f"Ya puedes pedirla. Cumples 65 {_cuando(h.fecha_acceso_pgu)}."
        return f"Podrás pedir la PGU {_cuando(h.fecha_apertura_pgu)}."
    if r.id == "pfp":
        return {R.CUMPLE: "Según tu Registro Social de Hogares, tu hogar está dentro del grupo que puede recibir la PGU.",
                R.NO_CUMPLE: "Según tu Registro Social de Hogares, tu hogar está en el 10% de mayores ingresos del país.",
                R.FALTA: ("No encontramos tu Registro Social de Hogares. Sin él no podemos orientarte sobre la PGU."
                          if "No tiene" in r.detalle else
                          "Tu Registro Social de Hogares está incompleto. Hay que actualizarlo.")}[r.estado]
    if r.id == "residencia":
        if r.estado == R.CUMPLE:
            return "Tienes los años de residencia en Chile que se piden."
        if r.estado == R.FALTA:
            return "No encontramos tus registros de entradas y salidas del país."
        extra = " Además, los registros indican que hoy vives fuera de Chile." if "extranjero" in r.detalle else ""
        return ("Los registros no muestran los años en Chile que se piden: 20 años desde los 20, "
                "y 4 de los últimos 5." + extra)
    if r.id == "pension_base":
        if d.pgu.pension_base == 0:
            return "No registras pensiones: no es un impedimento."
        return (f"Tu pensión ({_peso(d.pgu.pension_base)}) está bajo el límite." if r.estado == R.CUMPLE else
                f"Tu pensión ({_peso(d.pgu.pension_base)}) supera el límite de la PGU "
                f"({_peso(config.PGU['pension_superior'])}).")
    return r.detalle


def titular(d: R.Diagnostico) -> tuple[str, str]:
    """Título y bajada de la pantalla 'Tu situación', según el resultado."""
    p, j = d.pgu.resultado, d.jubilacion.resultado
    if p == R.ELEGIBLE:
        return "Podrías solicitar la PGU", "Revisamos tus antecedentes y están en orden. Te mostramos cómo pedirla."
    if p == R.PROXIMO:
        return "Ya casi: prepárate para la PGU", "Tus antecedentes están en orden. Te avisamos y te guiamos cuando llegue el momento."
    if p == R.ANTECEDENTE_FALTANTE:
        return "Nos falta un dato para seguir", "No es un rechazo. Te mostramos cómo conseguirlo y después continuamos."
    if p == R.NO_ELEGIBLE:
        return "Hoy la PGU no corresponde", "Te explicamos por qué y qué podría cambiarlo."
    if p == R.YA_RECIBE:
        return "Ya recibes la PGU", "Te acompañamos con lo que viene."
    if j in ("proximo", "puede_pensionarse"):
        return "Se acerca tu jubilación", "Te ayudamos a prepararla paso a paso, sin sorpresas."
    return "Aún es temprano", "Te avisaremos cuando se acerquen tus fechas importantes."


def _proximo_hito(d: R.Diagnostico) -> str:
    """Paso 6 del PPT, 'cerrar y anticipar': el siguiente hito que aplica a esta persona."""
    h = d.hitos
    if d.pgu.resultado in (R.NO_ELEGIBLE, R.EXCLUIDO):
        return "Si tu situación cambia (hogar, residencia o pensión), vuelve y revisamos de nuevo tu caso."
    if REF < h.fecha_apertura_pgu:
        return f"Te avisaremos {_cuando(h.fecha_apertura_pgu)}, cuando puedas pedir la PGU."
    if REF < h.fecha_acceso_pgu:
        return f"Cumples 65 {_cuando(h.fecha_acceso_pgu)}: desde ahí el IPS puede empezar a pagarte la PGU."
    if h.edad < 75:
        return (f"A los 75 años ({fmt(h.fecha_tramo_75)}) la PGU máxima sube a "
                f"{_peso(config.PGU['monto_max_75_mas'])}. Te avisaremos.")
    return "Te avisaremos si hay cambios en tu PGU o nuevos beneficios para ti."


# --- Piezas visuales -------------------------------------------------------
def _stepper(actual: int) -> None:
    html = "".join(
        f'<div class="ca-step {"done" if i < actual else "cur" if i == actual else ""}">'
        f'{"✔ " if i < actual else f"{i + 1}. "}{e}</div>' for i, e in enumerate(ETAPAS))
    st.markdown(f'<div class="ca-steps" role="list" aria-label="Etapas">{html}</div>', unsafe_allow_html=True)


def _hero(titulo: str, bajada: str) -> None:
    st.markdown(f'<div class="ca-hero"><h2>{escape(titulo)}</h2><p>{escape(bajada)}</p></div>', unsafe_allow_html=True)


def _card(titulo: str, cuerpo: str, badge: tuple[str, str] | None = None, clase: str = "") -> None:
    b = f'<span class="ca-badge {badge[0]}">{escape(badge[1])}</span>' if badge else ""
    st.markdown(f'<div class="ca-card {clase}">{b}<h4>{escape(titulo)}</h4><p>{cuerpo}</p></div>',
                unsafe_allow_html=True)


def _fechas_importantes(d: R.Diagnostico) -> None:
    h = d.hitos
    filas = []
    if d.jubilacion.resultado in ("futuro", "proximo"):
        filas.append(("🎂", f"Cumples {h.edad_legal}: edad legal para jubilar", h.fecha_edad_legal))
    if d.pgu.resultado in (R.FUTURO, R.PROXIMO, R.ANTECEDENTE_FALTANTE, R.ELEGIBLE) and h.edad < 65:
        filas.append(("📝", "Puedes pedir la PGU (64 años y 9 meses)", h.fecha_apertura_pgu))
        filas.append(("💰", "Cumples 65: puedes recibir la PGU", h.fecha_acceso_pgu))
    if h.edad < 75 and d.pgu.resultado in (R.ELEGIBLE, R.PROXIMO, R.YA_RECIBE):
        filas.append(("⬆️", f"A los 75 la PGU máxima sube a {_peso(config.PGU['monto_max_75_mas'])}", h.fecha_tramo_75))
    if not filas:
        return
    lineas = "".join(f'<div class="ca-line"><div class="ca-dot" aria-hidden="true">{i}</div>'
                     f'<div><b>{escape(t)}</b><br><small>{escape(_cuando(f))}</small></div></div>'
                     for i, t, f in filas)
    st.markdown(f'<div class="ca-card"><h4>Tus fechas importantes</h4>{lineas}</div>', unsafe_allow_html=True)


# --- Pantallas -------------------------------------------------------------
def _pantalla_invitacion(d, run, canal):
    _stepper(0)
    _hero(f"Hola, {d.nombre.split()[0]}", "ChileAtiende quiere ayudarte antes de que tengas que buscar por tu cuenta.")
    _card("¿Por qué te escribimos?", escape(asistente.mensaje_invitacion(d)))
    _card("¿Qué ganas?",
          "• Saber qué te corresponde, en palabras simples.<br>• Una lista clara de pasos, documentos y fechas.<br>"
          "• No repetir tu historia: retomas donde quedaste, por cualquier canal.")
    c1, c2 = st.columns(2)
    if c1.button("Sí, quiero que me acompañen", type="primary", use_container_width=True):
        casos.responder_invitacion(run, True, canal)
        st.rerun()
    if c2.button("No, gracias", use_container_width=True):
        casos.responder_invitacion(run, False, canal)
        st.rerun()


def _pantalla_rechazo(d, run, canal):
    _hero("Entendido", "No volveremos a contactarte por esta campaña.")
    _card("Si cambias de opinión", "Puedes volver cuando quieras desde chileatiende.gob.cl o llamando al 101.")
    if st.button("Cambié de opinión, quiero el acompañamiento", type="primary"):
        casos.responder_invitacion(run, True, canal)
        st.rerun()


def _pantalla_autorizacion(d, run, canal):
    _stepper(1)
    _hero("Antes de revisar tu caso, necesitamos tu permiso",
          "Solo usaremos estos datos para preparar tu ruta. Puedes retirar el permiso cuando quieras.")
    fuentes = [("🏠", "Registro Social de Hogares", "para saber si tu hogar está en el grupo que puede recibir la PGU"),
               ("✈️", "Registro de entradas y salidas del país", "para revisar tus años viviendo en Chile"),
               ("🏦", "Tu AFP", "para conocer tus cotizaciones y tu pensión estimada"),
               ("📄", "Pensiones y beneficios del IPS", "para saber qué recibes hoy")]
    lineas = "".join(f'<div class="ca-line"><div class="ca-dot" aria-hidden="true">{i}</div>'
                     f'<div><b>{escape(t)}</b><br><small>{escape(x)}</small></div></div>' for i, t, x in fuentes)
    st.markdown(f'<div class="ca-card"><h4>Qué vamos a consultar</h4>{lineas}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("Sí, autorizo", type="primary", use_container_width=True):
        casos.autorizar(run, True, canal)
        st.session_state.pop(f"sinaut-{run}", None)
        st.session_state[f"pantalla-{run}"] = "situacion"
        st.rerun()
    if c2.button("Ahora no", use_container_width=True):
        st.session_state[f"sinaut-{run}"] = True
        st.rerun()


def _pantalla_sin_autorizacion(d, run, canal):
    _stepper(1)
    _hero("Sin problema", "Sin tu permiso solo podemos mostrarte fechas calculadas desde tu fecha de nacimiento.")
    _fechas_importantes(d)
    if st.button("Quiero autorizar ahora", type="primary"):
        st.session_state.pop(f"sinaut-{run}", None)
        st.rerun()


def _pantalla_situacion(d, run, canal, ruta, estados):
    _stepper(2)
    t, b = titular(d)
    _hero(t, b)
    if d.pgu.resultado in (R.ELEGIBLE, R.PROXIMO) and d.pgu.monto_estimado:
        _card("Monto orientativo de tu PGU",
              f'<span class="ca-big">{_peso(d.pgu.monto_estimado)} al mes</span><br>'
              "Es una estimación con los datos disponibles. El monto final lo calcula el IPS.", clase="ca-now")
    if d.pgu.resultado != R.FUTURO:
        st.markdown("#### Lo que revisamos")
        cols = st.columns(2)
        for i, r in enumerate(d.pgu.requisitos):
            with cols[i % 2]:
                _card(TITULO_REQ[r.id], escape(texto_requisito(r, d)), BADGE_REQ[r.estado])
    if d.jubilacion.resultado in ("proximo", "puede_pensionarse"):
        _card("Tu jubilación", escape(d.jubilacion.motivo) +
              (f"<br>Tu AFP es <b>{escape(d.jubilacion.afp)}</b>." if d.jubilacion.afp else ""),
              ("wait", "Jubilación"))
    _fechas_importantes(d)
    st.caption("Esto es una orientación con los datos disponibles. La AFP o el IPS revisan y deciden.")
    if ruta and st.button("Ver mis pasos", type="primary", use_container_width=True):
        st.session_state[f"pantalla-{run}"] = "ruta"
        st.rerun()


def _paso_actual(d, run, canal, p: Paso, estado: str):
    docs = "".join(f"<li>{escape(x)}</li>" for x in p.documentos)
    cuerpo = (f"{escape(p.que_hacer)}<br><br><b>Dónde:</b> {escape(p.donde)}"
              + (f'<br><b>Qué llevar:</b><ul class="ca-docs">{docs}</ul>' if docs else ""))
    if p.tipo == "organismo":
        titulo, badge = f"Estamos esperando: {p.titulo}", ("wait", "⏳ Esperando respuesta")
    elif estado == "en_espera":
        titulo, badge = p.titulo, ("wait", f"📅 Disponible {_cuando(p.disponible_desde)}")
    else:
        titulo, badge = p.titulo, ("wait", "👉 Lo que tienes que hacer ahora")
    _card(titulo, cuerpo, badge, clase="ca-now")
    if p.fuente:
        st.caption(f"Fuente: {p.fuente}")
    if p.tipo == "organismo":
        if st.button("Simular respuesta del organismo (demo)", use_container_width=True, key=f"org-{p.id}"):
            casos.completar_paso(run, p.id, canal, p.titulo)
            st.rerun()
    elif estado == "en_espera":
        if st.button("Simular que llegó la fecha (demo)", use_container_width=True, key=f"fecha-{p.id}"):
            casos.completar_paso(run, p.id, canal, p.titulo)
            st.rerun()
    else:
        etiqueta = "Entendido, sigamos" if p.id == "G0" else "Ya lo hice"
        if st.button(etiqueta, type="primary", use_container_width=True, key=f"hecho-{p.id}"):
            casos.completar_paso(run, p.id, canal, p.titulo)
            st.rerun()


def _pantalla_ruta(d, run, canal, ruta, estados, caso):
    _stepper(3)
    hechos = sum(e == "completado" for e in estados.values())
    prox = proximo_paso(ruta, estados)
    if prox is None and ruta:
        _hero("¡Terminaste tu ruta!", "Hiciste todo lo que estaba en tus manos. Te avisaremos del próximo hito.")
        _card("Lo que viene", escape(_proximo_hito(d)))
    else:
        _hero(f"Tu ruta: paso {min(hechos + 1, len(ruta))} de {len(ruta)}",
              "Vamos de a un paso. Puedes volver cuando quieras y seguir donde quedaste.")
    st.progress(hechos / len(ruta) if ruta else 1.0, text=f"{hechos} de {len(ruta)} pasos listos")
    if prox:
        _paso_actual(d, run, canal, prox, estados[prox.id])

    lineas = []
    for p in ruta:
        clase, icono, txt = BADGE_PASO[estados[p.id]]
        if p.tipo == "organismo" and estados[p.id] != "completado":
            txt = "Lo resuelve " + p.donde
        actual = prox is not None and p.id == prox.id
        lineas.append(f'<div class="ca-line"><div class="ca-dot" aria-hidden="true">{icono}</div><div>'
                      f'<b>{"➜ " if actual else ""}{escape(p.titulo)}</b><br>'
                      f'<small>{escape(p.tramite)} · {escape(txt)}</small></div></div>')
    st.markdown(f'<div class="ca-card"><h4>Todos tus pasos</h4>{"".join(lineas)}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    if c1.button("← Volver a mi situación", use_container_width=True):
        st.session_state[f"pantalla-{run}"] = "situacion"
        st.rerun()
    completados = [p for p in ruta if estados[p.id] == "completado"]
    if completados and c2.button("Deshacer último paso (demo)", use_container_width=True):
        casos.deshacer_paso(run, completados[-1].id, canal)
        st.rerun()


# --- Asistente ---------------------------------------------------------------
PREGUNTAS = ["¿Qué es la PGU?", "¿Cuánto recibiría?", "¿Qué documentos necesito?",
             "¿Cuándo puedo hacerlo?", "¿Dónde lo hago?", "¿Cumplo los requisitos?"]


def _asistente(d, run, canal, ctx, *, sidebar=False):
    with st.container(border=True):
        st.markdown("#### Asistente de ayuda")
        st.caption("Tu chatbot para entender el trámite y encontrar el próximo paso.")
        clave = f"chat-{run}"
        saludo = {"rol": "assistant", "texto": asistente.explicar_resumen(ctx)}
        if sidebar and ctx["autorizado"]:
            saludo["texto"] = (
                f"Hola, {ctx['nombre']}. Estoy aquí para ayudarte con tus beneficios y trámites. "
                "¿Qué te gustaría saber?"
            )
        permiso_clave = f"assistant_consent_{run}"
        if (
            st.session_state.get(permiso_clave) != ctx["autorizado"]
            or len(st.session_state.get(clave, [])) <= 1
        ):
            # Sin preguntas todavía: el saludo se recalcula para reflejar autorización y avance actuales.
            st.session_state[clave] = [saludo]
        st.session_state[permiso_clave] = ctx["autorizado"]
        hist = st.session_state[clave]

        def preguntar(q: str):
            resp, motor = asistente.responder(q, ctx, hist)
            hist.extend([{"rol": "user", "texto": q}, {"rol": "assistant", "texto": resp}])
            casos.registrar_evento(run, canal, "consulta_asistente", {"pregunta": q, "motor": motor})

        if pending_question := st.session_state.pop("portal_pending_question", None):
            preguntar(pending_question)

        def preguntas_rapidas():
            cols = st.columns(1 if sidebar else 2)
            questions = PREGUNTAS if ctx["autorizado"] else PREGUNTAS[:1] + PREGUNTAS[3:4]
            for i, q in enumerate(questions):
                if cols[i % len(cols)].button(q, key=f"q-{run}-{i}", use_container_width=True):
                    preguntar(q)
                    st.rerun()

        if not sidebar:
            preguntas_rapidas()
        mensajes = st.container(height=240 if sidebar else 360, border=not sidebar)
        for i, m in enumerate(hist):
            target = mensajes.container(key=f"gov_chat_{m['rol']}_{i}") if sidebar else mensajes
            avatar = None if sidebar else ("🧭" if m["rol"] == "assistant" else "🙂")
            target.chat_message(m["rol"], avatar=avatar).write(m["texto"])
        if q := st.chat_input("Pregúntale al asistente de trámites"):
            preguntar(q)
            st.rerun()


def _permisos(run, canal, caso):
    with st.expander("🔐 Tus datos y permisos"):
        if caso["autorizacion"]:
            st.write(f"Autorizaste el uso de tus datos el {caso['fecha_autorizacion'][:10]}. "
                     "Solo se usan para preparar tu ruta.")
            if st.button("Retirar mi autorización"):
                casos.autorizar(run, False, canal)
                st.rerun()
        else:
            st.write("No has autorizado el uso de datos adicionales.")


def _historial(caso):
    with st.expander("🕑 Historial de tu caso (todos los canales)"):
        nombres = {"invitacion_enviada": "Te enviamos la invitación", "invitacion_aceptada": "Aceptaste el acompañamiento",
                   "invitacion_rechazada": "Preferiste no recibir acompañamiento", "autorizacion_otorgada": "Autorizaste el uso de datos",
                   "autorizacion_revocada": "Retiraste la autorización", "paso_completado": "Completaste un paso",
                   "paso_reabierto": "Se reabrió un paso", "consulta_asistente": "Hiciste una consulta"}
        if not caso["eventos"]:
            st.caption("Todavía no hay movimientos.")
        for e in reversed(caso["eventos"][-12:]):
            st.markdown(f"- **{nombres.get(e['tipo'], e['tipo'])}** · {e['canal']} · {e['fecha'][:16].replace('T', ' ')}")


# --- Entrada -----------------------------------------------------------------
def vista(diags: dict, demo: dict[str, str]) -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    # Controles de demo (no son parte de la experiencia ciudadana)
    st.sidebar.markdown("### Controles de demo")
    atajo = st.sidebar.selectbox("Caso", list(demo) + ["Otra persona…"])
    if atajo == "Otra persona…":
        vivos = sorted((d for d in diags.values() if d.vivo), key=lambda d: (not d.invitar, -d.hitos.edad))
        opciones = {f"{d.nombre} · {d.hitos.edad} años": d.run for d in vivos}
        run = opciones[st.sidebar.selectbox("Persona", list(opciones))]
    else:
        run = demo[atajo]
    canal = st.sidebar.selectbox("Canal", config.CANALES,
                                 help="Cambia el canal: el caso conserva su avance y contexto.")
    st.sidebar.caption(f"Viendo como: {canal}")

    d: R.Diagnostico = diags[run]
    caso = casos.obtener_caso(run)
    ruta = generar_ruta(d)
    estados = estado_pasos(ruta, caso["completados"])
    autorizado = bool(caso["autorizacion"])
    ctx = asistente.construir_contexto(d, ruta, estados, proximo_paso(ruta, estados), autorizado)

    if caso["invitacion"] in ("no_invitado", "invitado"):
        route_col, chat_col = st.columns([3, 2], gap="large")
        with route_col:
            _pantalla_invitacion(d, run, canal)
        with chat_col:
            _asistente(d, run, canal, ctx)
        return
    if caso["invitacion"] == "rechazado":
        _, centro, _ = st.columns([1, 3, 1])
        with centro:
            _pantalla_rechazo(d, run, canal)
        return

    izq, der = st.columns([3, 2], gap="large")
    with izq:
        if not autorizado:
            if st.session_state.get(f"sinaut-{run}"):
                _pantalla_sin_autorizacion(d, run, canal)
            else:
                _pantalla_autorizacion(d, run, canal)
        elif st.session_state.get(f"pantalla-{run}", "situacion") == "ruta" and ruta:
            _pantalla_ruta(d, run, canal, ruta, estados, caso)
        else:
            _pantalla_situacion(d, run, canal, ruta, estados)
    with der:
        _asistente(d, run, canal, ctx)
        _permisos(run, canal, caso)
        _historial(caso)
