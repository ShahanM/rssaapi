from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.study_schemas import StudySchema
from data.schemas.survey_response_schemas import FreeformTextResponseCreateSchema, SurveyReponseCreateSchema
from data.services.response_service import ParticipantResponseService
from docs.metadata import ResourceTagsEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

router = APIRouter(
	prefix='/v2',
	tags=[Tags.response],
)


@router.post('/responses/survey', response_model=None)
async def create_survey_item_response(
	survey_response: SurveyReponseCreateSchema,
	db: AsyncSession = Depends(rssa_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	"""_summary_

	Args:
		survey_response (SurveyReponseCreateSchema): _description_
		current_study (StudySchema, optional): _description_. Defaults to Depends(get_current_registered_study).

	Raises:
		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_

	Returns:
		_type_: _description_
	"""
	response_service = ParticipantResponseService(db)
	try:
		await response_service.create_survey_item_response(current_study.id, survey_response_data=survey_response)
		return {'message': 'Survey response successfully recorded.'}
	except IntegrityError as e:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f'Failed to record survey response due to data integrity issue: {e.orig}',
		) from e
	except SQLAlchemyError as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'An unexpected database error occurred: {e}'
		) from e
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'An unexpected error occurred: {e}'
		) from e


@router.post('/responses/text', response_model=None)
async def create_freeform_text_response(
	text_response: FreeformTextResponseCreateSchema,
	db: AsyncSession = Depends(rssa_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	"""Freeform text response endpoint.

	Endpoint to record participant response which is not part of a survey or a pre-defined scale.
	May also be used for study specific interaction response that can defined by the frontend.

	Args:

		text_response (FreeformTextResponseCreateSchema): The payload containing the response data.
		current_study (StudySchema): Depends on the header including the correct study_id.

	Raises:

		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_
	"""
	response_service = ParticipantResponseService(db)
	try:
		await response_service.create_freeform_text_response(current_study.id, text_response)
	except IntegrityError as e:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f'Failed to record survey response due to data integrity issue: {e.orig}',
		) from e
	except SQLAlchemyError as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'An unexpected database error occurred: {e}'
		) from e
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'An unexpected error occurred: {e}'
		) from e
