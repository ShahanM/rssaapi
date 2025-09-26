import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from auth.authorization import authorize_api_key_for_study, validate_api_key
from data.schemas.study_components import PageNavigationSchema, StudyStepNavigationSchema
from data.services import StepPageService, StudyStepService
from data.services.rssa_dependencies import get_step_page_service as page_service
from data.services.rssa_dependencies import get_study_step_service as step_service
from docs.rssa_docs import Tags

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix='/steps',
    tags=[Tags.survey],
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


# @router.get('/{step_id}/pages/{current_page_id}/next', response_model=SurveyPageSchema)
# async def get_next_page_endpoint(
# 	current_page_id: uuid.UUID,
# 	service: Annotated[SurveyService, Depends(survey_service)],
# 	current_study: Annotated[StudySchema, Depends(get_current_registered_study)],
# ):
# 	next_page = await service.get_next_survey_page(current_study.id, current_page_id)

# 	if not next_page:
# 		raise HTTPException(
# 			status_code=404, detail='No next page found for this current page or page not found in study/step.'
# 		)

# 	is_last_page = await service.is_last_page_in_step(next_page)
# 	page_to_return = SurveyPageSchema.model_validate(next_page)
# 	page_to_return.last_page = is_last_page

# 	return page_to_return
