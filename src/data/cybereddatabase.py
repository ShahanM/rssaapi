from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

CYBERED_SQLALCHEMY_DATABASE_URL = "sqlite:///data/db/cyberedmoviedatabase.db"

engine = create_engine(
    CYBERED_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()