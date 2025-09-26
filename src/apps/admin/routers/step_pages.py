import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from auth.security import get_auth0_authenticated_user, require_permissions
from data.schemas import Auth0UserSchema
from data.schemas.study_components import PageContentBaseSchema, PageContentSchema, PageSchema
from data.services import PageContentService, StepPageService, SurveyService
from data.services.rssa_dependencies import get_content_service as content_service
from data.services.rssa_dependencies import get_step_page_service as page_service
from data.services.rssa_dependencies import get_survey_service as survey_service
from docs.admin_docs import Tags

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix='/pages',
    tags=[Tags.page],
    dependencies=[Depends(get_auth0_authenticated_user), Depends(page_service)],
)


@router.get(
    '/{page_id}',
    response_model=PageSchema,
    summary='',
    description="""
	""",
    response_description='',
)
async def get_step_page_details(
    page_id: uuid.UUID,
    page_service: Annotated[StepPageService, Depends(page_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('read:pages', 'admin:all'))],
):
    page_from_db = await page_service.get_page_with_content_detail(page_id)
    return PageSchema.model_validate(page_from_db)


@router.patch(
    '/{page_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='',
    description="""
	""",
    response_description='',
)
async def update_step_page(
    page_id: uuid.UUID,
    updated_page: dict[str, str],
    page_service: Annotated[StepPageService, Depends(page_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:pages', 'admin:all'))],
):
    await page_service.update_step_page(page_id, updated_page)
    return {}


@router.delete(
    '/{page_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='',
    description="""
	""",
    response_description='',
)
async def delete_step_page(
    page_id: uuid.UUID,
    page_service: Annotated[StepPageService, Depends(page_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:pages', 'admin:all'))],
):
    await page_service.delete_step_page(page_id)

    return {}


@router.get(
    '/{page_id}/content',
    response_model=list[PageContentSchema],
    summary='',
    description='',
    response_description='',
)
async def get_page_content(
    page_id: uuid.UUID,
    content_service: Annotated[PageContentService, Depends(content_service)],
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('read:surveys', 'read:content')),
    ],
):
    content = await content_service.get_content_detail_by_page_id(page_id)

    return content


@router.post(
    '/{page_id}/content',
    status_code=status.HTTP_201_CREATED,
    summary='',
    description='',
    response_description='',
)
async def add_content_to_page(
    page_id: uuid.UUID,
    new_content: PageContentBaseSchema,
    content_service: Annotated[PageContentService, Depends(content_service)],
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('create:surveys', 'create:content')),
    ],
):
    await content_service.create_page_content(page_id, new_content)

    return {}
