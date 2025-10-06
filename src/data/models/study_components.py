import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.models.rssa_base_models import DBBaseModel, DBBaseOrderedModel
from data.models.survey_constructs import ConstructScale, SurveyConstruct


class Study(DBBaseModel):
    __tablename__ = 'studies'

    # Metadata
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

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


class StudyCondition(DBBaseModel):
    __tablename__ = 'study_conditions'

    # Metadata
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column()
    recommendation_count: Mapped[int] = mapped_column(default=10)

    study_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('studies.id'), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))

    # Foreign key relationships
    study: Mapped['Study'] = relationship('Study', back_populates='conditions')


class StudyStep(DBBaseOrderedModel):
    __tablename__ = 'study_steps'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

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


class PageContent(DBBaseOrderedModel):
    __tablename__ = 'page_contents'

    # Metadata
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
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


class Page(DBBaseOrderedModel):
    __tablename__ = 'step_pages'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

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
    __tablename__ = 'api_keys'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth0_sub: Mapped[str] = mapped_column(unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    studies_owned: Mapped[list['Study']] = relationship('Study', back_populates='owner', foreign_keys='Study.owner_id')

    studies_created: Mapped[list['Study']] = relationship(
        'Study', back_populates='created_by', foreign_keys='Study.created_by_id'
    )

    api_keys: Mapped[list['ApiKey']] = relationship('ApiKey', back_populates='user')
