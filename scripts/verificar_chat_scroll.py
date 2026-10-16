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
from urllib.parse import quote
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
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
asistente._template_stream = lambda text: iter([text])
asistente.explicar_resumen = lambda ctx: "Hola. ¿En qué te ayudo?"
casos.registrar_evento = lambda *args, **kwargs: None
mode = st.query_params.get("mode", "Público")
if mode == "Público":
    st.session_state["portal_home_page"] = st.Page(lambda: None, title="Inicio")
    portal.render_chat_page()
else:
    ui_persona._asistente(None, "test", "web", {"autorizado": True, "nombre": "Demo"},
                         sidebar=True)
""".replace("APP_DIR", repr(str(ROOT / "src/app")))

SCROLL_STATE = """e => {
  let node = e;
  while (node) {
    if (/(auto|scroll)/.test(getComputedStyle(node).overflowY) &&
        node.scrollHeight > node.clientHeight + 5) {
      return {top: node.scrollTop, remaining: node.scrollHeight-node.clientHeight-node.scrollTop};
    }
    node = node.parentElement;
  }
  return {top: 0, remaining: 0};
}"""


def wait_for_bottom(locator):
    """Allow layout/reruns to settle without forcing the scroll under test."""
    for _ in range(30):
        state = locator.evaluate(SCROLL_STATE)
        if state["remaining"] < 4:
            return
        locator.page.wait_for_timeout(100)
    raise AssertionError(state)


def verify(page, mode):
    container = ".st-key-public_chat" if mode == "Público" else ".st-key-personal_chat_composer"
    page.locator(container).wait_for()
    prompt = "Describe lo que necesitas"
    for turn in range(2):
        page.get_by_test_id("stStatusWidget").wait_for(state="hidden")
        question = f"Consulta {turn}"
        field = page.get_by_placeholder(prompt)
        field.fill(question)
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
        wait_for_bottom(dots)
        page.get_by_text(f"Fin de respuesta: {question}", exact=False).wait_for()
        dots.wait_for(state="detached")
        page.wait_for_timeout(1400)
        last = page.locator('[data-testid="stChatMessage"]').last
        wait_for_bottom(last)
        box = last.bounding_box()
        assert 0 < box["y"] + box["height"] < page.viewport_size["height"]
    # Once the new message settles, reading older messages must remain possible.
    last.evaluate("""e => { for(let n=e;n;n=n.parentElement) {
      if (/(auto|scroll)/.test(getComputedStyle(n).overflowY)) n.scrollTop=0;
    }}""")
    page.wait_for_timeout(1400)
    assert last.evaluate(SCROLL_STATE)["top"] == 0


def main():
    with tempfile.TemporaryDirectory(prefix="chat-scroll-") as tmp:
        harness = Path(tmp) / "app.py"
        harness.write_text(HARNESS)
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
                    "--server.address",
                    "127.0.0.1",
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
                            page.goto(url + "/?mode=" + quote(mode))
                            verify(page, mode)
                            assert page.locator('[data-testid="stException"]').count() == 0
                            print(
                                f"OK {mode}, {width}px: "
                                "envío visible, ola, scroll y lectura manual",
                                flush=True,
                            )
                            page.close()
                    browser.close()
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
