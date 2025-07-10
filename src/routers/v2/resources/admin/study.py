import logging
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.study_condition_schemas import StudyConditionSchema
from data.schemas.study_schemas import StudyCreateSchema, StudyDetailSchema, StudySchema, StudySummarySchema
from data.schemas.study_step_schemas import StepsReorderItem, StudyStepSchema
from data.services.study_service import StudyService
from docs.metadata import AdminTagsEnum as Tags
from routers.v2.resources.admin.auth0 import Auth0UserSchema, get_auth0_authenticated_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


router = APIRouter(
	prefix='/v2/admin/studies',
	tags=[Tags.study],
	dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get('/', response_model=List[StudySchema])
async def get_studies(
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	"""_summary_
	Args:
		db (Annotated[AsyncSession, Depends): _description_
		user (Annotated[Auth0UserSchema, Depends): _description_

	Returns:
		_type_: _description_
	"""
	is_super_admin = 'admin:all' in user.permissions
	study_service = StudyService(db)

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
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	study_service = StudyService(db)

	study_summary = await study_service.get_study_summary(study_id)
	return study_summary


@router.get('/{study_id}', response_model=StudyDetailSchema)
async def get_study_detail(
	study_id: uuid.UUID,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	study_service = StudyService(db)

	study_from_db = await study_service.get_study_details(study_id)

	return StudyDetailSchema.model_validate(study_from_db)


@router.post('/', response_model=StudySchema)
async def create_study(
	new_study: StudyCreateSchema,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	"""_summary_

	Args:
		new_study (StudyCreateSchema): _description_
		db (Annotated[AsyncSession, Depends): _description_
		user (Annotated[Auth0UserSchema, Depends): _description_

	Raises:
		HTTPException: _description_

	Returns:
		_type_: _description_
	"""
	has_write_access = 'admin:all' in user.permissions or 'study:create' in user.permissions
	study_service = StudyService(db)

	if has_write_access:
		created_study = await study_service.create_new_study(new_study, user.sub)
		return created_study
	else:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to do perform that action.'
		)


@router.get('/{study_id}/steps', response_model=List[StudyStepSchema])
async def get_study_steps(
	study_id: uuid.UUID,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	"""_summary_

	Args:
		study_id (uuid.UUID): _description_
		db (Annotated[AsyncSession, Depends): _description_
		user (Annotated[Auth0UserSchema, Depends): _description_

	Returns:
		_type_: _description_
	"""
	study_service = StudyService(db)
	study_steps_from_db = await study_service.get_study_steps(study_id)

	converted_steps = [StudyStepSchema.model_validate(s) for s in study_steps_from_db]

	return converted_steps


@router.get('/{study_id}/conditions', response_model=List[StudyConditionSchema])
async def get_study_conditions(
	study_id: uuid.UUID,
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	study_service = StudyService(db)
	study_conditions_from_db = await study_service.get_study_conditions(study_id)

	converted_conditions = [StudyConditionSchema.model_validate(sc) for sc in study_conditions_from_db]

	return converted_conditions


@router.put('/{study_id}/steps/order', status_code=204)
async def reorder_study_steps(
	study_id: uuid.UUID,
	payload: List[StepsReorderItem],
	db: Annotated[AsyncSession, Depends(rssa_db)],
	user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
	step_service = StudyService(db)
	steps_map = {item.id: item.order_position for item in payload}
	await step_service.reorder_study_steps(study_id, steps_map)

	return {'message': 'Steps reordered successfully'}
