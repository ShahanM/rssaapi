import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_components import Study
from data.models.study_participants import StudyParticipant
from data.rssadb import get_db as rssa_db
from data.schemas.study_schemas import StudySchema


async def get_current_registered_study(
	request: Request,
	db: AsyncSession = Depends(rssa_db),  # Use the same session as the route
) -> StudySchema:
	"""
	Retrieves the study based on the Study ID from the request header.
	Raises an HTTPException if the study ID is invalid or not found.
	"""
	study_id_header_value = request.headers.get('X-Study-Id')

	if not study_id_header_value:
		raise HTTPException(status_code=400, detail='Study ID header (X-Study-Id) is required')  # Corrected status code

	try:
		study_id = uuid.UUID(study_id_header_value)
	except ValueError:
		raise HTTPException(
			status_code=400, detail='Invalid Study ID format (must be a valid UUID)'
		) from None  # Corrected status code

	result = await db.execute(select(Study).where(Study.id == study_id))
	study = result.scalar_one_or_none()

	if not study:
		raise HTTPException(status_code=404, detail=f"Study with ID '{study_id}' not found")

	#  Validate the study against the schema.
	return StudySchema.model_validate(study, from_attributes=True)


async def get_current_participant_id(request: Request, db: AsyncSession = Depends(rssa_db)) -> uuid.UUID:
	participant_id_header_value = request.headers.get('X-Participant-Id')

	if not participant_id_header_value or participant_id_header_value == '':
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Participant ID header (X-Participant-Id) is required for this endpoint',
		)

	try:
		participant_id = uuid.UUID(participant_id_header_value)
	except ValueError:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid participant ID'
		) from None  # Corrected status code

	result = await db.execute(select(StudyParticipant).where(StudyParticipant.id == participant_id))
	participant = result.scalar_one_or_none()

	if not participant:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Participant not found')

	return participant_id
