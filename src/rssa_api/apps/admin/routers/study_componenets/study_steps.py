import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import OrderedListItem
from rssa_api.data.schemas.study_components import StudyStepPageCreate, StudyStepPageRead, StudyStepRead
from rssa_api.data.services import StudyStepPageServiceDep, StudyStepServiceDep

from ...docs import ADMIN_STUDY_STEPS_TAG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix='/steps',
    tags=[ADMIN_STUDY_STEPS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user), Depends(get_auth0_authenticated_user)],
)


@router.get('/{step_id}', response_model=StudyStepRead)
async def get_study_step(
    step_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    _: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    study_step = await step_service.get(step_id)
    if not study_step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')

    return study_step


@router.get('/{step_id}/pages', response_model=list[OrderedListItem])
async def get_pages_for_study_step(
    step_id: uuid.UUID,
    page_service: StudyStepPageServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:pages', 'admin:all'))],
):
    pages_from_db = await page_service.get_items_for_owner_as_ordered_list(step_id)

    return [OrderedListItem.model_validate(p) for p in pages_from_db]


@router.post('/{step_id}/pages', status_code=status.HTTP_201_CREATED, response_model=StudyStepPageRead)
async def create_page_for_step(
    step_id: uuid.UUID,
    new_page: StudyStepPageCreate,
    step_service: StudyStepServiceDep,
    page_service: StudyStepPageServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('create:pages', 'admin:all'))],
):
    step = await step_service.get(step_id)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study step not found.')
    created_page = await page_service.create_for_owner(step_id, new_page, study_id=step.study_id)
    page_dict = {
        'id': created_page.id,
        'created_at': created_page.created_at,
        'updated_at': created_page.updated_at,
        'enabled': created_page.enabled,
        'page_type': created_page.page_type,
        'name': created_page.name,
        'description': created_page.description,
        'title': created_page.title,
        'instructions': created_page.instructions,
        'created_by_id': created_page.created_by_id,
        'study_id': created_page.study_id,
        'study_step_id': created_page.study_step_id,
        'order_position': created_page.order_position,
        'study_step_page_contents': []
    }

    return StudyStepPageRead.model_validate(page_dict)


@router.patch('/{step_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_study_step(
    step_id: uuid.UUID,
    payload: dict[str, str],
    step_service: StudyStepServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('update:steps', 'admin:all'))],
):
    await step_service.update(step_id, payload)

    return {'Status': 'Success'}


@router.delete('/{step_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_step(
    step_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('delete:steps', 'admin:all'))],
):
    await step_service.delete(step_id)

    return {}
