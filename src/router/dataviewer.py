from fastapi import APIRouter, Depends

from data.models.schema.studyschema import *
from data.models.schema.userschema import *
from data.models.schema.movieschema import *
from data.models.schema.dataviewerschema import *

from data.users import *
from data.studies import *
from data.movies import *

from docs.metadata import TagsMetadataEnum as Tags

from .study import get_db as study_db
from .users import get_db as user_db

router = APIRouter(include_in_schema=False)

@router.get("/user/{user_id}", response_model=UserSchema, tags=['dataviewer'])
async def get_rssa_user(user_id: int, db: Session = Depends(user_db)):
	user = get_user(db, user_id)
	return user


@router.get("/user/", response_model=List[UserDetailSchema], 
	tags=['dataviewer'])
async def get_user_report(study_id: int, db: Session = Depends(user_db)):
	users = get_study_users(db, study_id)
	print(users)
	# demos = get_demographic_info(db)

	userlst = []
	for user in users:
		age_group = user.demographic_info.age_group if user.demographic_info else None
		gender = user.demographic_info.gender if user.demographic_info else None
		education = user.demographic_info.education if user.demographic_info else None
		user_type = user.user_type.type_str
		pydanticUser = UserSchema.from_orm(user)
		userschema = UserDetailSchema(id=pydanticUser.id, \
			study_id=pydanticUser.study_id, \
			condition=pydanticUser.condition, \
			completed=pydanticUser.completed, \
			user_type=user_type, \
			age_group=age_group, \
			gender=gender, \
			education=education)
		userlst.append(userschema)
	# userdict = {user.id: user for user in users}
	# for demo in demos:
	# 	print(userdict[demo.user_id])
	# 	userdata =  userdict[demo.user_id]
	# 	print(userdata.demographic_info)
	# 	usr_schema = UserDetailSchema(**userdict[demo.user_id], **demo)
	# 	userlst.append(usr_schema)

	return userlst