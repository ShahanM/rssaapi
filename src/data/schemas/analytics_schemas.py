import uuid

from typing_extensions import TypedDict


class ConditionCountSchema(TypedDict):
	condition_id: uuid.UUID
	condition_name: str
	participant_count: int
