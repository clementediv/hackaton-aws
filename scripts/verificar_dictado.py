"""Verificación de dictado en Chromium con reconocimiento simulado.

uv run --with playwright python scripts/verificar_dictado.py
El micrófono físico requiere prueba manual y permiso del navegador.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FAKE_SPEECH = """
window.componentEvents=[];
window.addEventListener('message',e=>{if(e.data.type==='streamlit:setComponentValue')
 window.componentEvents.push(e.data.value)});
class FakeSpeech {
 constructor(){window.recognitionForTest=this}
 start(){this.onstart()}
 stop(){this.onend()}
 abort(){this.onend()}
}
window.SpeechRecognition=FakeSpeech;
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 500})
        page.add_init_script(FAKE_SPEECH)
        page.goto((ROOT / "src/app/assets/voice_input/index.html").as_uri())
        page.locator("#mic").click()
        assert page.locator("#mic").get_attribute("aria-pressed") == "true"
        page.evaluate("""recognitionForTest.onresult({results:[[{transcript:'¿Qué es la PGU?'}]]});
                         recognitionForTest.onend();""")
        assert page.locator("#draft").input_value() == "¿Qué es la PGU?"
        assert page.evaluate("componentEvents.length") == 0
        page.locator("#draft").fill("¿Puedo solicitar la PGU?")
        page.screenshot(path="/tmp/chat-voice-review.png")
        page.locator("#send").click()
        page.wait_for_function("componentEvents.length === 1")
        assert page.evaluate("componentEvents[0].text") == "¿Puedo solicitar la PGU?"
        assert page.locator("#review").is_hidden()
        page.locator("#mic").click()
        page.evaluate("""recognitionForTest.onerror({error:'not-allowed'});
                         recognitionForTest.onend();""")
        assert "Permite el micrófono" in page.locator("#status").inner_text()
        assert page.evaluate("componentEvents.length") == 1
        page.locator("#mic").click()
        page.evaluate("""recognitionForTest.onresult({results:[[{transcript:'No enviar'}]]});
                         recognitionForTest.onend();""")
        page.locator("#cancel").click()
        assert page.evaluate("componentEvents.length") == 1
        assert page.locator("#review").is_hidden()
        unsupported = browser.new_page()
        unsupported.add_init_script("""Object.defineProperty(window,'SpeechRecognition',{value:null});
          Object.defineProperty(window,'webkitSpeechRecognition',{value:null});""")
        unsupported.goto((ROOT / "src/app/assets/voice_input/index.html").as_uri())
        unsupported.evaluate("window.postMessage({type:'streamlit:render',disabled:false}, '*')")
        unsupported.wait_for_function("document.getElementById('mic').disabled")
        assert "no admite dictado" in unsupported.locator("#status").inner_text()
        speech = browser.new_page()
        speech.add_init_script(
            FAKE_SPEECH
            + """
window.spokenForTest=[];window.cancelForTest=0;
window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
Object.defineProperty(window,'speechSynthesis',{value:{
 getVoices:()=>[{lang:'es-CL',name:'Español'}],
 cancel:()=>{window.cancelForTest++},
 speak:u=>{window.spokenForTest.push(u);u.onstart()}
}});
"""
        )
        speech.goto((ROOT / "src/app/assets/voice_input/index.html").as_uri())
        render = """window.postMessage({type:'streamlit:render',disabled:false,args:{
          reply_text:'Hola. Podemos revisarlo con calma.',speech_id:'reply-1',read_aloud:true}},'*')"""
        speech.evaluate(render)
        speech.wait_for_function("spokenForTest.length===1")
        assert speech.evaluate("spokenForTest[0].lang") == "es-CL"
        speech.evaluate(render)
        speech.wait_for_timeout(100)
        assert speech.evaluate("spokenForTest.length") == 1
        speech.locator("#stop-voice").click()
        assert speech.locator("#stop-voice").is_hidden()
        speech.locator("#listen").click()
        assert speech.evaluate("spokenForTest.length") == 2
        before = speech.evaluate("cancelForTest")
        speech.locator("#mic").click()
        assert speech.evaluate("cancelForTest") > before
        assert speech.locator("#stop-voice").is_hidden()
        print(
            "OK: voz española, reproducción automática optativa, no repetición y pausa al dictar."
        )
        print("OK: revisión, edición, envío único, permisos, descarte y navegador no compatible.")
        app = browser.new_page(viewport={"width": 1440, "height": 1000})
        app.add_init_script(FAKE_SPEECH)
        app.goto("http://localhost:8501/chat")
        app.wait_for_timeout(1000)
        dialog = app.get_by_role("dialog")
        if dialog.count() and "Page not found" in dialog.inner_text():
            dialog.get_by_role("button").first.click()
        frame = app.locator('iframe[title$="chat_voice_input"]')
        frame.wait_for(timeout=30000)
        assert frame.count() == 1
        assert "microphone" in frame.get_attribute("allow")
        assert app.get_by_test_id("stException").count() == 0
        app.screenshot(path="/tmp/chat-voice-app.png")
        print("OK: micrófono visible en el chat local y permiso microphone habilitado en iframe.")
        live = frame.element_handle().content_frame()
        live.locator("#mic").click()
        live.evaluate("""recognitionForTest.onresult({results:[[{transcript:'¿Qué es la PGU?'}]]});
                         recognitionForTest.onend();""")
        live.locator("#send").click()
        app.wait_for_function(
            "document.querySelectorAll('[data-testid=stChatMessage]').length===2", timeout=60000
        )
        assert (
            "Pensión Garantizada Universal" in app.get_by_test_id("stChatMessage").last.inner_text()
        )
        assert app.get_by_text("Orientación con respuestas predefinidas", exact=False).count() == 0
        app.wait_for_timeout(500)
        assert app.get_by_test_id("stChatMessage").count() == 2
        print("OK: transcripción simulada enviada una vez y respondida por Bedrock en la UI real.")
        browser.close()


if __name__ == "__main__":
    main()
