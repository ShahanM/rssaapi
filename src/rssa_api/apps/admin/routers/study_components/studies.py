"""Router for managing study components in the admin API."""

import csv
import io
import math
import uuid
from functools import reduce
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from rssa_storage.shared import RepoQueryOptions
from starlette.responses import StreamingResponse

from rssa_api.auth.security import (
    get_auth0_authenticated_user,
    get_current_user,
    require_permissions,
)
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.data.schemas.base_schemas import (
    OrderedListItem,
    PaginatedResponse,
    PreviewSchema,
    ReorderPayloadSchema,
    SortDir,
)
from rssa_api.data.schemas.export_schemas import ExportStudy, ParticipantExportSchema, flatten_participant_for_csv
from rssa_api.data.schemas.participant_schemas import ParticipantAuditRead
from rssa_api.data.schemas.study_components import (
    ApiKeyBase,
    ApiKeyCreate,
    ApiKeyRead,
    StudyAudit,
    StudyAuthorizationCreate,
    StudyAuthorizationRead,
    StudyConditionBase,
    StudyConditionCreate,
    StudyConditionRead,
    StudyCreate,
    StudyRead,
    StudyStepBase,
    StudyStepCreate,
)
from rssa_api.data.services.dependencies import (
    ApiKeyServiceDep,
    StudyConditionServiceDep,
    StudyServiceDep,
    StudyStepServiceDep,
)
from rssa_api.data.services.study_components import StudyParticipantServiceDep
from rssa_api.data.utility import generate_code_from_uuid

from ...docs import ADMIN_STUDIES_TAG

logging = structlog.getLogger()

router = APIRouter(
    prefix='/studies',
    tags=[ADMIN_STUDIES_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get(
    '/',
    response_model=PaginatedResponse[PreviewSchema],
    summary='Get a list of studies.',
    description="""
    Get a paginated and sortable list of studies accessible to the current user.

    Returns all studies where the user is either an owner or has specific
    visibility privileges. Super Admins will see all studies in the system.
    """,
)
async def get_studies(
    study_service: StudyServiceDep,
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('read:studies', 'admin:all', 'read:authorized_studies')),
    ],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: str | None = Query(None, description='The field to sort by.'),
    sort_dir: SortDir | None = Query(None, description='The direction to sort (asc or desc)'),
    search: str | None = Query(None, description='A search term to filter results by name or description'),
) -> PaginatedResponse[PreviewSchema]:
    """Get a paginated and sortable list of studies accessible to the current user.

    This returns all studies where the user is either an owner or has specific
    visibility privileges. Super Admins will see all studies in the system.

    ## Permissions
    Requires one of: `read:studies`, `admin:all`, `read:authorized_studies`
    """
    is_super_admin = 'admin:all' in user.permissions

    offset = page_index * page_size
    studies_from_db = []
    total_items = 0
    options = RepoQueryOptions(search_text=search)
    if is_super_admin:
        total_items = await study_service.count(options=options)
        studies_from_db = await study_service.get_all(
            PreviewSchema,
            limit=page_size,
            offset=offset,
            sort_by=sort_by,
            sort_dir=sort_dir.value if sort_dir else None,
            search=search,
        )
    else:
        total_items = await study_service.count_authorized_for_user(current_user.id, search)
        studies_from_db = await study_service.get_paged_for_authorized_user(
            user_id=current_user.id,
            limit=page_size,
            offset=offset,
            schema=PreviewSchema,
            sort_by=sort_by,
            sort_dir=sort_dir.value if sort_dir else None,
            search=search,
        )
    page_count = math.ceil(total_items / page_size) if total_items > 0 else 1

    return PaginatedResponse[PreviewSchema](data=studies_from_db, page_count=page_count, total=total_items)


