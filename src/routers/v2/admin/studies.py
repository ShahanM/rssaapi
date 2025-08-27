import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status

from data.schemas.base_schemas import ReorderPayloadSchema
from data.schemas.study_condition_schemas import StudyConditionSchema
from data.schemas.study_schemas import (
	StudyConfigSchema,
	StudyCreateSchema,
	StudyDetailSchema,
	StudySchema,
	StudySummarySchema,
)
from data.schemas.study_step_schemas import StudyStepSchema
from data.services import StudyService
from data.services.rssa_dependencies import get_study_service as study_service
from routers.v2.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user, require_permissions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/admin/studies',
	tags=['Studies'],
	dependencies=[Depends(get_auth0_authenticated_user), Depends(study_service)],
)


@router.get(
	'/',
	response_model=list[StudySchema],
	summary='Get the list of all available studies',
	description="""
	Retrieves the list of all the studies that the current authenticated user has access to.

	- This endpoint is used to facilitate in the administration and organization of studies.
	- Responds with an empty list if the current authenticated user does not have the corrent authorization.
	""",
	response_description='The list of studies',
)
async def get_studies(
	study_service: Annotated[StudyService, Depends(study_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	"""Retrieves all studies in the database by filtering on access rights.

	The special permission 'admin:all' gets all studies.

	Args:
		study_service: The dependency injection for the study service.
		user: The dependency injection that tests whether the access token in the header is authorized.

	Returns:
		[]: Empty list if there are no studies to show.
	"""
	is_super_admin = 'admin:all' in user.permissions or 'read:studies' in user.permissions

	studies_from_db = []
	if is_super_admin:
		studies_from_db = await study_service.get_all_studies()
	else:
		studies_from_db = await study_service.get_studies_by_ownership(user.sub)

	converted_studies = [StudySchema.model_validate(study) for study in studies_from_db]

	return converted_studies


@router.get('/{study_id}/summary', response_model=StudySummarySchema)
async def get_study_summary(
	study_id: uuid.UUID,
	study_service: Annotated[StudyService, Depends(study_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	study_summary = await study_service.get_study_summary(study_id)

	if study_summary is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')
	return study_summary


@router.get('/{study_id}', response_model=StudyDetailSchema)
async def get_study_detail(
	study_id: uuid.UUID,
	study_service: Annotated[StudyService, Depends(study_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	study_from_db = await study_service.get_study_details(study_id)

	return StudyDetailSchema.model_validate(study_from_db)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_study(
	new_study: StudyCreateSchema,
	study_service: Annotated[StudyService, Depends(study_service)],
	user: Annotated[Auth0UserSchema, Depends(require_permissions('create:studies', 'admin:all'))],
):
	await study_service.create_new_study(new_study, user.sub)
	return {'message': 'Study created.'}


@router.get('/{study_id}/steps', response_model=List[StudyStepSchema])
async def get_study_steps(
	study_id: uuid.UUID,
	study_service: Annotated[StudyService, Depends(study_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	study_steps_from_db = await study_service.get_study_steps(study_id)

	converted_steps = [StudyStepSchema.model_validate(s) for s in study_steps_from_db]

	return converted_steps


@router.get('/{study_id}/conditions', response_model=List[StudyConditionSchema])
async def get_study_conditions(
	study_id: uuid.UUID,
	study_service: Annotated[StudyService, Depends(study_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	study_conditions_from_db = await study_service.get_study_conditions(study_id)

	converted_conditions = [StudyConditionSchema.model_validate(sc) for sc in study_conditions_from_db]

	return converted_conditions


@router.put('/{study_id}/steps/order', status_code=204)
async def reorder_study_steps(
	study_id: uuid.UUID,
	payload: list[ReorderPayloadSchema],
	study_service: Annotated[StudyService, Depends(study_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	steps_map = {item.id: item.order_position for item in payload}
	await study_service.reorder_study_steps(study_id, steps_map)

	return {'message': 'Steps reordered successfully'}


@router.get('/{study_id}/export_study_config', response_model=StudyConfigSchema)
async def export_study_config(
	study_id: uuid.UUID,
	study_service: Annotated[StudyService, Depends(study_service)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	study_details = await study_service.get_study_details(study_id)

	study_config = {
		'study_id': study_details.id,
		'study_steps': [
			{'name': step.name, 'id': step.id} for step in sorted(study_details.steps, key=lambda s: s.order_position)
		],
		'conditions': {cond.id: cond.name for cond in study_details.conditions},
	}

	return StudyConfigSchema.model_validate(study_config)
