"""Revisa Datos personales con Chrome sobre una app local en ejecución.

Ejecutar: python scripts/verificar_datos_personales.py [http://localhost:8511]
Solo usa el perfil y la clave de demostración; no carga archivos ni cambia datos.
"""

import sys
import tempfile
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8511"
    output = Path(tempfile.mkdtemp(prefix="datos-personales-"))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.set_default_timeout(60000)
        page.goto(url)
        page.get_by_text("Mi Gobierno", exact=True).first.click()
        field = page.get_by_label("RUN", exact=True)
        field.wait_for()
        field.fill(field.get_attribute("placeholder").removeprefix("Ej: "))
        page.get_by_label("ClaveÚnica", exact=True).fill("demo2026")
        page.get_by_role("button", name="Ingresar a Mi Gobierno", exact=True).click()
        page.get_by_text("Datos personales", exact=True).click()
        page.locator(".gov-id-card").wait_for()
        consent = page.get_by_role("checkbox", name="Acepto el acompañamiento", exact=False)
        if consent.count():
            consent.check()
            page.get_by_role("button", name="Activar Mi Gobierno", exact=True).click()
        root = page.locator(".st-key-gov_personal_page")
        expect(root.locator('[class*="st-key-gov_document_slot_"]')).to_have_count(9)
        for width in (1440, 900, 390):
            page.set_viewport_size({"width": width, "height": 1000})
            page.wait_for_timeout(800)
            result = root.evaluate("""el => ({
                width: el.clientWidth, scroll: el.scrollWidth,
                font: getComputedStyle(el).fontFamily,
                cards: el.querySelectorAll('[class*="st-key-gov_document_slot_"]').length
            })""")
            assert result["scroll"] <= result["width"] + 1, result
            assert "Roboto" in result["font"], result
            assert result["cards"] == 9, result
            card = root.locator(".gov-id-card").evaluate("""el => ({
                width: el.clientWidth, scroll: el.scrollWidth,
                background: getComputedStyle(el).backgroundImage
            })""")
            assert card["scroll"] <= card["width"] + 1, card
            assert card["background"] == "none", card
            tiles = root.locator('[class*="st-key-gov_document_slot_"]')
            assert tiles.evaluate_all("""els => els.every(el => {
                const s = getComputedStyle(el);
                return s.borderTopColor === 'rgb(220, 230, 238)' &&
                    s.backgroundColor === 'rgb(255, 255, 255)';
            })"""), "Los documentos deben usar bordes y fondos neutros"
            assert tiles.evaluate_all("""els => els.every(el => {
                let borders = 0;
                let node = el;
                while (node && node.dataset.testid !== 'stColumn') {
                    if (parseFloat(getComputedStyle(node).borderTopWidth) > 0) borders++;
                    node = node.parentElement;
                }
                return borders === 1;
            })"""), "Cada documento debe tener un solo marco"
            for summary in root.locator('[data-testid="stExpander"] summary').all():
                if not summary.evaluate("el => el.parentElement.open"):
                    summary.click()
            page.locator('[data-testid="stMain"]').evaluate("el => el.scrollTop = 0")
            page.screenshot(path=str(output / f"datos-{width}.png"), full_page=True)
            tiles.first.scroll_into_view_if_needed()
            page.screenshot(path=str(output / f"documentos-{width}.png"))
            print(f"{width}px: tipografía, 9 documentos y ancho OK", flush=True)
        browser.close()
    print(f"Capturas: {output}")


if __name__ == "__main__":
    main()
