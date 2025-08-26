import datetime
import uuid
from typing import Any

from pydantic import BaseModel


class BaseDBSchema(BaseModel):
	id: uuid.UUID

	class Config:
		from_attributes = True
		json_encoders = {
			uuid.UUID: lambda v: str(v),
			datetime: lambda v: v.isoformat(),
		}


class ReorderPayloadSchema(BaseModel):
	id: uuid.UUID
	order_position: int


class UpdatePayloadSchema(BaseModel):
	parent_id: uuid.UUID
	updated_fields: dict[str, Any]
