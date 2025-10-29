from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.moviedb import get_db

from .movies import MovieRepository


def get_movie_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieRepository:
    return MovieRepository(db)
