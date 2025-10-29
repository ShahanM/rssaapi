import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_api_key
from rssa_api.data.schemas.study_components import PageNavigationSchema, StudyStepNavigationSchema
from rssa_api.data.services import StepPageService, StudyStepService
from rssa_api.data.services.rssa_dependencies import get_step_page_service as page_service
from rssa_api.data.services.rssa_dependencies import get_study_step_service as step_service

router = APIRouter(
    prefix='/steps',
    tags=['Study steps'],
    dependencies=[Depends(validate_api_key)],
)


@router.get(
    '/{step_id}',
    response_model=StudyStepNavigationSchema,
    summary='Get the step specified by an ID',
    description="""
	Retrieves the step specified by an ID.

	- This endpoint is used by a frontend study application to get the current step details.
	- Responds with a **404 error** if the step ID does not exist. This should never happen.
	""",
    response_description='The study step.',
)
async def get_study_step(
    step_id: uuid.UUID,
    service: Annotated[StudyStepService, Depends(step_service)],
    page_service: Annotated[StepPageService, Depends(page_service)],
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
):
    """Retrieves a step from the database via the StudyStepService.

    Args:
            step_id: The UUID of the study step to retrieve.
            service: The dependency-injected study step service.

    Returns:
            StudyStepSchema: The study step object if found.

    Raises:
            HTTPException: 404 if the study step is not found. However, this should never be raised since there are other
                    exception that will be through before we get here.
    """
    step = await service.get_step_with_navigation(step_id)
    if step is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Step not found!')
    if step.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Step not valid for this study.')

    if step.step_type == 'survey':
        first_page = await page_service.get_first_page_in_step(step_id)
        if first_page:
            step.survey_api_root = str(first_page.id)

    return step


@router.get('/{step_id}/pages/first', response_model=PageNavigationSchema)
async def get_first_page_endpoint(
    step_id: uuid.UUID,
    service: Annotated[StepPageService, Depends(page_service)],
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
):
    """Convenient routing to the StudySteps resources to access survey pages.

    Args:
            step_id (uuid.UUID): The UUID for StudyStep

    Raises:
            HTTPException:

    Returns:
            SurveyPageSchema: The full content of the first survey page for the survey step.
    """

    first_page = await service.get_first_page_with_navitation(step_id)
    if not first_page:
        raise HTTPException(status_code=404, detail='No first page found for this step or step not in study.')

    if first_page.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Step not valid for this study.')

    return first_page
