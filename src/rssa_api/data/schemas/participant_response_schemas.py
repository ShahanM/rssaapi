import uuid
from typing import Any, Optional, Union

from pydantic import BaseModel

from rssa_api.data.schemas.base_schemas import DBMixin, VersionMixin


class ParticipantResponseContextMixin:
    __abstract__ = True
    study_step_id: uuid.UUID
    study_step_page_id: Optional[uuid.UUID] = None
    context_tag: str


class ParticipantSurveyResponseBase(BaseModel, ParticipantResponseContextMixin):
    survey_construct_id: uuid.UUID
    survey_item_id: uuid.UUID
    survey_scale_id: uuid.UUID
    survey_scale_level_id: uuid.UUID


class ParticipantSurveyResponseCreate(ParticipantSurveyResponseBase):
    pass

class ParticipantSurveyResponseRead(ParticipantSurveyResponseBase, VersionMixin, DBMixin):
    pass


class ParticipantSurveyResponseUpdate(ParticipantSurveyResponseRead):
    survey_scale_level_id: uuid.UUID


class ParticipantFreeformResponseBase(BaseModel, ParticipantResponseContextMixin):
    response_text: str


class ParticipantFreeformResponseCreate(ParticipantFreeformResponseBase):
    pass


class ParticipantFreeformResponseRead(ParticipantFreeformResponseBase, VersionMixin, DBMixin):
    pass


class ParticipantFreeformResponseUpdate(ParticipantFreeformResponseRead):
    response_text: str


class RatedItem(BaseModel):
    item_id: uuid.UUID
    rating: int


class ParticipantRatingBase(BaseModel, ParticipantResponseContextMixin):
    rated_item: RatedItem


class MovieLensRating(BaseModel):
    item_id: Union[str, int]
    rating: int


class DynamicPayload(BaseModel):
    experimnet_condition: Optional[str] = None
    extra: dict[str, Any] = {}

    model_config = {'extra': 'allow'}


class ParticipantStudyInteractionResponseBase(BaseModel, ParticipantResponseContextMixin):
    payload_json: DynamicPayload


class ParticipantStudyInteractionResponseCreate(ParticipantStudyInteractionResponseBase):
    pass


class ParticipantStudyInteractionResponseRead(ParticipantStudyInteractionResponseBase, VersionMixin, DBMixin):
    pass


class ParticipantStudyInteractionResponseUpdate(ParticipantStudyInteractionResponseRead):
    pass



# The Feedback Schemas are deprecated. They will be refactored to become user feedback. Participant feedback will
# be collected in the form of freeform responses. So we will keep them as is for now.
class FeedbackBaseSchema(BaseModel, ParticipantResponseContextMixin):
    feedback_text: str
    feedback_type: str
    feedback_category: str


class FeedbackSchema(FeedbackBaseSchema, VersionMixin, DBMixin):
    pass


class ParticipantRatingRead(ParticipantRatingBase, VersionMixin, DBMixin):
    pass


class ParticipantRatingUpdate(ParticipantRatingRead):
    pass
