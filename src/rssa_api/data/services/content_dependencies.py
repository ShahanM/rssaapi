from typing import Annotated

from fastapi import Depends
from rssa_storage.moviedb.repositories import MovieRepository

from rssa_api.data.repositories.content_dependencies import get_movie_repository

from .movie_service import MovieService


def get_movie_service(
    movie_repo: Annotated[MovieRepository, Depends(get_movie_repository)],
) -> MovieService:
    return MovieService(movie_repo)
