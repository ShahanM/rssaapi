import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends

from data.schemas.study_condition_schemas import StudyConditionCreateSchema, StudyConditionSchema
from data.services import StudyConditionService
from data.services.rssa_dependencies import get_study_condition_service as conditions_service
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.resources.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2/admin/conditions',
	tags=[Tags.construct],
	dependencies=[Depends(get_auth0_authenticated_user), Depends(conditions_service)],
)


@router.get('/{condition_id}', response_model=StudyConditionSchema)
async def get_item(
	condition_id: uuid.UUID,
	service: Annotated[StudyConditionService, Depends(conditions_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	condition_in_db = await service.get_study_condition(condition_id)

	return StudyConditionSchema.model_validate(condition_in_db)


@router.post('/', response_model=StudyConditionSchema)
async def create_construct_item(
	new_condition: StudyConditionCreateSchema,
	service: Annotated[StudyConditionService, Depends(conditions_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	new_condition_in_db = await service.create_study_condition(new_condition)

	return StudyConditionSchema.model_validate(new_condition_in_db)
