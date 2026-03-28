"""Router for study page endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_api_key
from rssa_api.data.schemas.study_components import NavigationWrapper, StudyStepPagePresent
from rssa_api.data.services.dependencies import StudyStepPageServiceDep

router = APIRouter(
    prefix='/pages',
    tags=['Step pages'],
    dependencies=[Depends(validate_api_key)],
)


@router.get(
    '/{page_id}',
    response_model=NavigationWrapper[StudyStepPagePresent],
)
async def get_step_page_details(
    page_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
):
    """Get details for a specific page.

    Args:
        page_id: UUID of the page.
        page_service: Service for page operations.
        study_id: Authorized study UUID.

    Returns:
        Page details with navigation info.
    """
    page_result = await page_service.get_with_navigation(page_id, StudyStepPagePresent)
    if page_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Page was not found, study configuration fault.'
        )

    validated_page = StudyStepPagePresent.model_validate(page_result['current'])

    if validated_page.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Step not valid for this study.')

    step_page = NavigationWrapper[StudyStepPagePresent](
        data=validated_page,
        next_id=page_result['next_id'],
        next_path=page_result['next_path'],
    )
    return step_page
