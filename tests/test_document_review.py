import importlib
import sqlite3
from pathlib import Path

import pytest

from src.app.ruta import casos, config, government
from src.app.ruta import reglas as rules
from src.app.ruta.datos import cargar_perfiles

REVIEWER = "ejecutivo.rm@example.com"
KIND = "Cédula de identidad"


@pytest.fixture
def citizen(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "documents.db")
    profile = next(p for p in cargar_perfiles().values() if rules.diagnosticar(p).vivo)
    run = profile["run"]
    casos.responder_invitacion(run, True, "Web")
    casos.autorizar(run, True, "Web")
    return run, profile


def test_document_review_lifecycle_and_eligibility(citizen):
    run, profile = citizen
    original = rules.diagnosticar(profile).to_dict()
    assert government.document_status_label(None) == "Pendiente"
    government.save_document(run, KIND, "demo.pdf", b"%PDF-1.4 demo")
    received = government.list_documents(run)[0]
    assert received["status"] == "recibido"
    assert received["validated_by"] is None and received["validated_at"] is None
    government.validate_document(run, KIND, REVIEWER)
    validated = government.list_documents(run)[0]
    assert validated["status"] == "validado"
    assert validated["validated_by"] == REVIEWER and validated["validated_at"]
    government.validate_document(run, KIND, "social.rm@example.com")
    assert government.list_documents(run)[0] == validated
    events = casos.obtener_caso(run)["eventos"]
    assert sum(e["tipo"] == "documento_validado" for e in events) == 1
    assert rules.diagnosticar(profile).to_dict() == original
    assert not casos.obtener_caso(run)["completados"]
    government.save_document(run, KIND, "nuevo.pdf", b"%PDF-1.4 nuevo")
    assert government.list_documents(run)[0]["status"] == "recibido"
    government.validate_document(run, KIND, REVIEWER)
    government.delete_document(run, KIND)
    assert government.list_documents(run) == []
    assert government.document_status_label(None) == "Pendiente"


def test_old_database_migrates_without_losing_upload(citizen):
    run, _ = citizen
    with sqlite3.connect(config.DB_PATH) as db:
        db.execute(
            "CREATE TABLE government_documents (run TEXT, kind TEXT, name TEXT, "
            "size INTEGER, digest TEXT, content BLOB, PRIMARY KEY(run,kind))"
        )
        db.execute(
            "INSERT INTO government_documents VALUES (?,?,?,?,?,?)",
            (run, KIND, "antiguo.pdf", 5, "old-digest", b"%PDF-"),
        )
    assert government.list_documents(run)[0]["status"] == "recibido"
    government.validate_document(run, KIND, REVIEWER)
    with sqlite3.connect(config.DB_PATH) as db:
        assert db.execute("SELECT content FROM government_documents").fetchone()[0] == b"%PDF-"
    assert government.list_documents(run)[0]["name"] == "antiguo.pdf"


def test_review_requires_document_officer_and_consent(citizen):
    run, _ = citizen
    with pytest.raises(ValueError):
        government.validate_document(run, KIND, REVIEWER)
    government.save_document(run, KIND, "demo.pdf", b"%PDF-1.4 demo")
    with pytest.raises(PermissionError):
        government.validate_document(run, KIND, "citizen@example.com")
    casos.autorizar(run, False, "Web")
    with pytest.raises(PermissionError):
        government.validate_document(run, KIND, REVIEWER)


def test_officer_validates_in_ficha_and_citizen_sees_status(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    app_dir = Path(__file__).resolve().parents[1] / "src/app"
    monkeypatch.syspath_prepend(str(app_dir))
    settings = importlib.import_module("ruta.config")
    case_store = importlib.import_module("ruta.casos")
    docs = importlib.import_module("ruta.government")
    monkeypatch.setattr(settings, "DB_PATH", tmp_path / "ui-docs.db")
    profiles = importlib.import_module("ruta.datos").cargar_perfiles()
    diagnosis = importlib.import_module("ruta.reglas").diagnosticar
    run = next(r for r, p in profiles.items() if diagnosis(p).vivo)
    case_store.responder_invitacion(run, True, "Web")
    case_store.autorizar(run, True, "Web")
    docs.save_document(run, KIND, "demo.pdf", b"%PDF-1.4 demo")
    app = AppTest.from_string(
        "from ruta.datos import cargar_perfiles\n"
        "from ruta.reglas import diagnosticar\n"
        "import ui_ficha\n"
        f"p = cargar_perfiles()[{run!r}]\n"
        f"ui_ficha.render({{{run!r}: diagnosticar(p)}})\n",
        default_timeout=30,
    )
    app.session_state["staff_authenticated_user"] = REVIEWER
    app.run()
    assert not app.exception
    app.button(key=f"ficha_validate_{run}_{KIND}").click().run()
    assert not app.exception
    assert any("Validado por ChileAtiende" in c.value for c in app.caption)
    assert not any(b.label == "Marcar validado" for b in app.button)
    citizen_ui = AppTest.from_string(
        "import ui_government\n"
        f"ui_government._document_tiles({run!r}, ({ascii(KIND)},), 'personal')\n"
    ).run()
    assert not citizen_ui.exception
    assert any("Validado por ChileAtiende" in m.value for m in citizen_ui.markdown), [
        m.value for m in citizen_ui.markdown
    ]
    next(b for b in citizen_ui.button if b.label == "Eliminar").click().run()
    assert not citizen_ui.exception
    assert docs.list_documents(run) == []
    assert any("Pendiente" in m.value for m in citizen_ui.markdown), [
        m.value for m in citizen_ui.markdown
    ]
