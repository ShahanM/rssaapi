import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from data.schemas.survey_construct_schemas import (
	ScaleLevelCreateSchema,
	ScaleLevelSchema,
)
from data.services import ScaleLevelService
from data.services.survey_dependencies import get_scale_level_service as scale_level_service
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/admin/scale-levels',
	tags=[Tags.construct],
	dependencies=[Depends(get_auth0_authenticated_user), Depends(scale_level_service)],
)


@router.post('/', response_model=ScaleLevelSchema)
async def create_scale_level(
	create_scale_level: ScaleLevelCreateSchema,
	service: Annotated[ScaleLevelService, Depends(scale_level_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	is_super_admin = 'admin:all' in user.permissions
	if not is_super_admin:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
		)
	new_scale_in_db = await service.create_scale_level(create_scale_level)

	return ScaleLevelSchema.model_validate(new_scale_in_db)


@router.delete('/{level_id}', status_code=204)
async def delete_scale_level(
	service: Annotated[ScaleLevelService, Depends(scale_level_service)],
	level_id: uuid.UUID,
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	is_super_admin = 'admin:all' in user.permissions
	if not is_super_admin:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
		)

	await service.delete_scale_level(level_id)
