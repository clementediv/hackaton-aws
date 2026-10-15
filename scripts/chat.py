"""Cliente de humo del chatbot desplegado; obtiene secretos sin imprimirlos."""

import argparse
import json
import subprocess
import urllib.request

import boto3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", default="100000001-5")
    parser.add_argument("--profile", default="hackaton")
    parser.add_argument("--verify", action="store_true", help="Tres turnos y recarga por AWS CLI")
    args = parser.parse_args()
    session = boto3.Session(profile_name=args.profile, region_name="us-east-1")
    stack = session.client("cloudformation").describe_stacks(StackName="ChileAtiendeChat")
    outputs = {x["OutputKey"]: x["OutputValue"] for x in stack["Stacks"][0]["Outputs"]}
    key = session.client("secretsmanager").get_secret_value(SecretId=outputs["ApiKeySecret"])[
        "SecretString"
    ]

    def call(path, data=None):
        request = urllib.request.Request(
            outputs["Url"] + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={"x-api-key": key, "x-run": args.run, "content-type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=35) as result:
            payload = json.load(result)
            assert payload["ok"], payload
            return payload["data"]

    case = call("/casos", {"run": args.run})
    case_id = case["case_id"]
    print("Caso:", case_id)
    call(f"/casos/{case_id}/invitacion", {"response": "aceptada"})
    call(
        f"/casos/{case_id}/autorizacion",
        {
            "granted": True,
            "sources": ["Dataset A sintético"],
            "purpose": "Demostrar continuidad del acompañamiento",
        },
    )
    questions = (
        [
            "Me llamo Rosa. Recuerda que prefiero atención telefónica. Responde en una frase.",
            "Consulta leer_caso y resume mi orientación PGU en dos frases con fuente.",
            "¿Cómo me llamo y qué canal prefiero? Responde en una frase con fuente.",
        ]
        if args.verify
        else iter(lambda: input("Tú (vacío para salir): "), "")
    )
    replies = []
    for question in questions:
        reply = call("/chat", {"case_id": case_id, "text": question})
        replies.append(reply["text"])
        print("Asistente:", reply["text"])
    if args.verify:
        assert "Rosa" in replies[-1] and "telef" in replies[-1].lower()
        result = subprocess.run(
            [
                "aws",
                "dynamodb",
                "query",
                "--table-name",
                "ca-casos",
                "--key-condition-expression",
                "pk = :id",
                "--expression-attribute-values",
                json.dumps({":id": {"S": case_id}}),
                "--consistent-read",
                "--profile",
                args.profile,
                "--region",
                "us-east-1",
                "--output",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        items = json.loads(result.stdout)["Items"]
        messages = [x for x in items if x["sk"]["S"].startswith("msg#")]
        assert len(messages) == 6, len(messages)
        texts = [x["message"]["M"]["text"]["S"] for x in messages]
        assert "Rosa" in texts[0] and "Rosa" in texts[-1]
        print("AWS CLI DynamoDB: 6 mensajes, tres turnos y continuidad confirmados.")


if __name__ == "__main__":
    main()
