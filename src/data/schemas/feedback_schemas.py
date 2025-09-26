import uuid
from datetime import datetime

from pydantic import BaseModel

from .base_schemas import BaseDBMixin


class FeedbackBaseSchema(BaseModel):
    feedback_text: str
    feedback_type: str
    feedback_category: str


class FeedbackSchema(FeedbackBaseSchema, BaseDBMixin):
    participant_id: uuid.UUID
    created_at: datetime
    study_id: uuid.UUID
