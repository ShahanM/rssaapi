"""Router for managing study components in the admin API."""

import math
import uuid
from functools import reduce
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from rssa_api.auth.security import (
    get_auth0_authenticated_user,
    get_current_user,
    require_permissions,
)
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.auth_schemas import UserSchema
from rssa_api.data.schemas.base_schemas import (
    OrderedListItem,
    PreviewSchema,
    ReorderPayloadSchema,
    SortDir,
)
from rssa_api.data.schemas.study_components import (
    ApiKeyCreate,
    ApiKeyRead,
    PaginatedStudyResponse,
    StudyAudit,
    StudyAuthorizationCreate,
    StudyAuthorizationRead,
    StudyConditionCreate,
    StudyConditionRead,
    StudyCreate,
    StudyRead,
    StudyStepCreate,
    StudyStepRead,
)
from rssa_api.data.services.dependencies import (
    ApiKeyServiceDep,
    StudyConditionServiceDep,
    StudyParticipantServiceDep,
    StudyServiceDep,
    StudyStepServiceDep,
)

from ...docs import ADMIN_STUDIES_TAG

STEP_TYPE_TO_COMPONENT = {
    'survey': 'SurveyStep',
    'task': 'TaskStep',
    'preference-elicitation': 'PreferenceElicitationStep',
    'consent': 'ConsentStep',
    'instruction': 'InstructionStep',
    'demographics': 'DemographicsStep',
    'extras': 'ExtraStep',
    'end': 'CompletionStep',
}

