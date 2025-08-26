import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from data.schemas.survey_construct_schemas import ConstructItemCreateSchema, ConstructItemSchema
from data.services import ConstructItemService
from data.services.survey_dependencies import get_construct_item_service as item_service
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user, require_permissions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/admin/items',
	tags=[Tags.construct],
	dependencies=[
		Depends(item_service),
		Depends(get_auth0_authenticated_user),
		Depends(require_permissions('read:constructs')),
	],
)


@router.get('/{item_id}', response_model=ConstructItemSchema)
async def get_item(
	item_id: uuid.UUID,
	service: Annotated[ConstructItemService, Depends(item_service)],
):
	item_in_db = await service.get_construct_item(item_id)

	return ConstructItemSchema.model_validate(item_in_db)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_construct_item(
	new_item: ConstructItemCreateSchema,
	service: Annotated[ConstructItemService, Depends(item_service)],
):
	await service.create_construct_item(new_item)

	return {'message': 'Construct item created.'}


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