@router.get(
    '/{study_id}/',
    response_model=StudyAudit,
    responses={404: {'description': 'Study not found or user lacks permission'}},
    summary='Get a study details.',
    description="""
    Get a single instance of a study.

    Retrieves a single study with all joined table fields.

    **Visibility Rules:**
    * **Super Admins:** Can view any study.
    * **Standard Users:** Can only view studies they own.

    If the study does not exist or the user does not have permission,
    a generic `404 Not Found` is returned to prevent ID enumeration.
    """,
)
async def get_study_detail(
    study_id: uuid.UUID,
    study_service: StudyServiceDep,
    study_condition_service: StudyConditionServiceDep,
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('read:studies', 'admin:all', 'read:authorized_studies')),
    ],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> StudyAudit:
    """Get a single instance of a study.

    Retrieves a single study with all joined table fields.

    **Visibility Rules:**
    * **Super Admins:** Can view any study.
    * **Standard Users:** Can only view studies they own.

    If the study does not exist or the user does not have permission,
    a generic `404 Not Found` is returned to prevent ID enumeration.

    """
    study = await study_service.get(study_id, StudyAudit)

    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='viewer')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    grouped_count = await study_condition_service.get_participant_count_by_condition(study_id)
    total = reduce(lambda acc, row: acc + row.participant_count, grouped_count, 0)
    study_detail = StudyAudit(**study.model_dump())
    study_detail.total_participants = total
    study_detail.participants_by_condition = grouped_count

    return study_detail


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=StudyRead,
    summary='Create a new study.',
    description="""Create a new study instance.""",
)
async def create_study(
    new_study: StudyCreate,
    study_service: StudyServiceDep,
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permissions('create:studies', 'admin:all'))],
) -> StudyRead:
    """Create a new study instance.

    ## Permissions
    Requires one of: `create:studies`, `admin:all`
    """
    created_study = await study_service.create(new_study, owner_id=current_user.id)

    return StudyRead.model_validate(created_study)


@router.get(
    '/{study_id}/steps/',
    status_code=status.HTTP_200_OK,
    response_model=list[OrderedListItem],
    summary='Get a list of steps.',
    description="""Retrieve the list of steps belonging to a study.""",
)
async def get_study_steps(
    study_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    _: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
) -> list[OrderedListItem]:
    """Get a list of steps for a study.

    Returns all steps associated with the given study ID, ordered by their position.
    """
    study_steps = await step_service.get_all(OrderedListItem, owner_id=study_id)
    return study_steps


@router.post(
    '/{study_id}/steps/',
    status_code=status.HTTP_201_CREATED,
    response_model=OrderedListItem,
    summary='Create a new study step.',
    description="""Create a new step within a study.""",
    response_description='The created study step instance.',
)
async def create_study_step(
    study_id: uuid.UUID,
    new_step_payload: StudyStepBase,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:steps', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> OrderedListItem:
    """Create a new study step."""
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    new_step = StudyStepCreate(**new_step_payload.model_dump(exclude_computed_fields=True), study_id=study_id)
    step_in_db = await step_service.create(new_step, owner_id=study_id)

    return OrderedListItem.model_validate(step_in_db)


@router.get(
    '/{study_id}/conditions/',
    response_model=list[StudyConditionRead],
    summary='Get a list of conditions assigned to a study.',
    description="""Get a paginated list of conditions associated with a study.""",
    response_description="""A list of study conditions.""",
)
async def get_study_conditions(
    study_id: uuid.UUID,
    condition_service: StudyConditionServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
) -> list[StudyConditionRead]:
    """Get a list of conditions assigned to a study."""
    study_conditions = await condition_service.get_all(
        StudyConditionRead,
        owner_id=study_id,
        limit=page_size,
        offset=page_index * page_size,
    )
    return study_conditions


@router.post(
    '/{study_id}/conditions/',
    status_code=status.HTTP_201_CREATED,
    summary='Create a study condition for a study.',
    description="""Create a new condition for the specified study.""",
    response_description='The created study condition.',
)
async def create_study_condition(
    study_id: uuid.UUID,
    new_condition_payload: StudyConditionBase,
    condition_service: StudyConditionServiceDep,
    study_service: StudyServiceDep,
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'create:conditions'))],
) -> StudyConditionRead:
    """Create a study condition for a study."""
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    new_condition = StudyConditionCreate(**new_condition_payload.model_dump(), study_id=study_id)
    condition = await condition_service.create(new_condition, owner_id=study_id)

    return StudyConditionRead.model_validate(condition)


