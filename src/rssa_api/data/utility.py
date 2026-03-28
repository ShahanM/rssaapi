"""Utility file to help with data modeling."""

import inspect
import types
import uuid
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Union, get_args, get_origin

import sqlalchemy as sa
from pydantic import BaseModel


def sa_obj_to_dict(obj):
    """Converts a SQLAlchemy object to a dictionary."""
    return {c.key: getattr(obj, c.key) for c in sa.inspect(obj).mapper.column_attrs}


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


def get_columns_from_schema(schema_cls: type[BaseModel]) -> list[str]:
    """Extracts fields from a schema.

    Extracts all field names from a Pydantic schema to be used for
    SQLAlchemy deferred loading (load_only).
    """
    return list(schema_cls.model_fields.keys())


def _unwrap_pydantic_annotation(annotation: Any) -> Any:
    """Recursively unwraps Optional, Union, and Iterable types to find the core class."""
    origin = get_origin(annotation)

    if origin is None:
        return annotation

    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        for arg in args:
            if arg is not type(None):
                return _unwrap_pydantic_annotation(arg)

    if origin in (list, set, tuple) or (isinstance(origin, type) and issubclass(origin, Iterable)):
        args = get_args(annotation)
        if args:
            return _unwrap_pydantic_annotation(args[0])

    return annotation


def extract_load_strategies(schema_cls: type[BaseModel]) -> tuple[list[str], dict[str, list[str]]]:
    """Parses a Pydantic schema to separate top-level columns from nested relationships."""
    top_level_cols = []
    relationships = {}

    for field_name, field_info in schema_cls.model_fields.items():
        core_type = _unwrap_pydantic_annotation(field_info.annotation)

        if inspect.isclass(core_type) and issubclass(core_type, BaseModel):
            nested_cols, nested_rels = extract_load_strategies(core_type)

            relationships[field_name] = {'columns': nested_cols, 'relationships': nested_rels}
        else:
            top_level_cols.append(field_name)

    return top_level_cols, relationships
