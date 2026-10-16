"""Verifica el movimiento del home con sus estilos y contenido reales.

Ejecutar: python scripts/verificar_animaciones_home.py
Requiere Playwright y Chrome. No usa AWS ni modifica datos de la aplicación.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ASSETS = Path(__file__).resolve().parents[1] / "src/app/assets"


def main():
    styles = "\n".join(
        (ASSETS / name).read_text(encoding="utf-8")
        for name in ("official-home.css", "portal.css", "motion.css")
    )
    content = (ASSETS / "official-home.html").read_text(encoding="utf-8")
    content = content.split("</section>", 1)[1]
    intro = """
    <div class="home-assistant-intro">
      <h1>Prueba el asistente de inteligencia artificial de ChileAtiende</h1>
      <p>Encuentra tu próximo paso en trámites y beneficios del Estado.</p>
    </div>
    <div class="st-key-home_chat_preview"><input placeholder="Describe lo que necesitas"></div>
    """
    markup = (
        "<style>body{margin:0} main.stApp{padding:0 16px;box-sizing:border-box} "
        ".home-assistant-intro{padding:36px 18px} "
        ".st-key-home_chat_preview{margin:0 18px 40px}</style>"
        f"<style>{styles}</style><main class='stApp'>{intro}"
        f"<div class='official-home'>{content}</div></main>"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        for width in (390, 1440):
            for motion in ("no-preference", "reduce"):
                page = browser.new_page(
                    viewport={"width": width, "height": 900}, reduced_motion=motion
                )
                page.set_content(markup)
                title = page.locator(".home-assistant-intro h1")
                name = title.evaluate("el => getComputedStyle(el).animationName")
                assert name == ("none" if motion == "reduce" else "home-enter"), name
                page.wait_for_timeout(1000)
                assert title.evaluate("el => getComputedStyle(el).transform") == "none"
                assert title.evaluate("el => getComputedStyle(el).opacity") == "1"
                cards = page.locator(".official-home .card-link")
                assert cards.count() > 0
                card = cards.first
                card.scroll_into_view_if_needed()
                page.wait_for_timeout(400)
                assert card.is_visible()
                column = card.locator("xpath=ancestor::div[contains(@class,'column')][1]")
                assert column.evaluate("el => getComputedStyle(el).opacity") == "1"
                if motion == "no-preference" and width == 1440:
                    card.hover()
                    page.wait_for_timeout(300)
                    y = card.evaluate("el => new DOMMatrix(getComputedStyle(el).transform).m42")
                    assert y == -3, y
                if motion == "reduce":
                    assert page.locator(".official-home").evaluate("""el =>
                        el.getAnimations({subtree: true}).length === 0""")
                card.focus()
                assert card.evaluate("el => el === document.activeElement")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                    page.locator("body *").evaluate_all("""els => els.filter(el =>
                        el.getBoundingClientRect().right > innerWidth + 1).slice(0,8)
                        .map(el => [el.className, el.getBoundingClientRect().right])""")
                )
                print(f"OK {width}px / {motion}: entradas, tarjetas, teclado y ancho")
                page.close()
        browser.close()


if __name__ == "__main__":
    main()
