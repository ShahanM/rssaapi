"""SQLAlchemy models for study components in the RSSA API."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rssa_api.data.models.rssa_base_models import BaseModelMixin, DBBaseModel, DBBaseOrderedModel
from rssa_api.data.models.survey_constructs import ConstructScale, SurveyConstruct


class Study(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'studies' table.

    Attributes:
        enabled (bool): Indicates if the study is active.
        deleted_at (Optional[datetime]): Timestamp of deletion for soft deletes.
        name (str): Name of the study.
        description (Optional[str]): Description of the study.
        created_by_id (uuid.UUID): Foreign key to the user who created the study.
        owner_id (uuid.UUID): Foreign key to the owner of the study.
    """

    __tablename__ = 'studies'

    # Metadata
    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()

    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))

    created_by: Mapped['User'] = relationship('User', back_populates='studies_created', foreign_keys=[created_by_id])
    owner: Mapped['User'] = relationship('User', back_populates='studies_owned', foreign_keys=[owner_id])

    steps: Mapped[list['StudyStep']] = relationship(
        'StudyStep',
        back_populates='study',
        uselist=True,
        cascade='all, delete-orphan',
        order_by='StudyStep.order_position',
    )
    conditions: Mapped[list['StudyCondition']] = relationship(
        'StudyCondition', back_populates='study', uselist=True, cascade='all, delete-orphan'
    )
    api_keys: Mapped[list['ApiKey']] = relationship('ApiKey', back_populates='study', cascade='all, delete-orphan')


class StudyCondition(DBBaseModel, BaseModelMixin):
    """SQLAlchemy model for the 'study_conditions' table.

    Attributes:
        enabled (bool): Indicates if the condition is active.
        deleted_at (Optional[datetime]): Timestamp of deletion for soft deletes.
        name (str): Name of the study condition.
        description (Optional[str]): Description of the study condition.
        recommendation_count (int): Number of recommendations associated with the condition.
        study_id (uuid.UUID): Foreign key to the associated study.
        created_by_id (uuid.UUID): Foreign key to the user who created the condition.
    """

    __tablename__ = 'study_conditions'

    # Metadata
    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()
    recommendation_count: Mapped[int] = mapped_column(default=10)

    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))

    # Foreign key relationships
    study: Mapped['Study'] = relationship('Study', back_populates='conditions')


class StudyStep(DBBaseOrderedModel, BaseModelMixin):
    """SQLAlchemy model for the 'study_steps' table.

    Attributes:
        enabled (bool): Indicates if the study step is active.
        deleted_at (Optional[datetime]): Timestamp of deletion for soft deletes.
        step_type (Optional[str]): Type of the study step.
        name (str): Name of the study step.
        description (Optional[str]): Description of the study step.
        title (Optional[str]): Title of the study step.
        instructions (Optional[str]): Instructions for the study step.
        path (str): Path associated with the study step.
        survey_api_root (Optional[str]): API root for surveys in the study step.
        study_id (uuid.UUID): Foreign key to the associated study.
        created_by_id (uuid.UUID): Foreign key to the user who created the step.
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
    study: Mapped['Study'] = relationship('Study', back_populates='steps')
    pages: Mapped[list['Page']] = relationship(
        'Page', back_populates='step', uselist=True, cascade='all, delete-orphan'
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


class PageContent(DBBaseOrderedModel, BaseModelMixin):
    """SQLAlchemy model for the 'page_contents' table.

    Attributes:
        enabled (bool): Indicates if the page content is active.
        deleted_at (Optional[datetime]): Timestamp of deletion for soft deletes.
        created_by_id (uuid.UUID): Foreign key to the user who created the content.
        preamble (Optional[str]): Preamble text for the page content.
        page_id (uuid.UUID): Foreign key to the associated page.
        construct_id (uuid.UUID): Foreign key to the associated survey construct.
        scale_id (uuid.UUID): Foreign key to the associated construct scale.
    """

    __tablename__ = 'page_contents'

    # Metadata
    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))

    preamble: Mapped[Optional[str]] = mapped_column()

    page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('step_pages.id'), primary_key=True)
    construct_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('survey_constructs.id'), primary_key=True
    )
    scale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('construct_scales.id'), primary_key=True)

    page: Mapped['Page'] = relationship('Page', back_populates='page_contents')
    survey_construct: Mapped['SurveyConstruct'] = relationship('SurveyConstruct', back_populates='page_contents')
    construct_scale: Mapped['ConstructScale'] = relationship('ConstructScale', back_populates='page_contents')


class Page(DBBaseOrderedModel, BaseModelMixin):
    """SQLAlchemy model for the 'step_pages' table.

    Attributes:
        enabled (bool): Indicates if the page is active.
        deleted_at (Optional[datetime]): Timestamp of deletion for soft deletes.
        page_type (Optional[str]): Type of the page.
        name (str): Name of the page.
        description (Optional[str]): Description of the page.
        title (Optional[str]): Title of the page.
        instructions (Optional[str]): Instructions for the page.
        created_by_id (uuid.UUID): Foreign key to the user who created the page.
        study_id (uuid.UUID): Foreign key to the associated study.
        step_id (uuid.UUID): Foreign key to the associated study step.
    """

    __tablename__ = 'step_pages'

    enabled: Mapped[bool] = mapped_column(default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    page_type: Mapped[Optional[str]] = mapped_column('page_type', nullable=True)

    name: Mapped[str] = mapped_column()
    description: Mapped[Optional[str]] = mapped_column()

    title: Mapped[Optional[str]] = mapped_column()
    instructions: Mapped[Optional[str]] = mapped_column()

    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))
    study_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('studies.id'), nullable=False)
    step_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('study_steps.id'), nullable=False)

    step: Mapped['StudyStep'] = relationship('StudyStep', back_populates='pages')
    page_contents: Mapped[list[PageContent]] = relationship(
        'PageContent', back_populates='page', uselist=True, cascade='all, delete-orphan'
    )


class ApiKey(DBBaseModel):
    """SQLAlchemy model for the 'api_keys' table.

    Attributes:
        key_hash (str): Hashed value of the API key.
        description (str): Description of the API key.
        study_id (uuid.UUID): Foreign key to the associated study.
        user_id (Optional[uuid.UUID]): Foreign key to the associated user.
        is_active (bool): Indicates if the API key is active.
        created_at (datetime): Timestamp of creation.
        last_used_at (Optional[datetime]): Timestamp of last usage.
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
        auth0_sub (str): Unique Auth0 subject identifier.
        created_at (datetime): Timestamp of creation.
        studies_owned (list[Study]): List of studies owned by the user.
        studies_created (list[Study]): List of studies created by the user.
        api_keys (list[ApiKey]): List of API keys associated with the user.
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
