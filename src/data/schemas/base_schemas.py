import uuid

from pydantic import BaseModel, ConfigDict


class BaseDBSchema(BaseModel):
	model_config = ConfigDict(from_attributes=True)
	id: uuid.UUID
