"""Seguimiento de casos en SQLite: invitación, autorización, pasos e historial por canal.

Es lo que da continuidad: la persona no vuelve a empezar al cambiar de canal.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from . import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS casos (
    run TEXT PRIMARY KEY,
    invitacion TEXT NOT NULL DEFAULT 'no_invitado',   -- no_invitado | invitado | aceptado | rechazado
    canal_invitacion TEXT,
    fecha_invitacion TEXT,
    autorizacion INTEGER NOT NULL DEFAULT 0,
    fecha_autorizacion TEXT
);
CREATE TABLE IF NOT EXISTS pasos (
    run TEXT NOT NULL,
    paso_id TEXT NOT NULL,
    fecha TEXT NOT NULL,
    canal TEXT,
    PRIMARY KEY (run, paso_id)
);
CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run TEXT NOT NULL,
    fecha TEXT NOT NULL,
    canal TEXT,
    tipo TEXT NOT NULL,
    detalle TEXT
);
"""


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def _conn():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(ESQUEMA)
        yield con
        con.commit()
    finally:
        con.close()


def _asegurar(con, run: str) -> None:
    con.execute("INSERT OR IGNORE INTO casos(run) VALUES (?)", (run,))


def registrar_evento(run: str, canal: str, tipo: str, detalle: dict | str | None = None) -> None:
    det = json.dumps(detalle, ensure_ascii=False) if isinstance(detalle, dict) else detalle
    with _conn() as con:
        _asegurar(con, run)
        con.execute("INSERT INTO eventos(run, fecha, canal, tipo, detalle) VALUES (?,?,?,?,?)",
                    (run, _ahora(), canal, tipo, det))


def invitar(runs: list[str], canal: str) -> int:
    n = 0
    with _conn() as con:
        for run in runs:
            _asegurar(con, run)
            cur = con.execute(
                "UPDATE casos SET invitacion='invitado', canal_invitacion=?, fecha_invitacion=? "
                "WHERE run=? AND invitacion='no_invitado'", (canal, _ahora(), run))
            if cur.rowcount:
                con.execute("INSERT INTO eventos(run, fecha, canal, tipo, detalle) VALUES (?,?,?,?,?)",
                            (run, _ahora(), canal, "invitacion_enviada", None))
                n += 1
    return n


def responder_invitacion(run: str, acepta: bool, canal: str) -> None:
    with _conn() as con:
        _asegurar(con, run)
        con.execute(
            "UPDATE casos SET invitacion=?, "
            "autorizacion=CASE WHEN ? THEN autorizacion ELSE 0 END, "
            "fecha_autorizacion=CASE WHEN ? THEN fecha_autorizacion ELSE NULL END WHERE run=?",
            ("aceptado" if acepta else "rechazado", acepta, acepta, run),
        )
    registrar_evento(run, canal, "invitacion_aceptada" if acepta else "invitacion_rechazada")


def autorizar(run: str, autoriza: bool, canal: str) -> None:
    with _conn() as con:
        _asegurar(con, run)
        invitation = con.execute("SELECT invitacion FROM casos WHERE run=?", (run,)).fetchone()
        if autoriza and invitation["invitacion"] != "aceptado":
            raise PermissionError("Debe aceptar el acompañamiento antes de autorizar datos.")
        con.execute("UPDATE casos SET autorizacion=?, fecha_autorizacion=? WHERE run=?",
                    (int(autoriza), _ahora() if autoriza else None, run))
    registrar_evento(run, canal, "autorizacion_otorgada" if autoriza else "autorizacion_revocada")


def completar_paso(run: str, paso_id: str, canal: str, titulo: str = "") -> None:
    with _conn() as con:
        _asegurar(con, run)
        con.execute("INSERT OR IGNORE INTO pasos(run, paso_id, fecha, canal) VALUES (?,?,?,?)",
                    (run, paso_id, _ahora(), canal))
    registrar_evento(run, canal, "paso_completado", {"paso": paso_id, "titulo": titulo})


def deshacer_paso(run: str, paso_id: str, canal: str) -> None:
    with _conn() as con:
        con.execute("DELETE FROM pasos WHERE run=? AND paso_id=?", (run, paso_id))
    registrar_evento(run, canal, "paso_reabierto", {"paso": paso_id})


def obtener_caso(run: str) -> dict:
    with _conn() as con:
        _asegurar(con, run)
        caso = dict(con.execute("SELECT * FROM casos WHERE run=?", (run,)).fetchone())
        caso["completados"] = {r["paso_id"] for r in con.execute("SELECT paso_id FROM pasos WHERE run=?", (run,))}
        caso["eventos"] = [dict(r) for r in con.execute(
            "SELECT fecha, canal, tipo, detalle FROM eventos WHERE run=? ORDER BY id", (run,))]
    return caso


def todos_los_casos() -> list[dict]:
    with _conn() as con:
        casos = [dict(r) for r in con.execute("SELECT * FROM casos")]
        pasos = {}
        for r in con.execute("SELECT run, paso_id FROM pasos"):
            pasos.setdefault(r["run"], set()).add(r["paso_id"])
        canales = {}
        for r in con.execute("SELECT run, COUNT(DISTINCT canal) n FROM eventos GROUP BY run"):
            canales[r["run"]] = r["n"]
    for c in casos:
        c["completados"] = pasos.get(c["run"], set())
        c["n_canales"] = canales.get(c["run"], 0)
    return casos


def reiniciar() -> None:
    with _conn() as con:
        for table in ("government_documents", "government_profiles", "platform_event_keys"):
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                           (table,)).fetchone():
                con.execute(f"DELETE FROM {table}")
        # The existing demo reset also clears its funnel, if initialized.
        for table in ("funnel_events", "funnel_people", "funnel_clock"):
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                           (table,)).fetchone():
                con.execute(f"DELETE FROM {table}")
        con.executescript("DELETE FROM pasos; DELETE FROM eventos; DELETE FROM casos;")
