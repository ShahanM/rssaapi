from sqlalchemy.ext.asyncio import AsyncSession

from data.models.survey_constructs import SurveyConstruct
from data.repositories.base_repo import BaseRepository


class SurveyConstructRepository(BaseRepository[SurveyConstruct]):
	def __init__(self, db: AsyncSession):
		super().__init__(db, SurveyConstruct)


# def get_survey_constructs(db: Session) -> List[SurveyConstructSchema]:
# 	constructs = (
# 		db.query(SurveyConstruct, ConstructType)
# 		.join(ConstructType)
# 		.filter(SurveyConstruct.type == ConstructType.id)
# 		.all()
# 	)
# 	print(constructs)
# 	# constructs = db.query(SurveyConstruct).all()
# 	svyconstructs = []
# 	for construct in constructs:
# 		svyconstruct = construct.SurveyConstruct
# 		construct_type = construct.ConstructType
# 		svyconstructs.append(
# 			SurveyConstructSchema(
# 				id=svyconstruct.id,
# 				name=svyconstruct.name,
# 				desc=svyconstruct.desc,
# 				type=construct_type,
# 				scale=svyconstruct.scale,
# 			)
# 		)

# 	return svyconstructs


# def get_survey_construct_by_id(db: Session, construct_id: uuid.UUID) -> SurveyConstruct:
# 	construct = db.query(SurveyConstruct).where(SurveyConstruct.id == construct_id).first()
# 	if not construct:
# 		raise HTTPException(status_code=404, detail='Construct not found')

# 	# if not construct.items:
# 	# construct.items = []

# 	# svyconstruct = construct[0]
# 	# construct_type = construct[1]

# 	# return SurveyConstructSchema(id=svyconstruct.id, name=svyconstruct.name,
# 	# desc=svyconstruct.desc, type=construct_type)

# 	return construct


# def create_survey_construct(
# 	db: Session, name: str, desc: str, type_id: uuid.UUID, scale_id: uuid.UUID
# ) -> SurveyConstruct:
# 	ctype = get_construct_type_by_id(db, type_id)
# 	cscale = get_construct_scale_by_id(db, scale_id)
# 	construct = SurveyConstruct(name=name, desc=desc, type_id=ctype.id, scale_id=cscale.id)
# 	db.add(construct)
# 	db.commit()
# 	db.refresh(construct)

# 	# svyconstruct = SurveyConstructSchema(id=construct.id, name=construct.name,
# 	# 			desc=construct.desc, type=ConstructTypeSchema.from_orm(ctype))

# 	return construct


# def create_text_construct(db: Session, name: str, desc: str, type_id: uuid.UUID) -> SurveyConstruct:
# 	ctype = get_construct_type_by_id(db, type_id)
# 	construct = SurveyConstruct(name=name, desc=desc, type_id=ctype.id)
# 	db.add(construct)
# 	db.commit()
# 	db.refresh(construct)

# 	# svyconstruct = SurveyConstructSchema(id=construct.id, name=construct.name,
# 	# 				desc=construct.desc, type=ConstructTypeSchema.from_orm(ctype))

# 	return construct


# def update_survey_construct(
# 	db: Session, construct_id: uuid.UUID, name: str, desc: str, construct_type: uuid.UUID, construct_scale: uuid.UUID
# ) -> bool:
# 	updated = False
# 	construct = get_survey_construct_by_id(db, construct_id)

# 	if name:
# 		construct.name = name
# 		updated = True

# 	if desc:
# 		construct.desc = desc
# 		updated = True

# 	if construct_type:
# 		ctype = get_construct_type_by_id(db, construct_type)
# 		construct.type = ctype.id
# 		updated = True

# 	if construct_scale:
# 		cscale = get_construct_scale_by_id(db, construct_scale)
# 		construct.scale = cscale.id
# 		updated = True

# 	if updated:
# 		db.commit()
# 		db.refresh(construct)

# 	return updated


# def get_construct_types(db: Session) -> List[ConstructType]:
# 	item_types = db.query(ConstructType).all()

# 	return item_types


# def get_construct_type_by_id(db: Session, type_id: uuid.UUID) -> ConstructType:
# 	item_type = db.query(ConstructType).where(ConstructType.id == type_id).first()
# 	if not item_type:
# 		raise HTTPException(status_code=404, detail='Type not found')

# 	return item_type


# def create_construct_type(db: Session, type: str) -> ConstructType:
# 	item_type = ConstructType(type=type)
# 	db.add(item_type)
# 	db.commit()
# 	db.refresh(item_type)

# 	return item_type


# def get_construct_scales(db: Session) -> List[ConstructScale]:
# 	scales = db.query(ConstructScale).all()

# 	return scales


# def get_construct_scale_by_id(db: Session, scale_id: uuid.UUID) -> ConstructScale:
# 	scale = db.query(ConstructScale).where(ConstructScale.id == scale_id).first()
# 	if not scale:
# 		raise HTTPException(status_code=404, detail='Scale not found')

# 	return scale


# def create_construct_scale(
# 	db: Session, levels: int, name: str, scale_levels: List[NewScaleLevelSchema]
# ) -> ConstructScale:
# 	scale = ConstructScale(levels=levels, name=name)
# 	db.add(scale)
# 	db.flush()
# 	db.refresh(scale)

# 	assert len(scale_levels) == levels
# 	for scale_level in scale_levels:
# 		new_scale_level = ScaleLevel(level=scale_level.level, label=scale_level.label, scale_id=scale.id)
# 		db.add(new_scale_level)

# 	db.commit()
# 	db.refresh(scale)

# 	return scale


# def get_construct_scale_levels(db: Session, scale_id: uuid.UUID) -> List[ScaleLevel]:
# 	levels = db.query(ScaleLevel).where(ScaleLevel.scale_id == scale_id).all()

# 	return levels


# def create_construct_item_type(db: Session, type: str) -> ConstructItemType:
# 	item_type = ConstructItemType(type=type)
# 	db.add(item_type)
# 	db.commit()
# 	db.refresh(item_type)

# 	return item_type


# def get_item_type_by_id(db: Session, type_id: uuid.UUID) -> ConstructItemType:
# 	item_type = db.query(ConstructItemType).where(ConstructItemType.id == type_id).first()
# 	if not item_type:
# 		raise HTTPException(status_code=404, detail='Type not found')

# 	return item_type


# def get_item_types(db: Session) -> List[ConstructItemType]:
# 	types = db.query(ConstructItemType).all()

# 	return types


# def create_item_type(db: Session, type: str) -> ConstructItemType:
# 	item_type = ConstructItemType(type=type)
# 	db.add(item_type)
# 	db.commit()
# 	db.refresh(item_type)

# 	return item_type


# def create_construct_item(
# 	db: Session, construct_id: uuid.UUID, item_type: uuid.UUID, text: str, order_position: int
# ) -> ConstructItem:
# 	construct = get_survey_construct_by_id(db, construct_id)
# 	itype = get_item_type_by_id(db, item_type)
# 	item = ConstructItem(construct_id=construct.id, text=text, order_position=order_position, item_type=itype.id)
# 	db.add(item)
# 	db.commit()
# 	db.refresh(item)

# 	return item


# def get_construct_items(db: Session, construct_id: uuid.UUID) -> List[ConstructItem]:
# 	items = db.query(ConstructItem).where(ConstructItem.construct_id == construct_id).all()

# 	return items
