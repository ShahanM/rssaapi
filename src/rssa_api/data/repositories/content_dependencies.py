"""Content Dependencies Repository."""

from typing import Annotated

from fastapi import Depends
from rssa_storage.moviedb.repositories import MovieRepository
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.moviedb import get_db


def get_movie_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieRepository:
    """Get MovieRepository dependency."""
    return MovieRepository(db)


MovieRepositoryDep = Annotated[MovieRepository, Depends(get_movie_repository)]
