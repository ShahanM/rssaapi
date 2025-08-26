from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from data.rssadb import get_db as rssa_db
from data.schemas.feedback_schemas import FeedbackCreateSchema
from data.schemas.study_schemas import StudySchema
from data.services.feedback_service import FeedbackService
from docs.metadata import ResourceTagsEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

router = APIRouter(
	prefix='/feedbacks',
	tags=[Tags.feedback],
)


@router.post('/', response_model=None)
async def create_feedback(
	feedback: FeedbackCreateSchema,
	db: AsyncSession = Depends(rssa_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	"""_summary_

	Args:
		feedback (FeedbackCreateSchema): _description_
		db (AsyncSession, optional): _description_. Defaults to Depends(rssa_db).
		current_study (StudySchema, optional): _description_. Defaults to Depends(get_current_registered_study).

	Raises:
		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_

	Returns:
		_type_: _description_
	"""
	feedback_service = FeedbackService(db)
	try:
		await feedback_service.create_feedback(study_id=current_study.id, feedback_data=feedback)
		return {'message': 'Feedback successfully recorded.'}
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
