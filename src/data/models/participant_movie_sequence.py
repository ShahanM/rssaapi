import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import DateTime, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.base import RSSADBBase as Base


class PreShuffledMovieList(Base):
    """
    SQLAlchemy model for the 'pre_shuffled_movie_lists' table.
    Stores pre-generated, fully shuffled lists of movie UUIDs.
    """

    __tablename__ = 'pre_shuffled_movie_lists'

    list_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # SERIAL PRIMARY KEY
    movie_ids: Mapped[List[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False)
    subset_desc: Mapped[str] = mapped_column()
    seed: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return (
            f'<PreShuffledMovieList(list_id={self.list_id}, num_movies={len(self.movie_ids) if self.movie_ids else 0})>'
        )

    def __init__(self, movie_ids: List[uuid.UUID], subset_desc: str, seed: int):
        self.movie_ids = movie_ids
        self.subset_desc = subset_desc
        self.seed = seed


class ParticipantMovieSession(Base):
    """
    SQLAlchemy model for the 'participant_movie_sessions' table.
    Tracks each participant's assigned movie list and their current progress.
    """

    __tablename__ = 'participant_movie_sessions'

    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)  # UUID PRIMARY KEY

    assigned_list_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('pre_shuffled_movie_lists.list_id'), nullable=False
    )

    current_offset: Mapped[int] = mapped_column(Integer, server_default=text('0'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    assigned_list: Mapped[PreShuffledMovieList] = relationship(PreShuffledMovieList, lazy='joined')

    def __repr__(self):
        return (
            f'<ParticipantMovieSession(participant_id={self.participant_id}, '
            f'assigned_list_id={self.assigned_list_id}, offset={self.current_offset})>'
        )

    def __init__(self, participant_id: uuid.UUID, assigned_list_id: int):
        self.participant_id = participant_id
        self.assigned_list_id = assigned_list_id
