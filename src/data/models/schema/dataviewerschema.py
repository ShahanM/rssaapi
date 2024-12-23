from pydantic import BaseModel
from typing import List, Union
from data.models.schema.userschema import UserTypeSchema, DemographicInfoSchema

class UserDetailSchema(BaseModel):
	id: int

	study_id: int
	condition: int
	completed: bool
	user_type: str
	age_group: Union[str, None]
	gender: Union[str, None]
	education: Union[str, None]

	class Config:
		from_attributes = True