@router.patch(
    '/{study_id}/',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Update a study.',
    description="""Updates an existing study with the provided fields.""",
)
async def update_study(
    study_id: uuid.UUID,
    payload: dict[str, str],
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:studies', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Update a study."""
    is_super_admin = 'admin:all' in user.permissions or 'update:studies' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    await study_service.update(study_id, payload)


@router.delete(
    '/{study_id}/',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete a study.',
    description="""Deletes a study by its ID.""",
)
async def delete_study(
    study_id: uuid.UUID,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:studies', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Delete a study."""
    is_super_admin = 'admin:all' in user.permissions or 'delete:studies' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    await study_service.delete(study_id)


@router.patch('/{study_id}/steps/reorder/', status_code=204)
async def reorder_study_steps(
    study_id: uuid.UUID,
    payload: list[ReorderPayloadSchema],
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Reorder study steps."""
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    steps_map = {item.id: item.order_position for item in payload}
    await step_service.reorder_items(study_id, steps_map)


@router.get(
    '/{study_id}/steps/validate/',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Check if a step path is unique within a study',
    description="""Verifies that a proposed path for a study step is unique within the study.""",
    response_description="""HTTP 204 No Content on success.""",
)
async def validate_step_path_uniqueness(
    study_id: uuid.UUID,
    path: str,
    step_service: StudyStepServiceDep,
    exclude_step_id: uuid.UUID | None = None,
) -> None:
    """Check if a step path is unique within a study."""
    validated = await step_service.validate_step_path_uniqueness(study_id, path, exclude_step_id)

    if not validated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='This path is already in use for this study.',
        )


@router.post(
    '/{study_id}/apikeys/',
    status_code=status.HTTP_201_CREATED,
    response_model=ApiKeyRead,
    summary='Generate a new API key for the study.',
    description="""Creates a new API key and key secret to be used a study application.""",
)
async def generate_study_api_key(
    study_id: uuid.UUID,
    new_api_key_payload: ApiKeyBase,
    key_service: ApiKeyServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> ApiKeyRead:
    """Generate a new API key for a study."""
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')
    new_api_key = ApiKeyCreate(**new_api_key_payload.model_dump(), study_id=study_id, user_id=current_user.id)
    api_key = await key_service.generate_new_api_key(new_api_key)

    return api_key


@router.get(
    '/{study_id}/apikeys/',
    status_code=status.HTTP_200_OK,
    response_model=list[ApiKeyRead],
    summary='Get a list of API keys.',
    description="""Retrieive a list of active API keys for the authenticated user.""",
)
async def get_api_keys(
    study_id: uuid.UUID,
    service: ApiKeyServiceDep,
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> list[ApiKeyRead]:
    """Get all API keys for a study."""
    keys = await service.get_api_keys_for_study(study_id, current_user.id)

    return keys


@router.get(
    '/{study_id}/authorizations/',
    response_model=list[StudyAuthorizationRead],
    summary='Get list of authorized users for a study.',
    description="""Get a list of users who are authorized to access this study.""",
)
async def get_study_authorizations(
    study_id: uuid.UUID,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> list[StudyAuthorizationRead]:
    """Get list of authorized users for a study."""
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    study_auths = await study_service.get_study_authorizations(study_id)
    return [StudyAuthorizationRead.model_validate(study_auth) for study_auth in study_auths]


@router.post(
    '/{study_id}/authorizations/',
    status_code=status.HTTP_201_CREATED,
    response_model=StudyAuthorizationRead,
    summary='Add an authorized user to a study.',
    description="""Authorize a user to access a study.""",
)
async def add_study_authorization(
    study_id: uuid.UUID,
    payload: StudyAuthorizationCreate,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> StudyAuthorizationRead:
    """Add an authorized user to a study."""
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    study_auth = await study_service.add_study_authorization(study_id, payload.user_id, payload.role)
    return StudyAuthorizationRead.model_validate(study_auth)


@router.delete(
    '/{study_id}/authorizations/{user_id}/',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Remove an authorized user from a study.',
    description="""Revoke access for a user to a study.""",
)
async def remove_study_authorization(
    study_id: uuid.UUID,
    user_id: uuid.UUID,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> None:
    """Remove an authorized user from a study."""
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    await study_service.remove_study_authorization(study_id, user_id)


@router.get('/{study_id}/participants/', response_model=PaginatedResponse[ParticipantAuditRead])
async def get_study_participants(
    study_id: uuid.UUID,
    # start_datetime: datetime,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
    participant_service: StudyParticipantServiceDep,
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: str | None = Query(None, description='The field to sort by.'),
    sort_dir: SortDir | None = Query(None, description='The direction to sort (asc or desc)'),
    search: str | None = Query(None, description='A search term to filter results by name or description'),
    is_verified: bool | None = None,
    # status: str = Query(default='completed'),
):
    # status = 'completed'
    # status = 'active'
    status = ['completed', 'active']
    options = RepoQueryOptions(
        filters={'current_status': status, 'discarded': False},
    )
    offset = page_index * page_size
    if is_verified is not None:
        options.filters['is_verified'] = is_verified

    if not sort_by:
        sort_by = 'created_at'
    sorting = sort_dir.value if sort_dir else None
    options.search_text = search
    if sorting is None:
        sorting = 'desc'
    participants = await participant_service.get_all(
        ParticipantAuditRead,
        owner_id=study_id,
        options=options,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sorting,
        search=search,
    )
    total = await participant_service.count(owner_id=study_id, options=options)
    page_count = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse[ParticipantAuditRead](data=participants, page_count=page_count, total=total)


@router.get('/{study_id}/demographics/summary/')
async def get_demographic_summary(
    study_id: uuid.UUID,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all'))],
    participant_service: StudyParticipantServiceDep,
):
    summary = await participant_service.get_study_demographic_summary(study_id)
    return summary


@router.get('/{study_id}/export/')
async def export_study_data(
    study_id: uuid.UUID,
    participant_service: StudyParticipantServiceDep,
    study_service: StudyServiceDep,
):
    study = await study_service.get(study_id, ExportStudy)
    options = RepoQueryOptions(filters={'current_status': 'completed', 'discarded': False, 'is_verified': True})
    participants: list[ParticipantExportSchema] = await participant_service.get_all(
        schema=ParticipantExportSchema,
        owner_id=study_id,
        options=options,
    )

    if not participants:
        raise HTTPException(status_code=404, detail='No data found for this study.')

    header_mapping: dict[str, str] = {}
    flat_data = [flatten_participant_for_csv(p, header_mapping) for p in participants]
    base_headers = ['Participant_ID', 'Status', 'Condition']
    final_fieldnames = base_headers + list(header_mapping.values())

    label_row = {
        'Participant_ID': 'De-identified Hash',
        'Status': 'Participant Status',
        'Condition': 'Assigned Study Condition',
    }
    for full_text, short_code in header_mapping.items():
        label_row[short_code] = full_text

    def iter_csv():
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=final_fieldnames)

        writer.writeheader()
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        writer.writerow(label_row)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for row in flat_data:
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    study_name = generate_code_from_uuid(study_id, 4)
    if study:
        study_name = study.name.replace(' ', '_')
    return StreamingResponse(
        iter_csv(),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename=study_{study_name}_export.csv'},
    )