router = APIRouter(
    prefix='/studies',
    tags=[ADMIN_STUDIES_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


@router.get(
    '/',
    response_model=PaginatedStudyResponse,
    summary='Get a list of studies.',
    description="""
    Get a paginated and sortable list of studies accessible to the current user.

    This returns all studies where the user is either an owner or has specific
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
) -> PaginatedStudyResponse:
    """Get a paginated and sortable list of studies accessible to the current user.

    This returns all studies where the user is either an owner or has specific
    visibility privileges. Super Admins will see all studies in the system.

    ## Permissions
    Requires one of: `read:studies`, `admin:all`, `read:authorized_studies`

    Args:
        study_service: The study service.
        user: The authenticated user.
        current_user: The current user details.
        page_index: The page number to retrieve (0-indexed).
        page_size: The number of items per page.
        sort_by: The field to sort by.
        sort_dir: The direction to sort (asc or desc).
        search: A search term used to filter results.

    Returns:
        A paginated list of studies.
    """
    is_super_admin = 'admin:all' in user.permissions

    offset = page_index * page_size
    studies_from_db = []
    total_items = 0
    if is_super_admin:
        total_items = await study_service.count(search)
        studies_from_db = await study_service.get_paged_list(
            limit=page_size,
            offset=offset,
            schema=PreviewSchema,
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

    return PaginatedStudyResponse(rows=studies_from_db, page_count=page_count)


@router.get(
    '/{study_id}',
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
    study_participant_service: StudyParticipantServiceDep,
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

    Args:
        study_id: The UUID of the study.
        study_service: The study service.
        study_participant_service: The participant service.
        study_condition_service: The condition service.
        user: The authenticated user.
        current_user: The current user details.

    Returns:
        The study details.
    """
    study = await study_service.get_detailed(study_id, StudyAudit)

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
    description="""
    Create a new study instance.
    """,
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

    Args:
        new_study: The study data to create.
        study_service: The service to handle study operations.
        current_user: The currently authenticated user.
        _: Auth check.

    Returns:
        The created study instance.
    """
    created_study = await study_service.create_for_owner(current_user.id, new_study)

    return StudyRead.model_validate(created_study)


@router.get('/{study_id}/steps', response_model=list[OrderedListItem])
async def get_study_steps(
    study_id: uuid.UUID,
    step_service: StudyStepServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
) -> list[OrderedListItem]:
    """Get a list of steps for a study.

    Returns all steps associated with the given study ID, ordered by their position.

    Args:
        study_id: The UUID of the study.
        step_service: The service to handle study step operations.
        user: The currently authenticated user.

    Returns:
        A list of ordered study steps.
    """
    study_steps = await step_service.get_items_for_owner_as_ordered_list(study_id, OrderedListItem)
    return study_steps


@router.post(
    '/{study_id}/steps',
    status_code=status.HTTP_201_CREATED,
    response_model=StudyStepRead,
    summary='Create a new study step.',
    description="""
    Create a new step within a study.
    """,
    response_description='The created study step instance.',
)
async def create_study_step(
    study_id: uuid.UUID,
    new_step: StudyStepCreate,
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:steps', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> StudyStepRead:
    """Create a new study step.

    Args:
        study_id: The UUID of the study to add the step to.
        new_step: The step data to create.
        step_service: The service to handle study step operations.
        study_service: The study service.
        user: The currently authenticated user.
        current_user: The current user details.

    Returns:
        The created study step.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    step_in_db = await step_service.create_for_owner(study_id, new_step)

    return StudyStepRead.model_validate(step_in_db)


@router.get(
    '/{study_id}/conditions',
    response_model=list[StudyConditionRead],
    summary='Get a list of conditions assigned to a study.',
    description="""
    Get a paginated list of conditions associated with a study.
    """,
    response_description="""A list of study conditions.""",
)
async def get_study_conditions(
    study_id: uuid.UUID,
    condition_service: StudyConditionServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
) -> list[StudyConditionRead]:
    """Get a list of conditions assigned to a study.

    Args:
        study_id: The UUID of the study.
        condition_service: The service to handle condition operations.
        user: The currently authenticated user.
        page_index: The page number to retrieve (0-indexed).
        page_size: The number of items per page.

    Returns:
        A list of study conditions.
    """
    study_conditions = await condition_service.get_paged_for_owner(
        study_id, page_size, page_index * page_size, StudyConditionRead
    )
    return study_conditions


@router.post(
    '/{study_id}/conditions',
    status_code=status.HTTP_201_CREATED,
    summary='Create a study condition for a study.',
    description="""
    Create a new condition for the specified study.
    """,
    response_description='The created study condition.',
)
async def create_study_condition(
    study_id: uuid.UUID,
    new_condition: StudyConditionCreate,
    condition_service: StudyConditionServiceDep,
    study_service: StudyServiceDep,
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'create:conditions'))],
) -> StudyConditionRead:
    """Create a study condition for a study.

    Args:
        study_id: The UUID of the study.
        new_condition: The condition data to create.
        condition_service: The service to handle condition operations.
        study_service: The study service.
        current_user: The currently authenticated user.
        user: The user with permissions.

    Returns:
        The created study condition.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    condition = await condition_service.create_for_owner(study_id, new_condition)

    return condition


@router.patch(
    '/{study_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Update a study.',
    description="""
    Updates an existing study with the provided fields.
    """,
)
async def update_study(
    study_id: uuid.UUID,
    payload: dict[str, str],
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:studies', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> dict[str, str]:
    """Update a study.

    Args:
        study_id: The UUID of the study to update.
        payload: A dictionary of fields to update.
        study_service: The service to handle study operations.
        user: The currently authenticated user.
        current_user: The current user details.

    Returns:
        An empty dictionary on success.
    """
    is_super_admin = 'admin:all' in user.permissions or 'update:studies' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    await study_service.update(study_id, payload)

    return {}


@router.delete(
    '/{study_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete a study.',
    description="""
    Deletes a study by its ID.
    """,
)
async def delete_study(
    study_id: uuid.UUID,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:studies', 'admin:all'))],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> dict[str, str]:
    """Delete a study.

    Args:
        study_id: The UUID of the study to delete.
        study_service: The service to handle study operations.
        user: The currently authenticated user.
        current_user: The current user details.

    Returns:
        An empty dictionary on success.
    """
    # Check authorization if not super admin
    is_super_admin = 'admin:all' in user.permissions or 'delete:studies' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    await study_service.delete(study_id)

    return {}


@router.patch('/{study_id}/steps/reorder', status_code=204)
async def reorder_study_steps(
    study_id: uuid.UUID,
    payload: list[ReorderPayloadSchema],
    step_service: StudyStepServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> dict[str, str]:
    """Reorder study steps.

    Updates the order position of multiple steps within a study.

    Args:
        study_id: The UUID of the study.
        payload: A list of objects containing step ID and new order position.
        step_service: The service to handle study step operations.
        study_service: The study service.
        user: The currently authenticated user.
        current_user: The current user details.

    Returns:
        A success message.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='editor')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    steps_map = {item.id: item.order_position for item in payload}
    await step_service.reorder_items(study_id, steps_map)

    return {'message': 'Steps reordered successfully'}


