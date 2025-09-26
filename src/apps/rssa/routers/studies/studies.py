import datetime
import logging
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth.authorization import authorize_api_key_for_study, generate_jwt_token_for_payload
from data.schemas.participant_schemas import ParticpantBaseSchema
from data.schemas.study_components import StudyStepNavigationSchema, StudyStepSchema
from data.services import (
    ParticipantMovieSessionService,
    ParticipantService,
    ParticipantSessionService,
    StudyConditionService,
    StudyStepService,
)
from data.services.rssa_dependencies import get_participant_movie_session_service as movie_session_service
from data.services.rssa_dependencies import get_participant_service as participant_service
from data.services.rssa_dependencies import get_participant_session_service as participant_session_service
from data.services.rssa_dependencies import get_study_condition_service as condition_service
from data.services.rssa_dependencies import get_study_step_service as step_service
from docs.rssa_docs import Tags

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
    prefix='/studies',
    tags=[Tags.study],
    dependencies=[Depends(authorize_api_key_for_study)],
)

STEP_TYPE_TO_COMPONENT = {
    'survey': 'SurveyStep',
    'overview': 'StudyOverviewStep',
    'task': 'TaskStep',
    'preference-elicitation': 'PreferenceElicitationStep',
    'consent': 'ConsentStep',
    'instruction': 'InstructionStep',
    'demographics': 'DemographicsStep',
    'extras': 'ExtraStep',
    'end': 'CompletionStep',
}


class StudyStepConfigObj(BaseModel):
    step_id: uuid.UUID
    path: str
    component_type: str


class StudyConfigSchema(BaseModel):
    study_id: uuid.UUID
    conditions: dict[str, uuid.UUID]
    steps: list[StudyStepConfigObj]


class ResumePayloadSchema(BaseModel):
    resume_code: str


class ResumeResponseSchema(BaseModel):
    current_step_id: uuid.UUID
    current_page_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }


@router.get('/{study_id}/steps/first', response_model=StudyStepNavigationSchema)
async def get_first_step(
    study_id: uuid.UUID,
    step_service: Annotated[StudyStepService, Depends(step_service)],
):
    study_step = await step_service.get_first_study_step(study_id)

    if not study_step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Something went wrong, could not find the entry point to the study.',
        )
    study_step_dict = study_step.model_dump()
    next_step = await step_service.get_next_step(study_step.id)
    if not next_step:
        study_step_dict['next'] = None
    else:
        study_step_dict['next'] = next_step.path

    return StudyStepNavigationSchema.model_validate(study_step_dict)


@router.get('/{study_id}/config', response_model=StudyConfigSchema)
async def export_study_config(
    study_id: uuid.UUID,
    step_service: Annotated[StudyStepService, Depends(step_service)],
    condition_service: Annotated[StudyConditionService, Depends(condition_service)],
):
    steps = await step_service.get_study_steps(study_id)
    conditions = await condition_service.get_study_conditions(study_id)
    print(steps)
    config = {
        'study_id': study_id,
        'conditions': {con.name: con.id for con in conditions},
        'steps': [
            {
                'step_id': step.id,
                'path': step.path,
                'component_type': STEP_TYPE_TO_COMPONENT[step.step_type if step.step_type else 'extras'],
            }
            for step in steps
        ],
    }
    print(config)

    return config


@router.post('/{study_id}/new-participant', response_model=dict[str, str])
async def create_new_participant_with_session(
    study_id: uuid.UUID,
    new_participant: ParticpantBaseSchema,
    participant_service: Annotated[ParticipantService, Depends(participant_service)],
    step_service: Annotated[StudyStepService, Depends(step_service)],
    session_service: Annotated[ParticipantSessionService, Depends(participant_session_service)],
    movie_session_service: Annotated[ParticipantMovieSessionService, Depends(movie_session_service)],
):
    next_step = await step_service.get_next_step(new_participant.current_step_id)
    if not next_step:
        raise HTTPException(status_code=500, detail='Could not find next step, study is configuration fault.')
    new_participant.current_step_id = next_step.id
    study_participant = await participant_service.create_study_participant(study_id, new_participant)
    session = await session_service.create_session(study_participant.id)
    await movie_session_service.assign_pre_shuffled_list_participant(study_participant.id, 'ers')
    if session is None:
        raise HTTPException(status_code=500, detail='Could not create unique session.')

    jwt_payload = {'sub': str(study_participant.id), 'sid': str(session.id), 'exp': session.expires_at}
    jwt_token = generate_jwt_token_for_payload(jwt_payload)

    return {'resume_code': session.resume_code, 'token': jwt_token}


@router.post('/{study_id}/resume', response_model=ResumeResponseSchema)
async def resume_study_session(
    payload: ResumePayloadSchema,
    session_service: Annotated[ParticipantSessionService, Depends(participant_session_service)],
    participant_service: Annotated[ParticipantService, Depends(participant_service)],
    study_id: Annotated[uuid.UUID, Depends(authorize_api_key_for_study)],
):
    participant_session = await session_service.get_session_by_resume_code(payload.resume_code)
    if participant_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Could not find a valid session for the code.'
        )
    if (
        participant_session.expires_at < datetime.datetime.now(datetime.timezone.utc)
        or not participant_session.is_active
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Expired or invalid resume code.')

    participant = await participant_service.get_participant(participant_session.participant_id)

    if participant is None or participant.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Resume code not valid for this study.')

    jwt_payload = {
        'sub': str(participant.id),
        'sid': str(participant_session.id),
        'exp': participant_session.expires_at,
    }
    jwt_token = generate_jwt_token_for_payload(jwt_payload)

    return ResumeResponseSchema.model_validate(
        {
            'current_step_id': participant.current_step_id,
            'current_page_id': participant.current_page_id,
            'token': jwt_token,
        }
    )
