"""SQLAlchemy models for participant movie sequences in the RSSA API."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.models.rssa_base_models import DBBaseModel


class PreShuffledMovieList(DBBaseModel):
    """SQLAlchemy model for the 'pre_shuffled_movie_lists' table.

    Stores pre-generated, fully shuffled lists of movie UUIDs.

    Attributes:
        list_id (int): Primary key, auto-incremented.
        movie_ids (List[uuid.UUID]): Ordered list of movie UUIDs.
        subset_desc (str): Description of the movie subset.
        seed (int): Seed used for shuffling.
        created_at (datetime): Timestamp of creation.
    """

    __tablename__ = 'pre_shuffled_movie_lists'

    movie_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False)
    subset_desc: Mapped[str] = mapped_column()
    seed: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        """String representation of PreShuffledMovieList."""
        return f'<PreShuffledMovieList(list_id={self.id}, num_movies={len(self.movie_ids) if self.movie_ids else 0})>'


class ParticipantMovieSession(DBBaseModel):
    """SQLAlchemy model for the 'participant_movie_sessions' table.

    Tracks each participant's assigned movie list and their current progress.

    Attributes:
        participant_id (uuid.UUID): Primary key, references the participant.
        assigned_list_id (int): Foreign key to the assigned pre-shuffled movie list.
        current_offset (int): Current position in the movie list.
        created_at (datetime): Timestamp of session creation.
        last_accessed_at (datetime): Timestamp of last access to the session.
    """

    __tablename__ = 'participant_movie_sessions'

    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('study_participants.id'), nullable=False
    )
    assigned_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('pre_shuffled_movie_lists.id'), nullable=False
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
        """String representation of ParticipantMovieSession."""
        return (
            f'<ParticipantMovieSession(participant_id={self.participant_id}, '
            f'assigned_list_id={self.assigned_list_id}, offset={self.current_offset})>'
        )
