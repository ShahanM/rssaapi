import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from data.schemas.survey_construct_schemas import (
	ConstructDetailSchema,
	ConstructSummarySchema,
	SurveyConstructCreateSchema,
	SurveyConstructSchema,
)
from data.services.rssa_dependencies import get_survey_construct_service as construct_service
from data.services.survey_construct_service import SurveyConstructService
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.resources.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2/admin/constructs',
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


@router.get('/', response_model=List[SurveyConstructSchema])
async def get_survey_constructs(
	service: Annotated[SurveyConstructService, Depends(construct_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	constructs_in_db = await service.get_survey_constructs()
	converted = [SurveyConstructSchema.model_validate(c) for c in constructs_in_db]

	return converted


@router.get('/{construct_id}/summary', response_model=ConstructSummarySchema)
async def get_construct_summary(
	construct_id: uuid.UUID,
	service: Annotated[SurveyConstructService, Depends(construct_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	construct_in_db = await service.get_construct_summary(construct_id)

	return ConstructSummarySchema.model_validate(construct_in_db)


@router.get('/{construct_id}', response_model=ConstructDetailSchema)
async def get_construct_detail(
	construct_id: uuid.UUID,
	service: Annotated[SurveyConstructService, Depends(construct_service)],
):
	construct_in_db = await service.get_construct_details(construct_id)
	print('Construct DEETS: ', construct_in_db.__dict__)
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
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to do perform that action.'
		)
	await service.delete_survey_construct(construct_id)

	return {'message': 'Survey construct deleted.'}
