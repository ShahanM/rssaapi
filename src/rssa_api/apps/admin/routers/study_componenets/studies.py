"""Router for managing study components in the admin API."""

import math
import uuid
from functools import reduce
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict

from rssa_api.auth.security import (
    get_auth0_authenticated_user,
    get_current_user,
    require_permissions,
)
from rssa_api.data.models.study_components import User
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import (
    OrderedListItem,
    PreviewSchema,
    ReorderPayloadSchema,
    SortDir,
)
from rssa_api.data.schemas.study_components import (
    ApiKeyCreate,
    ApiKeyRead,
    StudyAudit,
    StudyBase,
    StudyConditionCreate,
    StudyConditionRead,
    StudyCreate,
    StudyRead,
    StudyStepCreate,
    StudyStepRead,
)
from rssa_api.data.services import (
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


class PaginatedStudyResponse(BaseModel):
    rows: list[PreviewSchema]  # type: ignore
    page_count: int

    model_config = ConfigDict(from_attributes=True)


class StudyStepConfigObj(BaseModel):
    step_id: uuid.UUID
    path: str
    component_type: str


class StudyConfigSchema(BaseModel):
    study_id: uuid.UUID
    conditions: dict[str, uuid.UUID]
    steps: list[StudyStepConfigObj]


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
        Depends(require_permissions('read:studies', 'admin:all', 'read:own_studies')),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: Optional[str] = Query(None, description='The field to sort by.'),
    sort_dir: Optional[SortDir] = Query(None, description='The direction to sort (asc or desc)'),
    search: Optional[str] = Query(None, description='A search term to filter results by name or description'),
):
    """Get a paginated and sortable list of studies accessible to the current user.

    This returns all studies where the user is either an owner or has specific
    visibility privileges. Super Admins will see all studies in the system.

    ## Permissions
    Requires one of: `read:studies`, `admin:all`, `read:own_studies`
    """
    is_super_admin = 'admin:all' in user.permissions or 'read:studies' in user.permissions

    offset = page_index * page_size
    studies_from_db = []
    total_items = 0
    total_items = await study_service.count(search)
    if is_super_admin:
        studies_from_db = await study_service.get_paged_list(
            limit=page_size,
            offset=offset,
            schema=PreviewSchema,
            sort_by=sort_by,
            sort_dir=sort_dir.value if sort_dir else None,
            search=search,
        )
    else:
        studies_from_db = await study_service.get_paged_for_owner(
            owner_id=current_user.id,
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
        Depends(require_permissions('read:studies', 'admin:all', 'read:own_studies')),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a single instance of a study.

    Retrieves a single study with all joined table fields.

    **Visibility Rules:**
    * **Super Admins:** Can view any study.
    * **Standard Users:** Can only view studies they own.

    If the study does not exist or the user does not have permission,
    a generic `404 Not Found` is returned to prevent ID enumeration.
    """
    study = await study_service.get_detailed(study_id, StudyAudit)

    if study is None:
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

    ## Permissions
    Requires one of: `create:studies`, `admin:all`
    """,
)
async def create_study(
    new_study: StudyCreate,
    study_service: StudyServiceDep,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permissions('create:studies', 'admin:all'))],
):
    """Create a new study instance.

    ## Permissions
    Requires one of: `create:studies`, `admin:all`

    Args:
        new_study: The study data to create.
        study_service: The service to handle study operations.
        current_user: The currently authenticated user.

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
):
    study_steps = await step_service.get_items_for_owner_as_ordered_list(study_id, OrderedListItem)
    return study_steps


@router.post(
    '/{study_id}/steps',
    status_code=status.HTTP_201_CREATED,
    response_model=StudyStepRead,
    summary='Get a list of steps for a study.',
    description="""
	""",
    response_description='A list of study steps: StudyStep[] or an empty list: [].',
)
async def create_study_step(
    study_id: uuid.UUID,
    new_step: StudyStepCreate,
    step_service: StudyStepServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:steps', 'admin:all'))],
):
    step_in_db = await step_service.create_for_owner(study_id, new_step)

    return StudyStepRead.model_validate(step_in_db)


@router.get(
    '/{study_id}/conditions',
    response_model=list[StudyConditionRead],
    summary='Get a list of conditions assigned to a study.',
    description="""
	""",
    response_description="""A list of study conditions: StudyCondition[],
	or an empty list: [].""",
)
async def get_study_conditions(
    study_id: uuid.UUID,
    condition_service: StudyConditionServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
):
    study_conditions = await condition_service.get_paged_for_owner(
        study_id, page_size, page_index * page_size, StudyConditionRead
    )
    return study_conditions


@router.post(
    '/{study_id}/conditions',
    status_code=status.HTTP_201_CREATED,
    summary='Create a study condition for a study.',
    description="""
	""",
    response_description='HTTP 201 Created on success',
)
async def create_study_condition(
    study_id: uuid.UUID,
    new_condition: StudyConditionCreate,
    condition_service: StudyConditionServiceDep,
    current_user: Annotated[User, Depends(get_current_user)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'create:conditions'))],
):
    new_condition.created_by_id = current_user.id
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
):
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
):
    await study_service.delete(study_id)

    return {}


@router.patch('/{study_id}/steps/reorder', status_code=204)
async def reorder_study_steps(
    study_id: uuid.UUID,
    payload: list[ReorderPayloadSchema],
    step_service: StudyStepServiceDep,
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    steps_map = {item.id: item.order_position for item in payload}
    await step_service.reorder_items(study_id, steps_map)

    return {'message': 'Steps reordered successfully'}


@router.get(
    '/{study_id}/steps/validate',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Check if a step path is unique within a study',
    description="""
	""",
    response_description="""HTTP 204 No Content on success, or HTTP 409 CONFLICT on
	failure.""",
)
async def validate_step_path_uniqueness(
    study_id: uuid.UUID,
    path: str,
    step_service: StudyStepServiceDep,
    exclude_step_id: Optional[uuid.UUID] = None,
):
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
    user: Annotated[User, Depends(get_current_user)],
):
    api_key = await key_service.create_api_key_for_study(study_id, new_api_key.description, user.id)

    return api_key


@router.get('/{study_id}/apikeys', response_model=list[ApiKeyRead])
async def get_api_keys(
    study_id: uuid.UUID,
    service: ApiKeyServiceDep,
    current_user: Annotated[User, Depends(get_current_user)],
):
    keys = await service.get_api_keys_for_study(study_id, current_user.id)

    return keys


# @router.get('/{study_id}/export_study_config', response_model=StudyConfigSchema)
# async def export_study_config(
#     study_id: uuid.UUID,
#     step_service: StudyStepServiceDep,
#     condition_service: StudyConditionServiceDep,
#     user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
# ):
#     steps = await step_service.get_study_steps(study_id)
#     conditions = await condition_service.get(study_id)

#     config = {
#         'study_id': study_id,
#         'conditions': {con.name: con.id for con in conditions},
#         'steps': [
#             {
#                 'step_id': step.id,
#                 'path': step.path,
#                 'component_type': STEP_TYPE_TO_COMPONENT[step.step_type if step.step_type else 'extras'],
#             }
#             for step in steps
#         ],
#     }

#     return config
