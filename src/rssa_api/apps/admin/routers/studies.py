import math
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

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
    ApiKeyBaseSchema,
    ApiKeySchema,
    StudyBaseSchema,
    StudyConditionBaseSchema,
    StudyConditionSchema,
    StudySchema,
    StudyStepBaseSchema,
)
from rssa_api.data.services import ApiKeyService, StudyConditionService, StudyService, StudyStepService
from rssa_api.data.services.rssa_dependencies import (
    get_api_key_service,
)
from rssa_api.data.services.rssa_dependencies import (
    get_study_condition_service as condition_service,
)
from rssa_api.data.services.rssa_dependencies import get_study_service as study_service
from rssa_api.data.services.rssa_dependencies import get_study_step_service as step_service

from ..docs import ADMIN_STUDIES_TAG

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
    dependencies=[Depends(get_auth0_authenticated_user), Depends(study_service)],
)


class PaginatedStudyResponse(BaseModel):
    rows: list[PreviewSchema]  # type: ignore
    page_count: int

    class Config:
        from_attributes = True


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
    summary='Get a paginated and sortable list of studies',
    description=(
        'Retrieves a paginated list of all the studies that the current authenticated user has access to. '
        'Supports sorting by a specifc field.'
    ),
    response_description='An object containing the list of studies, and a total pages.',
)
async def get_studies(
    study_service: Annotated[StudyService, Depends(study_service)],
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
    is_super_admin = 'admin:all' in user.permissions or 'read:studies' in user.permissions

    offset = page_index * page_size
    studies_from_db = []
    total_items = 0
    user_id = current_user.id
    if is_super_admin:
        user_id = None
    total_items = await study_service.count_studies_for_user(user_id, search)
    studies_from_db = await study_service.get_studies_for_user(
        user_id=user_id,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sort_dir.value if sort_dir else None,
        search=search,
    )
    page_count = math.ceil(total_items / page_size) if total_items > 0 else 1

    return PaginatedStudyResponse(rows=studies_from_db, page_count=page_count)


@router.get(
    '/{study_id}',
    response_model=StudySchema,
    summary='Get a single instance of a study',
    description=(
        'Retrieves a single instance of a study that matches the {study_id} with all its top level fields, '
        'and joined table fields. This is only visible to authorized users with full visibility privileges '
        'or those with ownership privileges and is listed as a owner of the study.\n\n'
        'Raises a 404 NOT FOUND exception if no studies matches {study_id} that is visible to the authorized user.\n\n'
        '_Note: The not found exception is also raised when the current user does not have the necessary privileges._'
    ),
    response_description='A detailed study instance, or a HTTP 404 NOT FOUND.',
)
async def get_study_detail(
    study_id: uuid.UUID,
    study_service: Annotated[StudyService, Depends(study_service)],
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('read:studies', 'admin:all', 'read:own_studies')),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
):
    is_super_admin = 'admin:all' in user.permissions or 'read:studies' in user.permissions

    study_detail = None
    if is_super_admin:
        study_detail = await study_service.get_study_info(study_id)
    else:
        study_detail = await study_service.get_study_info_for_user(current_user.id, study_id)

    if study_detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    return study_detail


