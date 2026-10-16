"""Verifica envío, espera animada y scroll de ambos chats sin consumir Bedrock.

Ejecutar: uv run --with playwright python scripts/verificar_chat_scroll.py
Usa Chromium/Chrome local y un servidor de prueba aislado con respuesta demorada.
"""

import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROME = next((str(path) for path in (
    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
) if path.exists()), None)
HARNESS = """
import sys
import time
sys.path.insert(0, APP_DIR)
import streamlit as st
import portal
import ui_persona
from ruta import asistente, casos
st.set_page_config(layout="wide")
def answer(q, *args, **kwargs):
    time.sleep(2.5)
    text = "Respuesta de prueba. " * 80 + "\\n\\nFin de respuesta: " + q
    return (iter([text]) if kwargs.get("stream") else text), "plantillas"
asistente.responder_publico = answer
asistente.responder = answer
asistente.explicar_resumen = lambda ctx: "Hola. ¿En qué te ayudo?"
casos.registrar_evento = lambda *args, **kwargs: None
mode = st.radio("Vista", ["Público", "Mi Gobierno"])
if mode == "Público":
    st.session_state["portal_home_page"] = st.Page(lambda: None, title="Inicio")
    portal.render_chat_page()
else:
    st.markdown('<style>' + (ui_persona.Path(APP_DIR) / 'assets/government.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)
    with st.container(key="gov_assistant"):
        ui_persona._asistente(None, "test", "web", {"autorizado": True, "nombre": "Demo"},
                             sidebar=True)
""".replace("APP_DIR", repr(str(ROOT / "src/app")))

SCROLL_STATE = """e => {
  let node = e;
  while (node) {
    if (/(auto|scroll)/.test(getComputedStyle(node).overflowY)) {
      return {top: node.scrollTop, remaining: node.scrollHeight-node.clientHeight-node.scrollTop};
    }
    node = node.parentElement;
  }
  throw Error('No se encontró el contenedor con scroll');
}"""


def verify(page, mode):
    alignment_only = "--alignment-only" in sys.argv
    if mode == "Mi Gobierno":
        page.get_by_role("radiogroup", name="Vista", exact=True).get_by_text(mode, exact=True).click()
    prompt = "Describe lo que necesitas"
    for turn in range(2):
        question = f"Consulta {turn}"
        composer = page.locator(".st-key-gov_assistant") if mode == "Mi Gobierno" else page
        field = composer.get_by_placeholder(prompt)
        field.fill(question)
        page_scroll = """() => [...document.querySelectorAll('section')]
            .reduce((sum, e) => sum + e.scrollTop, 0)"""
        outer_scroll = page.evaluate(page_scroll)
        field.press("Enter")
        dots = page.locator(".chat-typing")
        dots.wait_for()
        assert dots.locator("span").count() == 3
        assert page.locator('[data-testid="stChatMessage"]').nth(0).is_visible()
        assert page.locator('[data-testid="stChatMessage"]').filter(has_text=question).count() == 1
        assert dots.locator("span").evaluate_all(
            "els => els.map(e => getComputedStyle(e).animationDelay)"
        ) == ["0s", "0.16s", "0.32s"]
        page.wait_for_timeout(350)
        if mode == "Mi Gobierno":
            assert abs(page.evaluate(page_scroll) - outer_scroll) < 4
            bubble = page.locator('[data-testid="stChatMessage"]').filter(has_text=question)
            assert bubble.evaluate("""e => {
                const wrapper = e.closest('[class*=st-key-gov_chat_user_]');
                return wrapper && getComputedStyle(wrapper).alignSelf === 'flex-end';
            }"""), "Pregunta sin alineacion derecha durante espera"
        if not alignment_only:
            assert dots.evaluate(SCROLL_STATE)["remaining"] < 4
        page.get_by_text(f"Fin de respuesta: {question}", exact=False).wait_for()
        dots.wait_for(state="detached")
        page.wait_for_timeout(1400)
        last = page.locator('[data-testid="stChatMessage"]').last
        alignment = last.evaluate("""e => {
          const avatar = e.querySelector('[data-testid="stChatMessageAvatarAssistant"]');
          const text = e.querySelector('[data-testid="stMarkdownContainer"] p');
          return Math.abs(avatar.getBoundingClientRect().top - text.getBoundingClientRect().top);
        }""")
        assert alignment < 4, f"Respuesta nueva desalineada: {alignment}px"
        if not alignment_only:
            assert last.evaluate(SCROLL_STATE)["remaining"] < 4
        box = last.bounding_box()
        if not alignment_only:
            assert 0 < box["y"] + box["height"] < page.viewport_size["height"]
    # Once the new message settles, reading older messages must remain possible.
    if alignment_only:
        return
    last.evaluate("""e => { for(let n=e;n;n=n.parentElement) {
      if (/(auto|scroll)/.test(getComputedStyle(n).overflowY)) n.scrollTop=0;
    }}""")
    page.wait_for_timeout(1400)
    assert last.evaluate(SCROLL_STATE)["top"] == 0


def main():
    with tempfile.TemporaryDirectory(prefix="chat-scroll-", ignore_cleanup_errors=True) as tmp:
        harness = Path(tmp) / "app.py"
        harness.write_text(HARNESS, encoding="utf-8")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with (Path(tmp) / "server.log").open("w") as log:
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(harness),
                    "--server.port",
                    str(port),
                    "--server.headless",
                    "true",
                ],
                cwd=ROOT,
                stdout=log,
                stderr=log,
            )
            try:
                url = f"http://localhost:{port}"
                for _ in range(100):
                    try:
                        with urlopen(url + "/_stcore/health", timeout=1):
                            break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("No inició el servidor de prueba")
                with sync_playwright() as p:
                    browser = p.chromium.launch(executable_path=CHROME, headless=True)
                    for width in (390, 1440):
                        for mode in ("Público", "Mi Gobierno"):
                            page = browser.new_page(viewport={"width": width, "height": 760})
                            page.goto(url)
                            verify(page, mode)
                            assert page.locator('[data-testid="stException"]').count() == 0
                            print(
                                f"OK {mode}, {width}px: alineación de dos respuestas nuevas"
                            )
                            page.close()
                    browser.close()
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
