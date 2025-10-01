"""Normalization helpers mirroring production behaviour in a lightweight way."""
from __future__ import annotations

import datetime
import re
import uuid
from decimal import Decimal


def make_json_safe(value):
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def convert_row(row):
    return {col: make_json_safe(val) for col, val in row.items()}


def enforce_ilike(sql_query: str) -> str:
    pattern_equals = r"([\w\.]+)\s*=\s*'([^']+)'"

    def normalize(token: str) -> str:
        return re.sub(r"[ -]", "_", token).strip()

    sql_query = re.sub(
        pattern_equals,
        lambda m: f"REPLACE(REPLACE({m.group(1)}, ' ', '_'), '-', '_') ILIKE '%%{normalize(m.group(2))}%%'",
        sql_query,
        flags=re.IGNORECASE,
    )
    return sql_query

