import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.survey_constructs import ConstructItemSchema
from rssa_api.data.services import ConstructItemService
from rssa_api.data.services.survey_dependencies import get_construct_item_service as item_service

from ..docs import ADMIN_CONSTRUCT_ITEMS_TAG

router = APIRouter(
    prefix='/items',
    tags=[ADMIN_CONSTRUCT_ITEMS_TAG],
    dependencies=[
        Depends(item_service),
        Depends(get_auth0_authenticated_user),
        Depends(require_permissions('read:constructs')),
    ],
)


@router.get(
    '/{item_id}',
    response_model=ConstructItemSchema,
    summary='',
    description="""
	""",
    response_description='',
)
async def get_item(
    item_id: uuid.UUID,
    service: Annotated[ConstructItemService, Depends(item_service)],
):
    item_in_db = await service.get_construct_item(item_id)

    return ConstructItemSchema.model_validate(item_in_db)


@router.delete('/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_construct_item(
    item_id: uuid.UUID,
    service: Annotated[ConstructItemService, Depends(item_service)],
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
        )
    await service.delete_construct_item(item_id)

    return {}
