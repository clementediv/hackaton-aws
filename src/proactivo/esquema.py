"""Table keys and indexes. infra/proactivo_stack.py must declare the same ones."""

TABLES = {
    "personas": {"pk": "run"},
    "beneficios": {"pk": "beneficio_id"},
    "contactos": {"pk": "run", "sk": "beneficio_id"},
    "historial": {"pk": "run", "sk": "sk"},
}

# Sparse index: only contacts waiting for their next channel carry `cola`.
QUEUE_INDEX = "cola-siguiente"
QUEUE_PENDING = "pendiente"
# Field-team and dashboard listings by state.
STATE_INDEX = "estado-detectado"


def create_tables(dynamodb, names: dict[str, str]) -> None:
    """Create the tables (local tests / moto). Production uses CDK."""
    for key, spec in TABLES.items():
        attrs = [{"AttributeName": spec["pk"], "AttributeType": "S"}]
        schema = [{"AttributeName": spec["pk"], "KeyType": "HASH"}]
        if "sk" in spec:
            attrs.append({"AttributeName": spec["sk"], "AttributeType": "S"})
            schema.append({"AttributeName": spec["sk"], "KeyType": "RANGE"})
        extra = {}
        if key == "contactos":
            attrs += [
                {"AttributeName": a, "AttributeType": "S"}
                for a in ("cola", "siguiente_accion_en", "estado", "detectado_en")
            ]
            extra["GlobalSecondaryIndexes"] = [
                _gsi(QUEUE_INDEX, "cola", "siguiente_accion_en"),
                _gsi(STATE_INDEX, "estado", "detectado_en"),
            ]
        if key == "personas":
            extra["StreamSpecification"] = {
                "StreamEnabled": True,
                "StreamViewType": "NEW_AND_OLD_IMAGES",
            }
        dynamodb.create_table(
            TableName=names[key],
            KeySchema=schema,
            AttributeDefinitions=attrs,
            BillingMode="PAY_PER_REQUEST",
            **extra,
        )


def _gsi(name: str, pk: str, sk: str) -> dict:
    return {
        "IndexName": name,
        "KeySchema": [
            {"AttributeName": pk, "KeyType": "HASH"},
            {"AttributeName": sk, "KeyType": "RANGE"},
        ],
        "Projection": {"ProjectionType": "ALL"},
    }