@router.get(
    '/{study_id}/steps/validate',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Check if a step path is unique within a study',
    description="""
    Verifies that a proposed path for a study step is unique within the study.
    """,
    response_description="""HTTP 204 No Content on success.""",
)
async def validate_step_path_uniqueness(
    study_id: uuid.UUID,
    path: str,
    step_service: StudyStepServiceDep,
    exclude_step_id: uuid.UUID | None = None,
) -> dict[str, str]:
    """Check if a step path is unique within a study.

    Args:
        study_id: The UUID of the study.
        path: The path string to validate.
        step_service: The service to handle study step operations.
        exclude_step_id: Optional UUID of a step to exclude from the check (useful for updates).

    Raises:
        HTTPException: If the path is already in use (409 Conflict).

    Returns:
        An empty dictionary if valid.
    """
    validated = await step_service.validate_step_path_uniqueness(study_id, path, exclude_step_id)

    if not validated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='This path is already in use for this study.',
        )

    return {}


@router.post('/{study_id}/apikeys', response_model=ApiKeyRead, status_code=status.HTTP_201_CREATED)
async def generate_study_api_key(
    study_id: uuid.UUID,
    new_api_key: ApiKeyCreate,
    key_service: ApiKeyServiceDep,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> ApiKeyRead:
    """Generate a new API key for a study.

    Args:
        study_id: The UUID of the study.
        new_api_key: The API key data (description).
        key_service: The service to handle API key operations.
        study_service: The study service.
        user: The currently authenticated user.
        current_user: The current user details.

    Returns:
        The newly created API key details.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    api_key = await key_service.create_api_key_for_study(study_id, new_api_key.description, current_user.id)

    return api_key


@router.get('/{study_id}/apikeys', response_model=list[ApiKeyRead])
async def get_api_keys(
    study_id: uuid.UUID,
    service: ApiKeyServiceDep,
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> list[ApiKeyRead]:
    """Get all API keys for a study.

    Args:
        study_id: The UUID of the study.
        service: The service to handle API key operations.
        current_user: The currently authenticated user.

    Returns:
        A list of API keys associated with the study.
    """
    keys = await service.get_api_keys_for_study(study_id, current_user.id)

    return keys


@router.get(
    '/{study_id}/authorizations',
    response_model=list[StudyAuthorizationRead],
    summary='Get list of authorized users for a study.',
    description="""
    Get a list of users who are authorized to access this study.
    """,
)
async def get_study_authorizations(
    study_id: uuid.UUID,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> list[StudyAuthorizationRead]:
    """Get list of authorized users for a study.

    Args:
        study_id: The UUID of the study.
        study_service: The study service.
        user: The authenticated user.
        current_user: The current user details.

    Returns:
        List of authorized users.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    return await study_service.get_study_authorizations(study_id)


@router.post(
    '/{study_id}/authorizations',
    status_code=status.HTTP_201_CREATED,
    response_model=StudyAuthorizationRead,
    summary='Add an authorized user to a study.',
    description="""
    Authorize a user to access a study.
    """,
)
async def add_study_authorization(
    study_id: uuid.UUID,
    payload: StudyAuthorizationCreate,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> StudyAuthorizationRead:
    """Add an authorized user to a study.

    Args:
        study_id: The UUID of the study.
        payload: Authorization details.
        study_service: The study service.
        user: The authenticated user.
        current_user: The current user details.

    Returns:
        The created authorization.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    return await study_service.add_study_authorization(study_id, payload.user_id, payload.role)


@router.delete(
    '/{study_id}/authorizations/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Remove an authorized user from a study.',
    description="""
    Revoke access for a user to a study.
    """,
)
async def remove_study_authorization(
    study_id: uuid.UUID,
    user_id: uuid.UUID,
    study_service: StudyServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> dict[str, str]:
    """Remove an authorized user from a study.

    Args:
        study_id: The UUID of the study.
        user_id: The UUID of the user to remove.
        study_service: The study service.
        user: The authenticated user.
        current_user: The current user details.

    Returns:
        Empty dictionary on success.
    """
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        has_access = await study_service.check_study_access(study_id, current_user.id, min_role='admin')
        if not has_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    await study_service.remove_study_authorization(study_id, user_id)
    return {}
