import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from data.schemas.base_schemas import ReorderPayloadSchema
from data.schemas.survey_construct_schemas import (
	ConstructDetailSchema,
	SurveyConstructCreateSchema,
	SurveyConstructSchema,
)
from data.services.survey_dependencies import SurveyConstructService
from data.services.survey_dependencies import get_survey_construct_service as construct_service
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/admin/constructs',
	tags=[Tags.construct],
	dependencies=[Depends(get_auth0_authenticated_user), Depends(construct_service)],
)


@router.post('/', response_model=SurveyConstructSchema)
async def create_survey_construct(
	new_construct: SurveyConstructCreateSchema,
	service: Annotated[SurveyConstructService, Depends(construct_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	is_super_admin = 'admin:all' in user.permissions
	if not is_super_admin:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to do perform that action.'
		)
	new_construct_in_db = await service.create_survey_construct(new_construct)

	return SurveyConstructSchema.model_validate(new_construct_in_db)


@router.get('/', response_model=list[SurveyConstructSchema])
async def get_survey_constructs(
	service: Annotated[SurveyConstructService, Depends(construct_service)],
):
	constructs_in_db = await service.get_survey_constructs()
	converted = [SurveyConstructSchema.model_validate(c) for c in constructs_in_db]

	return converted


@router.get('/{construct_id}/summary', response_model=SurveyConstructSchema)
async def get_construct_summary(
	construct_id: uuid.UUID,
	service: Annotated[SurveyConstructService, Depends(construct_service)],
):
	construct_in_db = await service.get_survey_construct(construct_id)

	if not construct_in_db:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, detail=f'Survey construct with ID {construct_id} not found.'
		)
	logger.info(f'Retrieved construct summary for ID {construct_id}: {construct_in_db}')

	return SurveyConstructSchema.model_validate(construct_in_db)


@router.get('/{construct_id}', response_model=ConstructDetailSchema)
async def get_construct_detail(
	construct_id: uuid.UUID,
	service: Annotated[SurveyConstructService, Depends(construct_service)],
):
	construct_in_db = await service.get_construct_details(construct_id)

	if not construct_in_db:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND, detail=f'Survey construct with ID {construct_id} not found.'
		)
	logger.info(f'Retrieved construct details for ID {construct_id}: {construct_in_db}')
	return ConstructDetailSchema.model_validate(construct_in_db)


@router.delete('/{construct_id}', status_code=204)
async def delete_construct(
	construct_id: uuid.UUID,
	service: Annotated[SurveyConstructService, Depends(construct_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	is_super_admin = 'admin:all' in user.permissions
	if not is_super_admin:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
		)
	await service.delete_survey_construct(construct_id)

	return {'message': 'Survey construct deleted.'}


@router.put('/{construct_id}/items/order', status_code=204)
async def update_scale_levels_order(
	construct_id: uuid.UUID,
	service: Annotated[SurveyConstructService, Depends(construct_service)],
	payload: list[ReorderPayloadSchema],
):
	levels_map = {item.id: item.order_position for item in payload}
	await service.reorder_items(construct_id, levels_map)
