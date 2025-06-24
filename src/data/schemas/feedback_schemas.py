import uuid
from datetime import datetime

from pydantic import BaseModel


class FeedbackSchema(BaseModel):
	id: uuid.UUID
	participant_id: uuid.UUID
	created_at: datetime
	study_id: uuid.UUID
	feedback_text: str
	feedback_type: str
	feedback_category: str


class FeedbackCreateSchema(BaseModel):
	participant_id: uuid.UUID
	feedback_text: str
	feedback_type: str
	feedback_category: str
