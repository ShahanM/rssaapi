"""SQLAlchemy models for study components in the RSSA API."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.models.rssa_base_models import BaseModelMixin, DBBaseModel, DBBaseOrderedModel
from rssa_api.data.models.survey_constructs import SurveyConstruct, SurveyScale


class Study(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'studies' table.

    Attributes:
        enabled: Indicates if the study is active.
        deleted_at: Timestamp of deletion for soft deletes.
        name: Name of the study.
        description: Description of the study.
        created_by_id: Foreign key to the user who created the study.
        owner_id: Foreign key to the owner of the study.
    """

    __tablename__ = 'studies'

    # Metadata
    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()

    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
    )

    created_by: Mapped['User'] = relationship('User', back_populates='studies_created', foreign_keys=[created_by_id])
    owner: Mapped['User'] = relationship('User', back_populates='studies_owned', foreign_keys=[owner_id])

    study_steps: Mapped[list['StudyStep']] = relationship(
        'StudyStep',
        back_populates='study',
        uselist=True,
        cascade='all, delete-orphan',
        order_by='StudyStep.order_position',
    )
    study_conditions: Mapped[list['StudyCondition']] = relationship(
        'StudyCondition', back_populates='study', uselist=True, cascade='all, delete-orphan'
    )
    api_keys: Mapped[list['ApiKey']] = relationship('ApiKey', back_populates='study', cascade='all, delete-orphan')


