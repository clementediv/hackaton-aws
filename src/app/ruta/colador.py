"""Persistent deterministic contact funnel. All deliveries are simulated.

Business source: docs/arquitectura/contacto-y-campanas.md. Durations and
probabilities below are demo policy, not institutional deadlines/statistics.
"""

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date, datetime, time, timedelta
from pathlib import Path

from . import config, reglas
from .casos import ESQUEMA
from .contacto import Contact, stable_random
from .geografia import with_simulated_location

STAGES = {1: "Email", 2: "Llamada", 3: "Trabajo", 4: "Presencial"}
ACTIVE = "active"
CONTACTED = "contacted"
STARTED = "started"
DECLINED = "declined"
SCHEMA = """
CREATE TABLE IF NOT EXISTS funnel_clock (
 id INTEGER PRIMARY KEY CHECK(id=1), now TEXT NOT NULL, start TEXT NOT NULL, seed INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS funnel_people (
 run TEXT PRIMARY KEY, name TEXT NOT NULL, age INTEGER NOT NULL, reason TEXT NOT NULL,
 contact TEXT NOT NULL, stage INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'active',
 entered_at TEXT NOT NULL, next_at TEXT, attempts INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS funnel_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT NOT NULL, at TEXT NOT NULL,
 stage INTEGER NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS funnel_due ON funnel_people(status,next_at);
"""


