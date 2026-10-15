"""Repositorio DynamoDB con mensajes append-only y lecturas paginadas."""

from datetime import UTC, datetime
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key

from src.cases.esquema import RUN_INDEX, TABLE_NAME, deserialize, serialize
from src.contracts import Case, LifeEvent, Message
from src.tools.profiles import normalize_run


class CaseRepository:
    def __init__(self, table=None):
        self.table = table if table is not None else boto3.resource("dynamodb").Table(TABLE_NAME)

    def crear(self, run, event=LifeEvent.RETIREMENT):
        case = Case(
            case_id=str(uuid4()), run=normalize_run(run), event=event, created_at=datetime.now(UTC)
        )
        item = serialize(case.model_dump(mode="json", exclude={"messages"}))
        self.table.put_item(
            Item={"pk": case.case_id, "sk": "caso", **item},
            ConditionExpression="attribute_not_exists(pk)",
        )
        return case

    def _query(self, **kwargs):
        items = []
        while True:
            result = self.table.query(**kwargs)
            items.extend(result["Items"])
            if "LastEvaluatedKey" not in result:
                return items
            kwargs["ExclusiveStartKey"] = result["LastEvaluatedKey"]

    def cargar(self, case_id):
        result = self.table.get_item(Key={"pk": case_id, "sk": "caso"}, ConsistentRead=True)
        if "Item" not in result:
            raise KeyError(case_id)
        item = deserialize(result["Item"])
        item.pop("pk")
        item.pop("sk")
        messages = self._query(
            KeyConditionExpression=Key("pk").eq(case_id) & Key("sk").begins_with("msg#"),
            ConsistentRead=True,
        )
        item["messages"] = [deserialize(x["message"]) for x in messages]
        return Case.model_validate(item)

    def buscar_por_run(self, run):
        items = self._query(
            IndexName=RUN_INDEX, KeyConditionExpression=Key("run").eq(normalize_run(run))
        )
        return [self.cargar(item["pk"]) for item in items]

    def agregar_mensajes(self, case_id, mensajes):
        # A sortable batch token preserves order even for identical timestamps.
        batch = datetime.now(UTC).isoformat() + "#" + uuid4().hex
        for index, message in enumerate(mensajes):
            message = Message.model_validate(message)
            self.table.put_item(
                Item={
                    "pk": case_id,
                    "sk": f"msg#{batch}#{index:06d}",
                    "message": serialize(message.model_dump(mode="json")),
                },
                ConditionExpression="attribute_not_exists(pk)",
            )

    def guardar_estado(self, case):
        item = serialize(case.model_dump(mode="json", exclude={"messages"}))
        self.table.put_item(
            Item={"pk": case.case_id, "sk": "caso", **item},
            ConditionExpression="attribute_exists(pk)",
        )
