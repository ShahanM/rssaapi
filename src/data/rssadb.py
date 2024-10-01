from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import config as cfg

dbuser = cfg.get_env_var("DB_USER")
dbpass = cfg.get_env_var("DB_PASSWORD")
dbhost = cfg.get_env_var("DB_HOST")
dbport = cfg.get_env_var("DB_PORT")
dbname = cfg.get_env_var("DB_NAME")

RSSA_DB = f'postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}?client_encoding=utf8'

engine = create_engine(RSSA_DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
