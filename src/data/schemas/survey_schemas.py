import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


class SurveyPageSchema(BaseModel):
	id: uuid.UUID
	survey_id: uuid.UUID = Field(validation_alias='step_id')

	order_position: int

	construct_id = (construct.id,)
	construct_items = ([ConstructItemSchema.from_orm(item) for item in items],)
	construct_scale = ([ScaleLevelSchema.from_orm(level) for level in scalelevels],)
