"""Comprueba entradas de Mi Gobierno: escritorio, móvil y movimiento reducido.

Ejecutar: .venv/Scripts/python.exe scripts/verificar_animaciones_gobierno.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "src/app/assets/motion.css").read_text(encoding="utf-8")
CHROME = next((str(p) for p in (
    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
) if p.exists()), None)
HTML = """
<main class="stApp">
  <div class="st-key-gov_subnav">Beneficios / Datos personales</div>
  <div class="st-key-gov_benefits_layout">
    <div class="st-key-gov_pgu">PGU
      <div class="gov-timeline-step">Postulación</div>
      <div class="gov-timeline-step">Revisión</div>
      <div class="gov-timeline-step">Resultado</div>
    </div>
    <div class="st-key-gov_benefit_fuas">FUAS</div>
    <div class="st-key-gov_benefit_gratuidad">Gratuidad</div>
    <div class="st-key-gov_benefit_becas">Becas</div>
    <div class="st-key-gov_chat_page"><div class="st-key-gov_assistant">Asistente</div></div>
  </div>
  <div class="st-key-gov_personal_page">
    <div class="gov-identity">Identidad</div>
    <div data-testid="stExpander">Documentos</div>
  </div>
</main>
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        for width in (390, 1440):
            for reduced in ("no-preference", "reduce"):
                page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion=reduced)
                page.set_content("<style>" + CSS + "</style>" + HTML)
                cards = page.locator('.st-key-gov_benefits_layout > [class*="st-key-gov_"]:not(.st-key-gov_chat_page)')
                delays = cards.evaluate_all("els => els.map(e => getComputedStyle(e).animationDelay)")
                if reduced == "no-preference":
                    assert delays == ["0.07s", "0.14s", "0.21s", "0.28s"], delays
                    assert page.locator('.st-key-gov_assistant').evaluate(
                        "e => getComputedStyle(e).animationName"
                    ) == "government-enter"
                else:
                    assert cards.evaluate_all("els => els.every(e => getComputedStyle(e).animationName === 'none')")
                page.wait_for_timeout(1000)
                assert cards.evaluate_all("els => els.every(e => getComputedStyle(e).opacity === '1' && getComputedStyle(e).transform === 'none')")
                assert page.locator('.st-key-gov_chat_page').evaluate("e => getComputedStyle(e).transform") == 'none'
                # A normal content update must not restart surface entrances.
                page.locator('.st-key-gov_assistant').evaluate("e => e.textContent = 'Nueva respuesta'")
                assert page.locator('.stApp').evaluate("e => e.getAnimations({subtree:true}).length") == 0
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                print(f"OK {width}px, {reduced}: secuencia, fin sin transform y actualización sin repetición")
                page.close()
        browser.close()


if __name__ == "__main__":
    main()
