"""Inspecciona los detalles en la app completa: python scripts/verificar_detalles_pantalla.py."""
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width':1440,'height':1000})
        page.goto('http://localhost:8501')
        page.get_by_text('Mi Gobierno', exact=True).first.click()
        field = page.get_by_label('RUN', exact=True)
        field.wait_for()
        field.fill(field.get_attribute('placeholder').removeprefix('Ej: '))
        page.get_by_label('ClaveÚnica', exact=True).fill('demo2026')
        page.get_by_role('button', name='Ingresar a Mi Gobierno', exact=True).click()
        consent = page.get_by_role('checkbox', name='Acepto el acompañamiento', exact=False)
        page.wait_for_timeout(1200)
        if consent.count():
            consent.check()
            page.get_by_role('button', name='Activar Mi Gobierno', exact=True).click()
        page.locator('.st-key-gov_pgu').wait_for()
        for expander in page.locator('.st-key-gov_benefits_layout [data-testid="stExpander"] summary').all():
            if not expander.evaluate('e => e.parentElement.open'):
                expander.click()
        page.wait_for_timeout(1200)
        for width in (1440,900,390):
            page.set_viewport_size({'width':width,'height':1000})
            page.wait_for_timeout(900)
            rows = page.locator('.gov-requirement-card').evaluate_all('''els => els.map(e => {
              const rect = x => {if(!x)return null;const b=x.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height}};
              const outer=e.closest('[class*="st-key-gov_requirement_"]')||e;
              return {title:e.querySelector('strong').textContent,card:rect(e),outer:rect(outer),text:rect(e.querySelector('div')),html:rect(e.closest('[data-testid="stHtml"]')), parent:rect(e.parentElement),padding:getComputedStyle(e).padding};
            })''')
            assert len(rows) >= 5, 'No se encontraron todos los requisitos PGU'
            for row in rows:
                assert row['html'] is not None, f"Servidor con render anterior: {row['title']}"
                text, card = row['text'], row['card']
                assert abs(text['x']+text['width']/2-card['x']-card['width']/2) < 1
                assert abs(text['y']+text['height']/2-card['y']-card['height']/2) < 1
                assert card['width'] <= row['outer']['width']
                # Completed requirements have no auxiliary controls below the text.
                if row['outer']['height'] < card['height']+3:
                    outer=row['outer']
                    assert abs(text['y']+text['height']/2-outer['y']-outer['height']/2) < 1
            print(f'{width}px: {len(rows)} detalles con HTML actualizado y texto centrado',flush=True)
            path=Path(tempfile.gettempdir())/f'detalles-pantalla-{width}.png'
            page.locator('.gov-requirement-card').first.scroll_into_view_if_needed()
            page.screenshot(path=str(path),full_page=True)
            print(path,flush=True)
        browser.close()

if __name__=='__main__':
    main()
