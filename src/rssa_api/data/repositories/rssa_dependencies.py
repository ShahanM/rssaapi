"""RSSA Dependencies Repository."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rssa_api.data.repositories.study_admin.api_key_repo import ApiKeyRepository
from rssa_api.data.rssadb import get_db

from .study_admin.pre_shuffled_movie_list import PreShuffledMovieRepository
from .study_admin.user_repo import UserRepository


def get_pre_shuffled_movie_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PreShuffledMovieRepository:
    """Get PreShuffledMovieRepository dependency."""
    return PreShuffledMovieRepository(db)


def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    """Get UserRepository dependency."""
    return UserRepository(db)


def get_api_key_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKeyRepository:
    """Get ApiKeyRepository dependency."""
    return ApiKeyRepository(db)
