import importlib
from pathlib import Path

import pytest


def test_citizen_can_accept_authorize_and_revoke_without_stale_chat(tmp_path, monkeypatch):
    pytest.importorskip("streamlit", reason="Instalar el grupo app para verificar la UI")
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "ui-cases.db")
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=20).run()
    assert not app.exception

    def click(label):
        next(button for button in app.button if button.label == label).click().run()
        assert not app.exception

    app.radio(key="portal_section").set_value("Mi Gobierno").run()
    run = app.selectbox(key="gov_demo_example").value
    app.text_input(key="gov_login_rut").set_value(run)
    app.text_input(key="gov_login_password").set_value("demo2026")
    click("Ingresar a Mi Gobierno")
    app.checkbox(key=f"gov_consent_{run}").check().run()
    click("Activar Mi Gobierno")
    app.chat_input[0].set_value("¿Cuánto recibiría?").run()
    histories = [
        app.session_state[key]
        for key in app.session_state.filtered_state
        if key.startswith("chat-")
    ]
    assert any(len(history) > 1 for history in histories)
    app.radio(key=f"government_view_{run}").set_value("Datos personales").run()
    app.button(key=f"gov_revoke_{run}").click().run()
    app.button(key=f"gov_revoke_confirm_{run}").click().run()
    assert not app.exception
    histories = [
        app.session_state[key]
        for key in app.session_state.filtered_state
        if key.startswith("chat-")
    ]
    assert all(len(history) == 1 for history in histories)
    assert all("autorización" in history[0]["texto"] for history in histories)


def test_requirement_videos_play_inside_their_own_box(tmp_path, monkeypatch):
    pytest.importorskip("streamlit", reason="Instalar el grupo app para verificar la UI")
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "ui-videos.db")
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=30).run()
    app.radio(key="portal_section").set_value("Mi Gobierno").run()
    run = app.selectbox(key="gov_demo_example").value
    app.text_input(key="gov_login_rut").set_value(run)
    app.text_input(key="gov_login_password").set_value("demo2026")
    next(b for b in app.button if b.label == "Ingresar a Mi Gobierno").click().run()
    app.checkbox(key=f"gov_consent_{run}").check().run()
    next(b for b in app.button if b.label == "Activar Mi Gobierno").click().run()
    assert not app.exception

    videos = []  # ancestors of every video, outermost first

    def walk(node, ancestors):
        for child in getattr(node, "children", {}).values():
            if child.type == "video":
                videos.append(ancestors)
            else:
                walk(child, ancestors + [(child.type, getattr(child.proto, "id", ""))])

    walk(app._tree, [])
    assert videos
    for ancestors in videos:
        assert "popover" not in [kind for kind, _ in ancestors]  # no longer a pop-up
        assert "gov_video_" in ancestors[-1][1] and "gov_requirement_" in ancestors[-2][1]
