"""Router for study steps endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from rssa_api.auth.authorization import validate_api_key
from rssa_api.data.schemas.study_components import NavigationWrapper, StudyStepPageRead, StudyStepRead
from rssa_api.data.services.dependencies import StudyStepPageServiceDep, StudyStepServiceDep

router = APIRouter(
    prefix='/steps',
    tags=['Study steps'],
    dependencies=[Depends(validate_api_key)],
)


@router.get(
    '/{step_id}',
    response_model=NavigationWrapper[StudyStepRead],
)
async def get_study_step(
    step_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    page_service: StudyStepPageServiceDep,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
):
    """Retrieves a step from the database via the StudyStepService.

    Args:
            step_id: The UUID of the study step to retrieve.
            step_service: The dependency-injected study step service.
            page_service: The dependency-injected study step page service.
            study_id: The UUID of the study to which the step must belong.

    Returns:
            StudyStepSchema: The study step object if found.
    """
    step_result = await step_service.get_with_navigation(step_id)
    if not step_result:
        raise HTTPException(status_code=404, detail='Study step not found.')
    validated_step = StudyStepRead.model_validate(step_result['current'])

    if validated_step.study_id != study_id:
        raise HTTPException(status_code=403, detail='Study step does not belong to the authorized study.')

    page_result = await page_service.get_first_with_navigation(step_id)

    root_page_info = None
    if page_result:
        root_page_info = NavigationWrapper[StudyStepPageRead](
            data=page_result['current'],
            next_id=page_result['next_id'],
            next_path=page_result['next_path'],
        )
    validated_step.root_page_info = root_page_info
    step = NavigationWrapper[StudyStepRead](
        data=validated_step,
        next_id=step_result['next_id'],
        next_path=step_result['next_path'],
    )

    return step


@router.get('/{step_id}/pages/first', response_model=NavigationWrapper[StudyStepPageRead])
async def get_first_page_endpoint(
    step_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
):
    """Convenient routing to the StudySteps resources to access survey pages.

    Args:
            step_id: The UUID for StudyStep.
            page_service: The dependency-injected study step page service.
            study_id: The UUID of the study to which the step must belong.

    Returns:
            SurveyPageSchema: The full content of the first survey page for the survey step.
    """
    page_result = await page_service.get_first_with_navigation(step_id)
    if not page_result:
        raise HTTPException(status_code=404, detail='No first page found for this step or step not in study.')

    validated_page = StudyStepPageRead.model_validate(page_result['current'])

    if validated_page.study_id != study_id:
        raise HTTPException(status_code=403, detail='Study step page does not belong to the authorized study.')
    first_page = NavigationWrapper[StudyStepPageRead](
        data=validated_page,
        next_id=page_result['next_id'],
        next_path=page_result['next_path'],
    )
    return first_page