@router.get(
    '/{study_id}/summary',
    response_model=StudySchema,
    summary='Get a summary of a study instance',
    description=(
        'Retrieves a single instance of a study that matches the {study_id} with only the top level fields, and '
        'includes some computed statistics.This is only visible to authorized users with full visibility privileges '
        'or those with ownership privileges and is listed as a owner of the study.\n\n'
        'Raises a 404 NOT FOUND exception if no studies matches {study_id} that is visible to the authorized user.\n\n'
        '_Note: The not found exception is also raised when the current user does not have the necessary privileges._'
    ),
    response_description='A summary of a study isntance, or a HTTP 404 NOT FOUND.',
)
async def get_study_summary(
    study_id: uuid.UUID,
    study_service: Annotated[StudyService, Depends(study_service)],
    condition_service: Annotated[StudyConditionService, Depends(condition_service)],
    user: Annotated[
        Auth0UserSchema,
        Depends(require_permissions('read:studies', 'admin:all', 'read:own_studies')),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
):
    is_super_admin = 'admin:all' in user.permissions or 'read:studies' in user.permissions
    study_summary = None
    condition_counts = await condition_service.get_participant_count_per_coundition(study_id)
    if is_super_admin:
        study_summary = await study_service.get_study_info(study_id, condition_counts)
    else:
        study_summary = await study_service.get_study_info_for_user(current_user.id, study_id, condition_counts)

    if study_summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Study not found.')

    return study_summary


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    summary='Create a study instance.',
    description="""
	""",
    response_description='HTTP 201 CREATED, or an appropriate HTTP error',
)
async def create_study(
    new_study: StudyBaseSchema,
    study_service: Annotated[StudyService, Depends(study_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    user: Annotated[None, Depends(require_permissions('create:studies', 'admin:all'))],
):
    await study_service.create_new_study(new_study.name, new_study.description, current_user)

    return {'message': 'Study created.'}


@router.get(
    '/{study_id}/steps',
    response_model=list[OrderedListItem],
    summary='',
    description="""
	""",
    response_description='',
)
async def get_study_steps(
    study_id: uuid.UUID,
    step_service: Annotated[StudyStepService, Depends(step_service)],
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    study_steps = await step_service.get_study_steps_as_ordered_list_Items(study_id)
    return study_steps


@router.post(
    '/{study_id}/steps',
    status_code=status.HTTP_201_CREATED,
    summary='Get a list of steps for a study.',
    description="""
	""",
    response_description='A list of study steps: StudyStep[] or an empty list: [].',
)
async def create_study_step(
    study_id: uuid.UUID,
    new_step: StudyStepBaseSchema,
    step_service: Annotated[StudyStepService, Depends(step_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:steps'))],
):
    await step_service.create_study_step(study_id, new_step)

    return {'message': 'Study step created'}


@router.get(
    '/{study_id}/conditions',
    response_model=list[StudyConditionSchema],
    summary='Get a list of conditions assigned to a study.',
    description="""
	""",
    response_description="""A list of study conditions: StudyCondition[],
	or an empty list: [].""",
)
async def get_study_conditions(
    study_id: uuid.UUID,
    condition_service: Annotated[StudyConditionService, Depends(condition_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'read:conditions'))],
):
    study_conditions = await condition_service.get_study_conditions(study_id)
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
    new_condition: StudyConditionBaseSchema,
    condition_service: Annotated[StudyConditionService, Depends(condition_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'create:conditions'))],
):
    await condition_service.create_study_condition(study_id, new_condition)


@router.patch('/{study_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_study(
    study_id: uuid.UUID,
    payload: dict[str, str],
    study_service: Annotated[StudyService, Depends(study_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:studies', 'admin:all'))],
):
    await study_service.update_study(study_id, payload)

    return {}


@router.delete(
    '/{study_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='',
    description="""
	""",
    response_description='',
)
async def delete_study(
    study_id: uuid.UUID,
    study_service: Annotated[StudyService, Depends(study_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:studies'))],
):
    await study_service.delete_study(study_id)

    return {}


@router.patch('/{study_id}/steps/reorder', status_code=204)
async def reorder_study_steps(
    study_id: uuid.UUID,
    payload: list[ReorderPayloadSchema],
    step_service: Annotated[StudyStepService, Depends(step_service)],
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    steps_map = {item.id: item.order_position for item in payload}
    await step_service.reorder_study_steps(study_id, steps_map)

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
    step_service: Annotated[StudyStepService, Depends(step_service)],
    exclude_step_id: Optional[uuid.UUID] = None,
):
    validated = await step_service.validate_step_path_uniqueness(study_id, path, exclude_step_id)

    if not validated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='This path is already in use for this study.',
        )

    return {}


@router.post(
    '/{study_id}/apikeys',
    response_model=ApiKeySchema,
    status_code=status.HTTP_201_CREATED,
    summary='',
    description='',
    response_description='',
)
async def generate_study_api_key(
    study_id: uuid.UUID,
    new_api_key: ApiKeyBaseSchema,
    key_service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    user: Annotated[User, Depends(get_current_user)],
):
    api_key = await key_service.create_api_key_for_study(study_id, new_api_key.description, user.id)

    return api_key


@router.get(
    '/{study_id}/apikeys',
    response_model=list[ApiKeySchema],
    summary='',
    description='',
    response_description='',
)
async def get_api_keys(
    study_id: uuid.UUID,
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    keys = await service.get_api_keys_for_study(study_id, current_user.id)

    return keys


@router.get('/{study_id}/export_study_config', response_model=StudyConfigSchema)
async def export_study_config(
    study_id: uuid.UUID,
    step_service: Annotated[StudyStepService, Depends(step_service)],
    condition_service: Annotated[StudyConditionService, Depends(condition_service)],
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    steps = await step_service.get_study_steps(study_id)
    conditions = await condition_service.get_study_conditions(study_id)

    config = {
        'study_id': study_id,
        'conditions': {con.name: con.id for con in conditions},
        'steps': [
            {
                'step_id': step.id,
                'path': step.path,
                'component_type': STEP_TYPE_TO_COMPONENT[step.step_type if step.step_type else 'extras'],
            }
            for step in steps
        ],
    }

    return config
