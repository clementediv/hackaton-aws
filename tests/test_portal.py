import importlib
from pathlib import Path

import pytest

from src.app.ruta.chatbot import answer


def test_chatbot_reads_deterministic_route_with_shared_agent():
    context = {
        "autorizado": True,
        "run": "100000001-5",
        "nombre": "Luis",
        "pgu": {"resultado_orientativo": "antecedente_faltante"},
        "proximo_paso": "Actualizar RSH",
    }

    class FakeClient:
        def __init__(self):
            self.requests = []

        def converse(self, messages, **options):
            self.requests.append((messages.copy(), options))
            if len(self.requests) == 1:
                return {
                    "stopReason": "tool_use",
                    "output": {
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "toolUse": {
                                        "toolUseId": "read",
                                        "name": "leer_caso",
                                        "input": {},
                                    }
                                }
                            ],
                        }
                    },
                }
            result = messages[-1]["content"][0]["toolResult"]["content"][0]["json"]
            assert result["ok"]
            assert result["data"]["context"] == context
            assert "fuente_url" in result["data"]
            return {
                "stopReason": "end_turn",
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "Próximo paso: actualizar RSH."}],
                    }
                },
            }

    client = FakeClient()
    assert "actualizar RSH" in answer("¿Qué hago?", context, [], client=client)
    assert len(client.requests) == 2
    names = [entry["toolSpec"]["name"] for entry in client.requests[0][1]["toolConfig"]["tools"]]
    assert names == ["leer_caso"]


def test_chatbot_does_not_create_a_client_without_authorization(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("No se debe crear cliente AWS sin autorización")

    monkeypatch.setattr("src.app.ruta.chatbot.BedrockClient.from_env", forbidden)
    with pytest.raises(PermissionError):
        answer("Mi ruta", {"autorizado": False}, [])


def test_portal_navigation_search_and_official_links(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    config = importlib.import_module("ruta.config")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "portal.db")
    monkeypatch.setattr(config, "BEDROCK_MODEL_ID", "")
    app = AppTest.from_file(str(app_dir / "app.py"), default_timeout=20).run()
    assert not app.exception
    app.radio(key="portal_section").set_value("Inicio").run()
    assert not app.exception
    search = next(field for field in app.text_input if field.label == "¿Qué trámite necesitas?")
    search.set_value("certificados")
    next(button for button in app.button if button.label == "Buscar").click().run()
    assert app.session_state["portal_query"] == "certificados"
    assert not app.exception
    assert "Trámites" not in app.radio(key="portal_section").options
    assert "Mi ruta" not in app.radio(key="portal_section").options
    app.radio(key="portal_section").set_value("Inicio").run()
    assert not any(field.label == "Describe lo que necesitas" for field in app.text_input)
    app.button(key="home_government_access").click().run()
    assert not app.exception
    assert app.session_state["portal_section"] == "Mi Gobierno"
    assert any(button.label == "Ingresar a Mi Gobierno" for button in app.button)
    app.radio(key="portal_section").set_value("Ayuda para tus trámites").run()
    assert not app.exception
    assert any(button.label == "Sí, quiero que me acompañen" for button in app.button)
