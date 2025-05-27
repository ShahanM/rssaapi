from typing import Union

from pydantic import BaseModel


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
