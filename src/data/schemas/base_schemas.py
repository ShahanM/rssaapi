import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class BaseDBSchema(BaseModel):
	model_config = ConfigDict(from_attributes=True)
	id: uuid.UUID


class ReorderPayloadSchema(BaseModel):
	id: uuid.UUID
	order_position: int


class UpdatePayloadSchema(BaseModel):
	parent_id: uuid.UUID
	updated_fields: dict[str, Any]
