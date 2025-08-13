import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from data.schemas.survey_construct_schemas import (
	ConstructScaleCreateSchema,
	ConstructScaleDetailSchema,
	ConstructScaleSchema,
	ConstructScaleSummarySchema,
	ReorderPayloadSchema,
	ScaleLevelSchema,
)
from data.services import ConstructScaleService
from data.services import get_construct_scale_service as scales_service
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.resources.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2/admin/construct-scales',
	tags=[Tags.construct],
	dependencies=[Depends(get_auth0_authenticated_user), Depends(scales_service)],
)


@router.get('/', response_model=List[ConstructScaleSchema])
async def get_construct_scales(
	service: Annotated[ConstructScaleService, Depends(scales_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	constructs_in_db = await service.get_construct_scales()
	converted = [ConstructScaleSchema.model_validate(c) for c in constructs_in_db]

	return converted


@router.post('/', response_model=ConstructScaleSchema)
async def create_construct_scale(
	create_scale: ConstructScaleCreateSchema,
	service: Annotated[ConstructScaleService, Depends(scales_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	is_super_admin = 'admin:all' in user.permissions
	if not is_super_admin:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
		)
	new_scale_in_db = await service.create_construct_scale(create_scale, created_by=user.sub)

	return ConstructScaleSchema.model_validate(new_scale_in_db)


@router.get('/{scale_id}/summary', response_model=ConstructScaleSummarySchema)
async def get_construct_scale(
	service: Annotated[ConstructScaleService, Depends(scales_service)],
	scale_id: uuid.UUID,
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	scale_in_db = await service.get_construct_scale(scale_id)
	if not scale_in_db:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Construct scale not found.')

	return ConstructScaleSummarySchema.model_validate(scale_in_db)


@router.get('/{scale_id}', response_model=ConstructScaleDetailSchema)
async def get_construct_scale_detail(
	service: Annotated[ConstructScaleService, Depends(scales_service)],
	scale_id: uuid.UUID,
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	scale_in_db = await service.get_construct_scale_detail(scale_id)
	if not scale_in_db:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Construct scale not found.')

	return ConstructScaleDetailSchema.model_validate(scale_in_db)


@router.delete('/{scale_id}', status_code=204)
async def delete_construct_scale(
	service: Annotated[ConstructScaleService, Depends(scales_service)],
	scale_id: uuid.UUID,
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	is_super_admin = 'admin:all' in user.permissions
	if not is_super_admin:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
		)

	await service.construct_scale_repo.delete(scale_id)


@router.get('/{scale_id}/levels', response_model=List[ScaleLevelSchema])
async def get_scale_levels(
	scale_id: uuid.UUID,
	service: Annotated[ConstructScaleService, Depends(scales_service)],
):
	levels_in_db = await service.get_scale_levels(scale_id)
	if not levels_in_db:
		return []
	converted = [ScaleLevelSchema.model_validate(c) for c in levels_in_db]

	return converted


@router.put('/{scale_id}/levels/order', status_code=204)
async def update_scale_levels_order(
	scale_id: uuid.UUID,
	service: Annotated[ConstructScaleService, Depends(scales_service)],
	payload: List[ReorderPayloadSchema],
):
	levels_map = {level.id: level.order_position for level in payload}
	await service.reorder_scale_levels(scale_id, levels_map)
