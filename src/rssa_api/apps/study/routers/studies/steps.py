"""Router for study steps endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from rssa_api.auth.authorization import decode_jwt
from rssa_api.data.schemas.study_components import (
    NavigationWrapper,
    StudyStepPagePresent,
    StudyStepPresent,
)
from rssa_api.data.services.dependencies import StudyStepPageServiceDep, StudyStepServiceDep

router = APIRouter(
    prefix='/steps',
    tags=['Study steps'],
    dependencies=[Depends(decode_jwt)],
)


@router.get(
    '/{step_id}',
    response_model=NavigationWrapper[StudyStepPresent],
)
async def get_study_step(
    step_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    page_service: StudyStepPageServiceDep,
    token_content: Annotated[dict, Depends(decode_jwt)],
):
    """Retrieves a step from the database via the StudyStepService.

    Args:
        step_id: The UUID of the study step to retrieve.
        step_service: The dependency-injected study step service.
        page_service: The dependency-injected study step page service.
        token_content: The decoded jwt contaning the registered study_id, and current participant_id.

    Returns:
        StudyStepSchema: The study step object if found.
    """
    step_result = await step_service.get_with_navigation(step_id, StudyStepPresent)
    if not step_result:
        raise HTTPException(status_code=404, detail='Study step not found.')
    validated_step = StudyStepPresent.model_validate(step_result['current'])

    participant_id = uuid.UUID(token_content.get('sub'))
    study_id = uuid.UUID(token_content.get('sty'))

    if validated_step.study_id != study_id:
        raise HTTPException(status_code=403, detail='Study step does not belong to the authorized study.')

    step_service.enqueue_progress_update(participant_id, step_id)
    page_result = await page_service.get_first_with_navigation(step_id, StudyStepPagePresent)

    root_page_info = None
    if page_result:
        root_page_info = NavigationWrapper[StudyStepPagePresent](
            data=page_result['current'],
            next_id=page_result['next_id'],
            next_path=page_result['next_path'],
        )
    validated_step.root_page_info = root_page_info
    step = NavigationWrapper[StudyStepPresent](
        data=validated_step,
        next_id=step_result['next_id'],
        next_path=step_result['next_path'],
    )

    return step


@router.get('/{step_id}/pages/first', response_model=NavigationWrapper[StudyStepPagePresent])
async def get_first_page_endpoint(
    step_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    token_content: Annotated[dict, Depends(decode_jwt)],
):
    """Convenient routing to the StudySteps resources to access survey pages.

    Args:
        step_id: The UUID for StudyStep.
        page_service: The dependency-injected study step page service.
        token_content: The decoded jwt contaning the registered study_id, and current participant_id.

    Returns:
        SurveyPageSchema: The full content of the first survey page for the survey step.
    """
    page_result = await page_service.get_first_survey_page(step_id, StudyStepPagePresent)
    if not page_result:
        raise HTTPException(status_code=404, detail='No first page found for this step or step not in study.')

    study_id = uuid.UUID(token_content.get('sty'))

    if page_result.data.study_id != study_id:
        raise HTTPException(status_code=403, detail='Study step page does not belong to the authorized study.')
    return page_result