class StudyCondition(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'study_conditions' table.

    Attributes:
        enabled: Indicates if the condition is active.
        deleted_at: Timestamp of deletion for soft deletes.
        name: Name of the study condition.
        description: Description of the study condition.
        recommendation_count: Number of recommendations associated with the condition.
        study_id: Foreign key to the associated study.
        created_by_id: Foreign key to the user who created the condition.
    """

    __tablename__ = 'study_conditions'

    # Metadata
    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()
    recommender_key: Mapped[str] = mapped_column()
    recommendation_count: Mapped[int] = mapped_column(default=10)

    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))

    # Foreign key relationships
    study: Mapped['Study'] = relationship('Study', back_populates='study_conditions')
    study_participants: Mapped[list['StudyParticipant']] = relationship(
        'StudyParticipant', back_populates='study_condition', uselist=True, cascade='all, delete-orphan'
    )


class StudyStep(DBBaseOrderedModel, BaseModelMixin):
    """SQLAlchemy model for the 'study_steps' table.

    Attributes:
        enabled: Indicates if the study step is active.
        deleted_at: Timestamp of deletion for soft deletes.
        step_type: Type of the study step.
        name: Name of the study step.
        description: Description of the study step.
        title: Title of the study step.
        instructions: Instructions for the study step.
        path: Path associated with the study step.
        survey_api_root: API root for surveys in the study step.
        study_id: Foreign key to the associated study.
        created_by_id: Foreign key to the user who created the step.
    """

    __tablename__ = 'study_steps'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    step_type: Mapped[Optional[str]] = mapped_column(nullable=True)

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()

    title: Mapped[Optional[str]] = mapped_column()
    instructions: Mapped[Optional[str]] = mapped_column()

    path: Mapped[str] = mapped_column()
    survey_api_root: Mapped[Optional[str]] = mapped_column()

    # Foreign key
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('studies.id'), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))

    # Foreign key relationships
    study: Mapped['Study'] = relationship('Study', back_populates='study_steps')
    study_step_pages: Mapped[list['StudyStepPage']] = relationship(
        'StudyStepPage', back_populates='study_step', uselist=True, cascade='all, delete-orphan'
    )

    __table_args__ = (
        UniqueConstraint(
            'study_id',
            'order_position',
            name='study_step_study_id_order_position_key',
            deferrable=True,
            initially='deferred',
        ),
    )


class StudyStepPageContent(DBBaseOrderedModel, BaseModelMixin):
    """SQLAlchemy model for the 'page_contents' table.

    Attributes:
        enabled: Indicates if the page content is active.
        deleted_at: Timestamp of deletion for soft deletes.
        created_by_id: Foreign key to the user who created the content.
        preamble: Preamble text for the page content.
        page_id: Foreign key to the associated page.
        construct_id: Foreign key to the associated survey construct.
        scale_id: Foreign key to the associated construct scale.
    """

    __tablename__ = 'study_step_page_contents'

    # Metadata
    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))

    preamble: Mapped[Optional[str]] = mapped_column()

    study_step_page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('study_step_pages.id'), primary_key=True
    )
    survey_construct_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('survey_constructs.id'), primary_key=True
    )
    survey_scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('survey_scales.id'), primary_key=True)

    study_step_page: Mapped['StudyStepPage'] = relationship('StudyStepPage', back_populates='study_step_page_contents')
    survey_construct: Mapped['SurveyConstruct'] = relationship(
        'SurveyConstruct', back_populates='study_step_page_contents'
    )
    survey_scale: Mapped['SurveyScale'] = relationship('SurveyScale', back_populates='study_step_page_contents')

    @property
    def name(self) -> str:
        """Get the display name for the content."""
        if self.survey_construct:
            return self.survey_construct.name
        return "Unknown Content"


class StudyStepPage(DBBaseOrderedModel, BaseModelMixin):
    """SQLAlchemy model for the 'study_step_pages' table.

    Attributes:
        enabled: Indicates if the page is active.
        deleted_at: Timestamp of deletion for soft deletes.
        page_type: Type of the page.
        name: Name of the page.
        description: Description of the page.
        title: Title of the page.
        instructions: Instructions for the page.
        created_by_id: Foreign key to the user who created the page.
        study_id: Foreign key to the associated study.
        step_id: Foreign key to the associated study step.
    """

    __tablename__ = 'study_step_pages'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    page_type: Mapped[Optional[str]] = mapped_column('page_type', nullable=True)

    name: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column()

    title: Mapped[Optional[str]] = mapped_column()
    instructions: Mapped[Optional[str]] = mapped_column()

    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('studies.id'), nullable=False)
    study_step_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_steps.id'), nullable=False)

    study_step: Mapped['StudyStep'] = relationship('StudyStep', back_populates='study_step_pages')
    study_step_page_contents: Mapped[list[StudyStepPageContent]] = relationship(
        'StudyStepPageContent', back_populates='study_step_page', uselist=True, cascade='all, delete-orphan'
    )


class ApiKey(DBBaseModel):
    """SQLAlchemy model for the 'api_keys' table.

    Attributes:
        key_hash: Hashed value of the API key.
        description: Description of the API key.
        study_id: Foreign key to the associated study.
        user_id: Foreign key to the associated user.
        is_active: Indicates if the API key is active.
        created_at: Timestamp of creation.
        last_used_at: Timestamp of last usage.
    """

    __tablename__ = 'api_keys'

    key_hash: Mapped[str] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(nullable=False)

    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey('users.id'))

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    study: Mapped['Study'] = relationship('Study', back_populates='api_keys')
    user: Mapped['User'] = relationship('User', back_populates='api_keys')


class User(DBBaseModel):
    """SQLAlchemy model for the 'users' table.

    Attributes:
        auth0_sub: Unique Auth0 subject identifier.
        created_at: Timestamp of creation.
        studies_owned: List of studies owned by the user.
        studies_created: List of studies created by the user.
        api_keys: List of API keys associated with the user.
    """

    __tablename__ = 'users'

    auth0_sub: Mapped[str] = mapped_column(unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    studies_owned: Mapped[list['Study']] = relationship('Study', back_populates='owner', foreign_keys='Study.owner_id')

    studies_created: Mapped[list['Study']] = relationship(
        'Study', back_populates='created_by', foreign_keys='Study.created_by_id'
    )

    api_keys: Mapped[list['ApiKey']] = relationship('ApiKey', back_populates='user')
