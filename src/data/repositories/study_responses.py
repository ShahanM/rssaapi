from sqlalchemy.orm import Session


class StudyResponseRepository:
	def __init__(self, db: Session):
		self.db = db