class Funnel:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else Path(config.DB_PATH)

    @contextmanager
    def _transaction(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        try:
            con.executescript(ESQUEMA + SCHEMA)
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    @staticmethod
    def _clock(con):
        row = con.execute("SELECT * FROM funnel_clock WHERE id=1").fetchone()
        if row is None:
            raise ValueError("Primero inicializa el embudo.")
        return row

    @staticmethod
    def _event(con, run, at, stage, kind, **detail):
        payload = json.dumps({"simulated": True, **detail}, ensure_ascii=False)
        con.execute(
            "INSERT INTO funnel_events(run,at,stage,kind,detail) VALUES(?,?,?,?,?)",
            (run, at.isoformat(), stage, kind, payload),
        )
        con.execute("INSERT OR IGNORE INTO casos(run) VALUES(?)", (run,))
        con.execute(
            "INSERT INTO eventos(run,fecha,canal,tipo,detalle) VALUES(?,?,?,?,?)",
            (run, at.isoformat(), STAGES[stage], f"colador_{kind}", payload),
        )

    def initialize(
        self,
        profiles: dict[str, dict],
        contacts: dict[str, Contact],
        *,
        reference_date: date = config.FECHA_REFERENCIA,
        seed: int = 20261008,
        simulate: bool = False,
    ) -> dict:
        """Detect candidates with the existing rules and enqueue each at email.

        Idempotent for an existing RUN. No invitations, permissions or progress
        are reset. Missing contact channels are explicitly logged and skipped.
        """
        start = datetime.combine(reference_date, time(9))
        with self._transaction() as con:
            current = con.execute("SELECT * FROM funnel_clock WHERE id=1").fetchone()
            if current and (current["seed"] != seed or current["start"] != start.isoformat()):
                raise ValueError("La campaña existente tiene otra semilla/fecha; usa otra base.")
            con.execute(
                "INSERT OR IGNORE INTO funnel_clock VALUES(1,?,?,?)",
                (start.isoformat(), start.isoformat(), seed),
            )
            now = datetime.fromisoformat(self._clock(con)["now"])
            for run, profile in sorted(profiles.items()):
                diagnosis = reglas.diagnosticar(profile, reference_date)
                if not diagnosis.invitar or not diagnosis.vivo:
                    continue
                contact = contacts.get(run)
                if contact is None:
                    raise ValueError(f"Falta contacto para {run}.")
                if contact.run != run:
                    raise ValueError("El RUN del contacto no coincide con la persona.")
                if not contact.synthetic:
                    raise ValueError("Este backend demo solo admite contactos sintéticos.")
                existing = con.execute("SELECT * FROM funnel_people WHERE run=?", (run,)).fetchone()
                if existing:
                    known = {existing["reason"]} | {
                        json.loads(event["detail"])["reason"]
                        for event in con.execute(
                            "SELECT detail FROM funnel_events WHERE run=? AND kind='signal'", (run,)
                        )
                    }
                    if diagnosis.razon_invitacion not in known:
                        self._event(
                            con,
                            run,
                            now,
                            existing["stage"],
                            "signal",
                            reason=diagnosis.razon_invitacion,
                        )
                    continue
                con.execute(
                    "INSERT INTO funnel_people(run,name,age,reason,contact,stage,entered_at) "
                    "VALUES(?,?,?,?,?,1,?)",
                    (
                        run,
                        diagnosis.nombre,
                        diagnosis.hitos.edad,
                        diagnosis.razon_invitacion,
                        json.dumps(asdict(contact), ensure_ascii=False),
                        now.isoformat(),
                    ),
                )
                con.execute("INSERT OR IGNORE INTO casos(run) VALUES(?)", (run,))
                person = con.execute("SELECT * FROM funnel_people WHERE run=?", (run,)).fetchone()
                if not self._sync_case(con, person, now):
                    self._enter(con, run, 1, now, seed, simulate)
        return self.snapshot()

    def _terminal(self, con, person, status, now, reason):
        if person["status"] == status:
            return
        con.execute(
            "UPDATE funnel_people SET status=?, next_at=NULL WHERE run=?", (status, person["run"])
        )
        if status == DECLINED:
            con.execute(
                "UPDATE casos SET invitacion='rechazado',autorizacion=0,fecha_autorizacion=NULL "
                "WHERE run=?",
                (person["run"],),
            )
        self._event(con, person["run"], now, person["stage"], status, reason=reason)

    def _sync_case(self, con, person, now) -> bool:
        """Confirmed response stops outreach; procedure initiation is tracked separately."""
        case = con.execute("SELECT invitacion FROM casos WHERE run=?", (person["run"],)).fetchone()
        if case and case["invitacion"] == "rechazado":
            self._terminal(con, person, DECLINED, now, "Rechazo registrado en el caso")
            return True
        progress = con.execute(
            "SELECT 1 FROM pasos WHERE run=? AND paso_id IN ('G1','J2') UNION ALL "
            "SELECT 1 FROM eventos WHERE run=? AND tipo='tramite_iniciado' LIMIT 1",
            (person["run"], person["run"]),
        ).fetchone()
        if progress and person["status"] in {ACTIVE, CONTACTED}:
            self._terminal(con, person, STARTED, now, "Inicio registrado en el caso")
            return True
        answered = con.execute(
            "SELECT 1 FROM funnel_events WHERE run=? AND kind IN ('answered','contacted') LIMIT 1",
            (person["run"],),
        ).fetchone()
        if person["status"] == ACTIVE and ((case and case["invitacion"] == "aceptado") or answered):
            self._terminal(
                con, person, CONTACTED, now, "Respuesta/aceptación confirmada: fin del contacto"
            )
            return True
        return person["status"] != ACTIVE

    def _enter(self, con, run, stage, now, seed, simulate):
        con.execute(
            "UPDATE funnel_people SET stage=?,entered_at=?,attempts=0,next_at=NULL WHERE run=?",
            (stage, now.isoformat(), run),
        )
        self._event(con, run, now, stage, "entered", label=STAGES[stage])
        person = con.execute("SELECT * FROM funnel_people WHERE run=?", (run,)).fetchone()
        contact = json.loads(person["contact"])
        channel = {1: "email", 2: "phone", 3: "employer"}.get(stage)
        if channel and not contact[channel]:
            self._event(con, run, now, stage, "skipped", reason=f"Sin {channel}")
            self._enter(con, run, stage + 1, now, seed, simulate)
            return
        if stage == 4:
            self._event(con, run, now, stage, "queued", reason="Pendiente de campaña presencial")
            return
        self._attempt(con, person, now, seed, simulate)
        refreshed = con.execute("SELECT * FROM funnel_people WHERE run=?", (run,)).fetchone()
        if refreshed["status"] == ACTIVE:
            days = 2 if stage == 2 else 7
            con.execute(
                "UPDATE funnel_people SET next_at=? WHERE run=?",
                ((now + timedelta(days=days)).isoformat(), run),
            )

    def _attempt(self, con, person, now, seed, simulate):
        attempt = person["attempts"] + 1
        con.execute("UPDATE funnel_people SET attempts=? WHERE run=?", (attempt, person["run"]))
        message = (
            "Por favor, pide a la persona que se comunique con ChileAtiende."
            if person["stage"] == 3
            else (
                "ChileAtiende te invita a preparar tu trámite. "
                "Puedes aceptar o declinar el acompañamiento."
            )
        )
        self._event(
            con,
            person["run"],
            now,
            person["stage"],
            "attempt",
            attempt=attempt,
            message=message,
            delivered=False,
        )
        con.execute(
            "UPDATE casos SET invitacion='invitado',canal_invitacion=?,fecha_invitacion=? "
            "WHERE run=? AND invitacion='no_invitado'",
            (STAGES[person["stage"]], now.isoformat(), person["run"]),
        )
        if simulate:
            draw = stable_random(seed, person["run"], person["stage"], attempt, "response").random()
            # Illustrative hypothesis: digital response decreases with age.
            rate = {1: 0.32, 2: 0.22, 3: 0.25}[person["stage"]]
            if person["stage"] == 1:
                rate = max(0.08, rate - max(0, person["age"] - 65) * 0.012)
            if draw < 0.04:
                self._terminal(con, person, DECLINED, now, "Rechazo simulado; hipótesis de demo")
            elif draw < 0.04 + rate:
                self._terminal(con, person, CONTACTED, now, "Respuesta simulada; hipótesis de demo")
                # Contact and subsequent initiation are different simulated outcomes.
                starts = stable_random(seed, person["run"], "start-after-contact").random() < 0.65
                if starts:
                    self._terminal(
                        con, person, STARTED, now, "Inicio tras contacto; hipótesis de demo"
                    )

    def advance(self, days: int = 0, *, simulate: bool = False) -> dict:
        if isinstance(days, bool) or not isinstance(days, int) or days < 0:
            raise ValueError("El avance debe ser un número entero de días no negativo.")
        with self._transaction() as con:
            clock = self._clock(con)
            now = datetime.fromisoformat(clock["now"])
            target = now + timedelta(days=days)
            for person in con.execute("SELECT * FROM funnel_people").fetchall():
                self._sync_case(con, person, now)
            while True:
                person = con.execute(
                    "SELECT * FROM funnel_people WHERE status='active' AND next_at<=? "
                    "ORDER BY next_at,run LIMIT 1",
                    (target.isoformat(),),
                ).fetchone()
                if person is None:
                    break
                due = datetime.fromisoformat(person["next_at"])
                if person["stage"] == 2:
                    self._attempt(con, person, due, clock["seed"], simulate)
                    row = con.execute(
                        "SELECT * FROM funnel_people WHERE run=?", (person["run"],)
                    ).fetchone()
                    if row["status"] != ACTIVE:
                        continue
                    if row["attempts"] < 3:
                        entered = datetime.fromisoformat(row["entered_at"])
                        con.execute(
                            "UPDATE funnel_people SET next_at=? WHERE run=?",
                            ((entered + timedelta(days=5)).isoformat(), row["run"]),
                        )
                        continue
                self._enter(con, person["run"], person["stage"] + 1, due, clock["seed"], simulate)
            con.execute("UPDATE funnel_clock SET now=? WHERE id=1", (target.isoformat(),))
        return self.snapshot()

    def respond(self, run: str, response: str) -> dict:
        if response not in {"opened", "answered", CONTACTED, STARTED, DECLINED}:
            raise ValueError("Respuesta no reconocida.")
        with self._transaction() as con:
            now = datetime.fromisoformat(self._clock(con)["now"])
            person = con.execute("SELECT * FROM funnel_people WHERE run=?", (run,)).fetchone()
            if person is None:
                raise ValueError("El RUN no está en el embudo.")
            self._sync_case(con, person, now)
            person = con.execute("SELECT * FROM funnel_people WHERE run=?", (run,)).fetchone()
            if person["status"] != ACTIVE:
                if person["status"] == response or (
                    person["status"] == CONTACTED and response == "answered"
                ):
                    return self._snapshot(con)
                if person["status"] != CONTACTED or response not in {STARTED, DECLINED}:
                    raise ValueError("El seguimiento de contacto ya terminó para esta persona.")
            if response in {CONTACTED, STARTED, DECLINED}:
                self._terminal(con, person, response, now, "Acción manual en demostración")
            elif response == "answered":
                self._event(
                    con, run, now, person["stage"], "answered", reason="Respondió al contacto"
                )
                self._terminal(con, person, CONTACTED, now, "Respuesta confirmada: no se escala")
            else:
                self._event(
                    con,
                    run,
                    now,
                    person["stage"],
                    response,
                    reason="Abrir sin responder no confirma contacto ni inicio de trámite",
                )
        return self.snapshot()

    def snapshot(self) -> dict:
        with self._transaction() as con:
            clock = con.execute("SELECT now FROM funnel_clock WHERE id=1").fetchone()
            if clock:
                now = datetime.fromisoformat(clock["now"])
                for person in con.execute("SELECT * FROM funnel_people").fetchall():
                    self._sync_case(con, person, now)
            return self._snapshot(con)

    @staticmethod
    def _snapshot(con) -> dict:
        clock = con.execute("SELECT * FROM funnel_clock WHERE id=1").fetchone()
        people = []
        for row in con.execute("SELECT * FROM funnel_people ORDER BY run"):
            person = dict(row)
            person["contact"] = with_simulated_location(
                json.loads(person["contact"]), person["run"], clock["seed"] if clock else 0
            )
            person["stage_label"] = STAGES[person["stage"]]
            person["alert_level"] = person["stage"] if person["status"] == ACTIVE else 0
            people.append(person)
        events = [
            {**dict(row), "detail": json.loads(row["detail"])}
            for row in con.execute("SELECT * FROM funnel_events ORDER BY at,id")
        ]
        funnel = []
        for stage, label in STAGES.items():
            reached = {
                event["run"]
                for event in events
                if event["stage"] == stage and event["kind"] == "entered"
            }
            attempts = [
                event for event in events if event["stage"] == stage and event["kind"] == "attempt"
            ]
            confirmed = {
                event["run"]
                for event in events
                if event["stage"] == stage and event["kind"] in {CONTACTED, STARTED, DECLINED}
            }
            funnel.append(
                {
                    "stage": stage,
                    "label": label,
                    "reached": len(reached),
                    "attempts": len(attempts),
                    "attempted": len({event["run"] for event in attempts}),
                    "skipped": len(
                        {
                            event["run"]
                            for event in events
                            if event["stage"] == stage and event["kind"] == "skipped"
                        }
                    ),
                    "confirmed": len(confirmed),
                    "active": sum(p["stage"] == stage and p["status"] == ACTIVE for p in people),
                }
            )
        return {
            "clock": dict(clock) if clock else None,
            "synthetic": True,
            "people": people,
            "events": events,
            "funnel": funnel,
            "totals": {
                "detected": len(people),
                "active": sum(p["status"] == ACTIVE for p in people),
                "contacted": sum(p["status"] == CONTACTED for p in people),
                "confirmed_contacts": sum(
                    p["status"] in {CONTACTED, STARTED, DECLINED} for p in people
                ),
                "started": sum(p["status"] == STARTED for p in people),
                "declined": sum(p["status"] == DECLINED for p in people),
                "in_person": sum(p["stage"] == 4 and p["status"] == ACTIVE for p in people),
            },
            "source": "contacto-y-campanas.md; reglas.py; dataset A sintético (2026-10-08)",
        }
