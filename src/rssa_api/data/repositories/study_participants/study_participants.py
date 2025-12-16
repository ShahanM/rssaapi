from sqlalchemy.orm import selectinload

from rssa_api.data.models.study_participants import StudyParticipant
from rssa_api.data.repositories.base_repo import BaseRepository


class StudyParticipantRepository(BaseRepository[StudyParticipant]):
    LOAD_ASSIGNED_CONDITION = (selectinload(StudyParticipant.study_condition),)
