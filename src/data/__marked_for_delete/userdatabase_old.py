from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models.user import Base


def create_database_meta(study_id:  int):
    user_database_uri = "sqlite:///data/db/userdatabase_"  +  str (study_id) +  ".db"
    user_engine = create_engine(
        user_database_uri, connect_args={"check_same_thread": False}
	)
    # base = declarative_base()
    Base.metadata.create_all(bind=user_engine)


def get_user_db(study_id: int):
	user_database_uri = "sqlite:///data/db/userdatabase_"  +  str (study_id) +  ".db"
	user_engine = create_engine(
		user_database_uri, connect_args={"check_same_thread": False}
	)
	SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=user_engine)

	return SessionLocal()
