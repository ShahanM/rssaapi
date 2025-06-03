from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.study_schemas import StudySchema
from data.schemas.survey_response_schemas import SurveyReponseCreateSchema
from data.services.response_service import ParticipantResponseService
from docs.metadata import TagsMetadataEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

router = APIRouter(
	prefix='/v2',
	tags=[Tags.study],
)


@router.post('/response/survey', response_model=None)
async def get_first_page_endpoint(
	survey_response: SurveyReponseCreateSchema,
	db: AsyncSession = Depends(rssa_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	survey_response_service = ParticipantResponseService(db)
	try:
		await survey_response_service.insert_survey_item_response(survey_response_data=survey_response)
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
