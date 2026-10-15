"""Claves y serialización DynamoDB de casos."""

import json
import os
from decimal import Decimal

TABLE_NAME = os.environ.get("TABLA_CASOS", "ca-casos")
RUN_INDEX = "por-run"


def serialize(value):
    return json.loads(json.dumps(value), parse_float=Decimal)


def deserialize(value):
    return json.loads(
        json.dumps(value, default=lambda x: float(x) if isinstance(x, Decimal) else x)
    )
