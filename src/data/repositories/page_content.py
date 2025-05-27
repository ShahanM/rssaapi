def create_page_content(
	db: Session, page_id: uuid.UUID, content_id: uuid.UUID, order_position: int
) -> PageContentSchema:
	page = db.query(Page).where(Page.id == page_id).first()
	if not page:
		raise Exception('Page not found')

	page = StepPageSchema.model_validate(page)

	content = db.query(SurveyConstruct).where(SurveyConstruct.id == content_id).first()
	if not content:
		raise Exception('Content not found')

	content = SurveyConstructSchema.model_validate(content)

	# Check to see if the content is already in the page
	existing = (
		db.query(PageContent).where(and_(PageContent.page_id == page_id, PageContent.content_id == content_id)).first()
	)

	if existing:
		return existing

	page_content = PageContent(page_id=page.id, content_id=content.id, order_position=order_position)
	db.add(page_content)
	db.commit()
	db.refresh(page_content)

	return page_content


def get_first_survey_page(db: Session, step_id: uuid.UUID) -> StepPageSchema:
	page = db.query(Page).filter(Page.step_id == step_id).order_by(Page.order_position).first()

	return page


def get_survey_page(db: Session, page_id: uuid.UUID) -> Page:
	page = db.query(Page).where(Page.id == page_id).first()

	return page


def get_page_content(db: Session, page_id: uuid.UUID) -> List[SurveyConstructSchema]:
	query = (
		select(SurveyConstruct, ConstructType)
		.join(PageContent, SurveyConstruct.id == PageContent.content_id)
		.join(ConstructType, SurveyConstruct.type == ConstructType.id)
		.where(PageContent.page_id == page_id)
	)
	# constructs = db.query(SurveyConstruct)\
	# 	.join(SurveyConstruct, )\
	# 	.join(ConstructType)\
	# 	.where(PageContent.page_id == page_id).all()
	constructs = db.execute(query).all()
	# query = select(SurveyConstruct, ConstructType)\

	svyconstructs: List[SurveyConstructSchema] = []
	for construct in constructs:
		svyconstruct = construct[0]
		construct_type = construct[1]
		svyconstructs.append(
			SurveyConstructSchema(
				id=svyconstruct.id,
				name=svyconstruct.name,
				desc=svyconstruct.desc,
				type=construct_type,
				scale=svyconstruct.scale,
			)
		)

	# return svyconstructs
	return svyconstructs
