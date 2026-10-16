"""Verifica en Chrome la alineación real de recuadros de detalles Streamlit."""

import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HARNESS = """
import sys
from pathlib import Path
sys.path.insert(0, APP_DIR)
import streamlit as st
import ui_government as ui
st.set_page_config(layout='wide')
st.markdown('<style>' + (Path(APP_DIR)/'assets/government.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)
with st.container(key='gov_benefits_layout'):
    with st.container(key='gov_pgu'):
        ui._requirement_card('Resultado de la revisión', 'Según los antecedentes disponibles podría solicitar la PGU.', 'Listo para iniciar la solicitud', ready=True, summary=True)
        ui._requirement_card('Edad', 'Cumple con la edad requerida.', 'Cumple', ready=True, context='edad')
        ui._requirement_card('Residencia', 'Faltan antecedentes para revisar los años de residencia en Chile. Fuente oficial de información.', 'Falta información', ready=False, context='residencia')
        ui._requirement_card('Registro Social de Hogares', 'Antecedentes disponibles para revisar el requisito.', 'Cumple', ready=True, context='rsh')
""".replace('APP_DIR', repr(str(ROOT / 'src/app')))


def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        app = Path(tmp) / 'app.py'
        app.write_text(HARNESS, encoding='utf-8')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        server = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', str(app), '--server.port', str(port), '--server.headless', 'true'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            url = f'http://localhost:{port}'
            for _ in range(100):
                try:
                    urlopen(url+'/_stcore/health', timeout=1).close()
                    break
                except OSError:
                    time.sleep(.1)
            with sync_playwright() as p:
                browser = p.chromium.launch(channel='chrome', headless=True)
                page = browser.new_page()
                page.goto(url)
                page.locator('.gov-requirement-card').last.wait_for()
                for width in (1440, 900, 390):
                    page.set_viewport_size({'width': width, 'height': 1000})
                    page.wait_for_timeout(300)
                    result = page.locator('.gov-requirement-card').evaluate_all('''els => els.map(el => {
                      const outer = el.closest('[class*="st-key-gov_requirement_"]') || el;
                      const box = outer.getBoundingClientRect();
                      const text = el.querySelector('div').getBoundingClientRect();
                      return {title:el.querySelector('strong').textContent,
                        vertical:Math.abs((text.top+text.bottom-box.top-box.bottom)/2),
                        top:el.getBoundingClientRect().top-box.top,
                        height:box.height,
                        offset:Math.abs((text.left+text.right-box.left-box.right)/2),
                        cardWidth:el.getBoundingClientRect().width, outerWidth:box.width,
                        overflow:el.scrollWidth>el.clientWidth+1};
                    })''')
                    print(width, result, flush=True)
                    assert all(r['vertical'] < 2 and r['offset'] < 2 and abs(r['cardWidth']-r['outerWidth']) < 3 and not r['overflow'] for r in result)
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    main()
