import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.study_components import PageBaseSchema, PageSchema, StudyStepSchema
from rssa_api.data.services import StudyStepPageServiceDep, StudyStepServiceDep

from ...docs import ADMIN_STUDY_STEPS_TAG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix='/steps',
    tags=[ADMIN_STUDY_STEPS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user), Depends(get_auth0_authenticated_user)],
)


@router.get('/{step_id}', response_model=StudyStepSchema)
async def get_study_step(
    step_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    study_step = await step_service.get_study_step(step_id)
    if not study_step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    return study_step


@router.get('/{step_id}/pages', response_model=list[PageSchema])
async def get_pages_for_study_step(
    step_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('read:pages', 'admin:all'))],
):
    pages_from_db = await page_service.get_pages_for_step(step_id)

    return [PageSchema.model_validate(p) for p in pages_from_db]


@router.post('/{step_id}/pages', status_code=status.HTTP_201_CREATED)
async def create_page_for_step(
    step_id: uuid.UUID,
    new_page: PageBaseSchema,
    step_service: StudyStepServiceDep,
    page_service: StudyStepPageServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:pages', 'admin:all'))],
):
    study_step = await step_service.get_study_step(step_id)
    if not study_step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Something went wrong, step not found.')
    if study_step.step_type != 'survey':
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Step not a valid survey step.')
    await page_service.create_step_page(study_step.study_id, step_id, new_page)


@router.patch('/{step_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_study_step(
    step_id: uuid.UUID,
    payload: dict[str, str],
    step_service: StudyStepServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:steps'))],
):
    await step_service.update_study_step(step_id, payload)

    return {}


@router.delete('/{step_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_step(
    step_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:steps', 'admin:all'))],
):
    await step_service.delete_step(step_id)

    return {}
