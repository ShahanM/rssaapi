import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_api_key
from rssa_api.data.schemas.study_components import NavigationWrapper, StudyStepPageRead
from rssa_api.data.services import StudyStepPageServiceDep

router = APIRouter(
    prefix='/pages',
    tags=['Step pages'],
    dependencies=[Depends(validate_api_key)],
)


@router.get(
    '/{page_id}',
    response_model=NavigationWrapper[StudyStepPageRead],
)
async def get_step_page_details(
    page_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    study_id: Annotated[uuid.UUID, Depends(validate_api_key)],
):
    page_result = await page_service.get_with_navigation(page_id)
    if page_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Page was not found, study configuration fault.'
        )

    validated_page = StudyStepPageRead.model_validate(page_result['current'])

    if validated_page.study_id != study_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Step not valid for this study.')

    # page_content = await content_service.get_content_detail_by_page_id(page_id)

    # survey_page = page.model_dump()
    # survey_page['page_content'] = page_content

    # return SurveyPage.model_validate(survey_page)
    step_page = NavigationWrapper[StudyStepPageRead](
        data=validated_page,
        next_id=page_result['next_id'],
        next_path=page_result['next_path'],
    )
    return step_page
