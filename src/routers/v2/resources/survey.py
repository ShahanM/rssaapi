import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.study import Study
from data.rssadb import get_db as rssa_db
from data.schemas.study_schemas import StudyAuthSchema, StudySchema
from data.schemas.study_step_schemas import NextStepRequest, StudyStepSchema
from data.schemas.survey_schemas import SurveyPageSchema
from data.services.study_service import StudyService
from data.services.survey_service import SurveyService
from docs.metadata import TagsMetadataEnum as Tags
from routers.v2.resources.authorization import get_current_registered_study

router = APIRouter(
	prefix='/v2',
	tags=[Tags.study],
)


"""Step paging endpoint specifically for survey steps

	Raises:
		HTTPException 404: _description_
		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_
		HTTPException: _description_

	Returns:
		SurveyPageSchema: _description_
"""


@router.get('/survey/{step_id}/first', response_model=SurveyPageSchema)
async def retrieve_survey_page(
	step_id: uuid.UUID,
	db: AsyncSession = Depends(rssa_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	survey_service = SurveyService(db)
	# page = get_first_survey_page(db, step_id)
	# if not page:
	# raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No survey page found')

	# construct = get_page_content(db, page.id)
	# if len(construct) == 0:
	# 	raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No construct found for survey page')
	# construct = construct[0]  # FIXME: We currently only support one construct per page
	# items = get_construct_items(db, construct.id)
	# scalelevels = get_construct_scale_levels(db, construct.scale)

	# survey = SurveyPageSchema(
	# 	step_id=page.step_id,
	# 	page_id=page.id,
	# 	order_position=page.order_position,
	# 	construct_id=construct.id,
	# 	construct_items=[ConstructItemSchema.from_orm(item) for item in items],
	# 	construct_scale=[ScaleLevelSchema.from_orm(level) for level in scalelevels],
	# )

	return survey


@router.get('/survey/{page_id}', response_model=SurveyPageSchema)
async def retrieve_survey_page_by_id(
	page_id: uuid.UUID,
	db: Session = Depends(rssa_db.get_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	page = get_survey_page(db, page_id)
	if not page:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No survey page found')

	constructs = get_page_content(db, page.id)
	if len(constructs) == 0:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No construct found for survey page')

	construct = constructs[0]  # FIXME: We currently only support one construct per page
	items = get_construct_items(db, construct.id)
	assert construct.scale is not None
	scalelevels = get_construct_scale_levels(db, construct.scale)

	survey = SurveyPageSchema(
		step_id=page.step_id,
		page_id=page.id,
		order_position=0,
		construct_id=construct.id,
		construct_items=[ConstructItemSchema.from_orm(item) for item in items],
		construct_scale=sorted([ScaleLevelSchema.from_orm(level) for level in scalelevels], key=lambda x: x.level),
	)

	return survey


@router.get('/page/{page_id}', response_model=PageMultiConstructSchema)
async def retrieve_page_content(
	page_id: uuid.UUID,
	db: Session = Depends(rssa_db.get_db),
	current_study: StudySchema = Depends(get_current_registered_study),
):
	page = get_survey_page(db, page_id)
	if not page:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No page found')

	constructs = get_page_content(db, page.id)
	if len(constructs) == 0:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No construct found for page')

	page_constructs = []
	for construct in constructs:
		print(construct)
		items = get_construct_items(db, construct.id)
		print(items)
		constructdetail = TextConstructSchema(
			id=construct.id,
			name=construct.name,
			desc=construct.desc,
			type=construct.type.id,
			items=ConstructItemSchema.from_orm(items[0]),
		)
		page_constructs.append(constructdetail)

	multipage = PageMultiConstructSchema(
		page_id=page.id, step_id=page.step_id, order_position=page.order_position, constructs=page_constructs
	)

	return multipage
