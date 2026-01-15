import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import inspect


def sa_obj_to_dict(obj):
    """Converts a SQLAlchemy object to a dictionary."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def convert_uuids_to_str(data: dict[str, Any]) -> dict[str, Any]:
    """Converts UUIDs in a dictionary to strings recursively."""
    if isinstance(data, dict):
        return {k: convert_uuids_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_uuids_to_str(element) for element in data]
    elif isinstance(data, uuid.UUID):
        return str(data)
    else:
        return data


def convert_datetime_to_str(data: dict[str, Any]) -> dict[str, Any]:
    """Converts datetime in a dictionary to strings recursively."""
    if isinstance(data, dict):
        return {k: convert_datetime_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_datetime_to_str(element) for element in data]
    elif isinstance(data, datetime):
        return str(data)
    else:
        return data
