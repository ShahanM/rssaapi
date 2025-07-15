import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends

from data.schemas.survey_construct_schemas import ConstructItemCreateSchema, ConstructItemSchema
from data.services.construct_item_service import ConstructItemService
from data.services.rssa_dependencies import get_construct_item_service as construct_item_service
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.resources.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2/admin/items',
	tags=[Tags.construct],
	dependencies=[Depends(get_auth0_authenticated_user), Depends(construct_item_service)],
)


@router.get('/{item_id}', response_model=ConstructItemSchema)
async def get_item(
	item_id: uuid.UUID,
	service: Annotated[ConstructItemService, Depends(construct_item_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	item_in_db = await service.get_construct_item(item_id)

	return ConstructItemSchema.model_validate(item_in_db)


@router.post('/', response_model=ConstructItemSchema)
async def create_construct_item(
	new_item: ConstructItemCreateSchema,
	service: Annotated[ConstructItemService, Depends(construct_item_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	new_item_in_db = await service.create_construct_item(new_item)

	return ConstructItemSchema.model_validate(new_item_in_db)
