import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study_v2 import Study
from data.rssadb import get_db as rssa_db
from data.schemas.study_schemas import StudyAuthSchema, StudySchema
from data.schemas.study_step_schemas import NextStepRequest, StudyStepSchema
from data.services.study_service import StudyService
from docs.metadata import TagsMetadataEnum as Tags

router = APIRouter(
	prefix='/v2',
	tags=[Tags.study],
)


@router.get('/step/{step_id}', response_model=StudyStepSchema, tags=[Tags.meta])
async def retrieve_steps(study_id: str, db: Session = Depends(rssa_db), current_user=Depends(auth0_user)):
	steps = get_study_steps(db, uuid.UUID(study_id))

	log_access(db, current_user.sub, 'read', 'steps for study', study_id)

	return steps


@router.post('/step/', response_model=StudyStepSchema, tags=[Tags.meta])
async def new_step(new_step: CreateStepSchema, db: Session = Depends(rssa_db), current_user=Depends(auth0_user)):
	step = create_study_step(db, **new_step.dict())
	log_access(db, current_user.sub, 'create', 'step', step.id)

	return step
