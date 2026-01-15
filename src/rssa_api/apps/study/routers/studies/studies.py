"""Router for study management endpoints."""

import datetime
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from rssa_api.auth.authorization import authorize_api_key_for_study, generate_jwt_token_for_payload
from rssa_api.data.schemas.participant_schemas import StudyParticipantCreate
from rssa_api.data.schemas.study_components import NavigationWrapper, StudyStepRead
from rssa_api.data.services.dependencies import (
    EnrollmentServiceDep,
    ParticipantStudySessionServiceDep,
    StudyConditionServiceDep,
    StudyParticipantMovieSessionServiceDep,
    StudyParticipantServiceDep,
    StudyStepServiceDep,
)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str


router = APIRouter(
    prefix='/studies',
    tags=['Studies'],
    dependencies=[Depends(authorize_api_key_for_study)],
    responses={
        status.HTTP_403_FORBIDDEN: {
            'model': ErrorResponse,
            'description': 'API key missing or invalid (Forbidden)',
        }
    },
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
    """Configuration object for a study step."""

    step_id: uuid.UUID
    path: str
    component_type: str


class StudyConfigSchema(BaseModel):
    """Schema for the full study configuration."""

    study_id: uuid.UUID
    conditions: dict[str, uuid.UUID]
    steps: list[StudyStepConfigObj]


class ResumePayloadSchema(BaseModel):
    """Payload for resuming a study session."""

    resume_code: str


class ResumeResponseSchema(BaseModel):
    """Response schema for a resumed session."""

    current_step_id: uuid.UUID
    current_page_id: uuid.UUID | None = None
    token: str

    model_config = ConfigDict(from_attributes=True)


@router.get(
    '/{study_id}/steps/first',
    status_code=status.HTTP_200_OK,
    response_model=NavigationWrapper[StudyStepRead],
    summary='Retrieves the first step of the study.',
    description='This is the first call made by a registered study when a study start is initiated.',
    response_description='Returns the first StudyStep object with navigation info.',
    responses={
        status.HTTP_404_NOT_FOUND: {
            'model': ErrorResponse,
            'description': 'No study steps found.',
        }
    },
)
async def get_first_step(
    study_id: uuid.UUID,
    step_service: StudyStepServiceDep,
):
    """Get the first step of a study.

    Args:
        study_id: The UUID of the study.
        step_service: The study step service.

    Raises:
        HTTPException: If the study entry point is not found.

    Returns:
        The first study step with navigation details.
    """
    study_step = await step_service.get_first_with_navigation(study_id)

    if not study_step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Something went wrong, could not find the entry point to the study.',
        )

    validated_step = StudyStepRead.model_validate(study_step['current'])
    study_step_dict = NavigationWrapper[StudyStepRead](
        data=validated_step,
        next_id=study_step['next_id'],
        next_path=study_step['next_path'],
    )

    return study_step_dict


@router.get(
    '/{study_id}/config',
    status_code=status.HTTP_200_OK,
    response_model=StudyConfigSchema,
    summary='Get study configuration.',
    description='Retrieves the configuration for a study, including steps and conditions.',
)
async def export_study_config(
    study_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    condition_service: StudyConditionServiceDep,
):
    """Export the configuration for a study.

    Args:
        study_id: The UUID of the study.
        step_service: Service for study steps.
        condition_service: Service for study conditions.

    Returns:
        The study configuration object.
    """
    steps = await step_service.get_items_for_owner_as_ordered_list(study_id)
    conditions = await condition_service.get_all_for_owner(study_id)
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

    return config


@router.post(
    '/{study_id}/new-participant',
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, str],
    summary='Create and enroll a new participant.',
    description='Enrolls a new participant, creates a session, and assigns a movie list.',
)
async def create_new_participant_with_session(
    study_id: uuid.UUID,
    new_participant: StudyParticipantCreate,
    enrollment_service: EnrollmentServiceDep,
    step_service: StudyStepServiceDep,
    session_service: ParticipantStudySessionServiceDep,
    movie_session_service: StudyParticipantMovieSessionServiceDep,
):
    """Enroll a new participant and start a session.

    Args:
        study_id: The UUID of the study.
        new_participant: Participant creation data.
        enrollment_service: Service for enrollment.
        step_service: Service for study steps.
        session_service: Service for session management.
        movie_session_service: Service for movie session assignments.

    Raises:
        HTTPException: If next step cannot be found or session creation fails.

    Returns:
        Dictionary containing resume code and JWT token.
    """
    current_step = await step_service.get_with_navigation(new_participant.current_step_id)
    if not current_step:
        raise HTTPException(status_code=500, detail='Could not find next step, study is configuration fault.')
    new_participant.current_step_id = current_step['next_id']

    study_participant = await enrollment_service.enroll_participant(study_id, new_participant)
    session = await session_service.create_session(study_participant.id)
    await movie_session_service.assign_pre_shuffled_list_participant(study_participant.id, 'ers')
    if session is None:
        raise HTTPException(status_code=500, detail='Could not create unique session.')

    jwt_payload = {'sub': str(study_participant.id), 'sid': str(session.id), 'exp': session.expires_at}
    jwt_token = generate_jwt_token_for_payload(jwt_payload)

    return {'resume_code': session.resume_code, 'token': jwt_token}


@router.post(
    '/{study_id}/resume',
    status_code=status.HTTP_200_OK,
    response_model=ResumeResponseSchema,
    summary='Resume a study session.',
    description='Resumes an existing study session using a resume code.',
)
async def resume_study_session(
    payload: ResumePayloadSchema,
    session_service: ParticipantStudySessionServiceDep,
    participant_service: StudyParticipantServiceDep,
    study_id: Annotated[uuid.UUID, Depends(authorize_api_key_for_study)],
):
    """Resume a study session.

    Args:
        payload: The resume payload containing the resume code.
        session_service: Service for session management.
        participant_service: Service for participant management.
        study_id: The UUID of the authorized study.

    Raises:
        HTTPException: If session is invalid, expired, or belongs to another study.

    Returns:
        Resume response with current step and new token.
    """
    participant_session = await session_service.get_session_by_resume_code(payload.resume_code)
    if participant_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Could not find a valid session for the code.'
        )
    if participant_session.expires_at < datetime.datetime.now(datetime.UTC) or not participant_session.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Expired or invalid resume code.')

    participant = await participant_service.get(participant_session.study_participant_id)

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
