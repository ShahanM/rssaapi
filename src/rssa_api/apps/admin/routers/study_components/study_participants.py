"""Router for managing study conditions in the admin API."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.security import get_auth0_authenticated_user, get_current_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.data.schemas.participant_schemas import ParticipantAuditDetailRead, ParticipantUpdate
from rssa_api.data.schemas.study_components import StudyComponentCheck
from rssa_api.data.services.dependencies import StudyServiceDep
from rssa_api.data.services.study_components import StudyParticipantServiceDep

router = APIRouter(
    prefix='/participants',
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.patch('/{participant_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_participant(
    participant_id: uuid.UUID,
    payload: ParticipantUpdate,
    service: StudyParticipantServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'update:participants'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Update a study participant."""
    participant = await service.get(participant_id, StudyComponentCheck)
    if participant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Participant data not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(participant.study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail='Current user is not authorized to edit this study.'
            )

    update_dict = payload.model_dump(exclude_unset=True)

    if not update_dict:
        return

    await service.update(participant_id, update_dict)


audit_router = APIRouter(
    prefix='/participant-audits',
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@audit_router.get('/{participant_id}', response_model=ParticipantAuditDetailRead)
async def get_participant_audit_detail(
    participant_id: uuid.UUID,
    service: StudyParticipantServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
):
    participant = await service.get(participant_id, ParticipantAuditDetailRead)
    if participant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Participant data not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(participant.study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not authorized to view this study.')

    return participant


@audit_router.patch('/{participant_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_participant_audit(
    participant_id: uuid.UUID,
    payload: ParticipantUpdate,
    service: StudyParticipantServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'update:participants'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Update a study participant."""
    participant = await service.get(participant_id, StudyComponentCheck)
    if participant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Participant data not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(participant.study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail='Current user is not authorized to edit this study.'
            )

    update_dict = payload.model_dump(exclude_unset=True)

    if not update_dict:
        return

    await service.update(participant_id, update_dict)
