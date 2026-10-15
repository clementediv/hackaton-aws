"""Operate the proactive detection deployed on AWS (see infra/README.md).

uv run python scripts/proactivo.py cargar            # catalog + 500 people + demo people
uv run python scripts/proactivo.py evento 90000002-2 --edad 65   # star demo
uv run python scripts/proactivo.py estado 90000002-2
uv run python scripts/proactivo.py responder 90000002-2 pgu acepto --canal telefono
uv run python scripts/proactivo.py terreno
uv run python scripts/proactivo.py resumen
uv run python scripts/proactivo.py escalar | revisar  # run the scheduled Lambdas now
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import boto3
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.proactivo import carga  # noqa: E402
from src.proactivo.catalogo import BENEFICIOS  # noqa: E402
from src.proactivo.reglas import add_years  # noqa: E402
from src.proactivo.servicio import Service, Settings  # noqa: E402

FUNCTIONS = {"escalar": "ca-escalador", "revisar": "ca-revision-diaria"}


def session() -> boto3.Session:
    values = {**dotenv_values(ROOT / ".env"), **os.environ}
    return boto3.Session(
        profile_name=values.get("AWS_PROFILE") or "hackaton",
        region_name=values.get("AWS_REGION") or "us-east-1",
    )


def today() -> date:
    return (datetime.now(UTC) - timedelta(hours=3)).date()


def cmd_cargar(args, s):
    db = s.resource("dynamodb")
    with db.Table("ca-beneficios").batch_writer() as batch:
        for benefit in BENEFICIOS:
            batch.put_item(Item=benefit)
    people = carga.demo_people(args.email, today())
    if not args.solo_demo:
        contacts = carga.load_contacts()
        profiles = json.loads(carga.PROFILES.read_text(encoding="utf-8"))
        people += [carga.from_dataset(p, contacts.get(p["run"])) for p in profiles]
    with db.Table("ca-personas").batch_writer() as batch:
        for person in people:
            batch.put_item(Item=person)
    print(f"{len(BENEFICIOS)} beneficios y {len(people)} personas cargadas.")
    print("La detección corre sola en la Lambda del stream; revisa con `resumen` en unos segundos.")


def cmd_evento(args, s):
    values = {}
    if args.edad is not None:
        values["fecha_nacimiento"] = add_years(today(), -args.edad).isoformat()
    if args.nacimiento:
        values["fecha_nacimiento"] = args.nacimiento
    if args.hijos is not None:
        values["num_hijos"] = args.hijos
    if args.estado_civil:
        values["estado_civil"] = args.estado_civil
    if args.casado_desde:
        values |= {"estado_civil": "casado", "fecha_matrimonio": args.casado_desde}
    if args.accidente:
        values["accidente_laboral"] = True
    if args.tramo is not None:
        values["tramo_rsh"] = args.tramo
    if args.trabaja is not None:
        values["trabaja"] = args.trabaja == "si"
    if not values:
        sys.exit("Indica al menos un cambio (por ejemplo --edad 65).")
    table = s.resource("dynamodb").Table("ca-personas")
    table.update_item(
        Key={"run": args.run},
        UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in values),
        ExpressionAttributeNames={f"#{k}": k for k in values},
        ExpressionAttributeValues={f":{k}": v for k, v in values.items()},
        ConditionExpression="attribute_exists(run)",
    )
    print(f"Actualizado {args.run}: {values}")
    print("El stream de DynamoDB dispara la detección; revisa con `estado` en unos segundos.")


def _service(s) -> Service:
    return Service(Settings(), dynamodb=s.resource("dynamodb"), ses=s.client("ses"))


def cmd_estado(args, s):
    svc = _service(s)
    print(json.dumps(svc.person(args.run), ensure_ascii=False, indent=1, default=str))
    for contact in svc.contacts_of(args.run):
        contact.pop("token", None)
        print(json.dumps(contact, ensure_ascii=False, indent=1, default=str))
    print("Historial:")
    for event in svc.history_of(args.run):
        detail = {k: v for k, v in event["detalle"].items() if k != "texto"}
        print(
            f"  {event['sk'][:19]} {event['beneficio_id']:<22} {event['evento']:<18} "
            f"{event['canal']:<8} {detail}"
        )


def cmd_responder(args, s):
    contact = _service(s).record_answer(args.run, args.beneficio, args.respuesta, args.canal)
    print(
        f"{args.run} {args.beneficio}: estado {contact['estado']}, respuesta {contact['respuesta']}"
    )


def cmd_terreno(args, s):
    svc = _service(s)
    rows = svc.by_state("terreno")
    by_commune = Counter()
    for contact in rows:
        person = svc.person(contact["run"]) or {}
        by_commune[person.get("comuna", "sin comuna")] += 1
        print(
            f"{contact['run']:<12} {person.get('nombre', ''):<28} {person.get('comuna', ''):<14} "
            f"{contact['beneficio']}"
        )
    print(f"\n{len(rows)} contactos para el equipo en terreno. Por comuna: {dict(by_commune)}")


def cmd_resumen(args, s):
    table = s.resource("dynamodb").Table("ca-contactos")
    items, options = [], {}
    while True:
        page = table.scan(**options)
        items += page["Items"]
        if "LastEvaluatedKey" not in page:
            break
        options["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    print(f"{len(items)} contactos")
    for title, key in (
        ("Por estado", "estado"),
        ("Por beneficio", "beneficio_id"),
        ("Por tipo", "tipo"),
        ("Por respuesta", "respuesta"),
    ):
        print(f"{title}: {dict(Counter(i[key] for i in items).most_common())}")
    flags = (
        "email_enviado",
        "email_simulado",
        "email_abierto",
        "email_click",
        "sms_enviado",
        "terreno",
    )
    print("Banderas:", {f: sum(bool(i.get(f)) for i in items) for f in flags})


def cmd_invocar(args, s):
    response = s.client("lambda").invoke(FunctionName=FUNCTIONS[args.cmd])
    print(response["Payload"].read().decode())


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("cargar")
    p.add_argument(
        "--email", default="curibeo@utem.cl", help="Casilla verificada de las personas demo"
    )
    p.add_argument(
        "--solo-demo", action="store_true", help="No cargar los 500 perfiles del dataset"
    )
    p = sub.add_parser("evento", help="Simular un cambio de vida en la base de datos")
    p.add_argument("run")
    p.add_argument("--edad", type=int)
    p.add_argument("--nacimiento", help="AAAA-MM-DD")
    p.add_argument("--hijos", type=int)
    p.add_argument("--estado-civil", choices=["soltero", "casado", "AUC", "divorciado", "viudo"])
    p.add_argument("--casado-desde", help="AAAA-MM-DD")
    p.add_argument("--accidente", action="store_true")
    p.add_argument("--tramo", type=int, help="Tramo RSH: 40, 50, ..., 100")
    p.add_argument("--trabaja", choices=["si", "no"])
    p = sub.add_parser("estado")
    p.add_argument("run")
    p = sub.add_parser("responder")
    p.add_argument("run")
    p.add_argument("beneficio")
    p.add_argument("respuesta", choices=["acepto", "rechazo", "sin_respuesta"])
    p.add_argument("--canal", default="terreno", choices=["telefono", "terreno", "sucursal"])
    sub.add_parser("terreno")
    sub.add_parser("resumen")
    sub.add_parser("escalar")
    sub.add_parser("revisar")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    handler = {
        "cargar": cmd_cargar,
        "evento": cmd_evento,
        "estado": cmd_estado,
        "responder": cmd_responder,
        "terreno": cmd_terreno,
        "resumen": cmd_resumen,
        "escalar": cmd_invocar,
        "revisar": cmd_invocar,
    }[args.cmd]
    handler(args, session())


if __name__ == "__main__":
    main()
