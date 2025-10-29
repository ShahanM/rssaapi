import math
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import OrderedTextListItem, PreviewSchema, ReorderPayloadSchema, SortDir
from rssa_api.data.schemas.survey_constructs import (
    ConstructBaseSchema,
    ConstructItemBaseSchema,
    SurveyConstructSchema,
)
from rssa_api.data.services.survey_dependencies import ConstructItemService, SurveyConstructService
from rssa_api.data.services.survey_dependencies import (
    get_construct_item_service as item_service,
)
from rssa_api.data.services.survey_dependencies import (
    get_survey_construct_service as construct_service,
)

from ..docs import ADMIN_SURVEY_CONSTRUCTS_TAG

router = APIRouter(
    prefix='/constructs',
    tags=[ADMIN_SURVEY_CONSTRUCTS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user), Depends(construct_service)],
)


class PaginatedConstructResponse(BaseModel):
    rows: list[PreviewSchema]
    page_count: int

    class Config:
        from_attribute = True


@router.get(
    '/',
    response_model=PaginatedConstructResponse,
    summary='Get a paginated and sortable list of constructs',
    description="""
    Retrieves a paginated list of all the constructs.
    Supports sorting by a specifc field.

    - This endpoint is used to facilitate in the administration and organization of survey constructs.
    - Responds with an empty list if the current authenticated user does not have the correct authorization.
    """,
    response_description='A paginated list of constructs with total page count',
)
async def get_survey_constructs(
    service: Annotated[SurveyConstructService, Depends(construct_service)],
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:constructs', 'admin:all'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: Optional[str] = Query(None, description='The field to sort by.'),
    sort_dir: Optional[SortDir] = Query(None, description='The direction to sort (asc or desc)'),
    search: Optional[str] = Query(None, description='A search term to filter results by name or dscription'),
):
    offset = page_index * page_size
    total_items = await service.count_constructs(search=search)
    constructs_from_db = await service.get_survey_constructs(
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sort_dir.value if sort_dir else None,
        search=search,
    )
    page_count = math.ceil(total_items / float(page_size)) if total_items > 0 else 1
    print(page_count, total_items)

    return PaginatedConstructResponse(rows=constructs_from_db, page_count=page_count)


@router.get(
    '/{construct_id}',
    response_model=SurveyConstructSchema,
    summary='Get a single instance of a survey construct',
    description="""
    Retrieves a single isntance of a survey construct that matches the {construct_id} with all its top level fields,
    and joined table fields.

    Raises a 404 NOT FOUND exception if no construct matches the {construct_id}.
    """,
    response_description='A detailed survey construct instance, or a HTTP 404 NOT FOUND.',
)
async def get_construct_detail(
    construct_id: uuid.UUID,
    service: Annotated[SurveyConstructService, Depends(construct_service)],
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:constructs', 'admin:all'))],
):
    construct = await service.get_construct_details(construct_id)

    if not construct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Survey construct with ID {construct_id} not found.'
        )

    logger.info(f'Retrieved construct details for ID {construct_id}: {construct}')

    return construct


@router.get(
    '/{construct_id}/summary',
    response_model=SurveyConstructSchema,
    summary='Get a construct instance with its top level fields.',
    description="""
    """,
    response_description='',
)
async def get_construct_summary(
    construct_id: uuid.UUID,
    service: Annotated[SurveyConstructService, Depends(construct_service)],
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:constructs', 'admin:all'))],
):
    construct_summary = await service.get_construct_summary(construct_id)

    if not construct_summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Survey construct not found.')

    logger.info(f'Retrieved construct summary for ID {construct_id}: {construct_summary}')

    return construct_summary


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    summary='Create a survey construct instance.',
    description="""
    """,
    response_description='HTTP 201 CREATED, or an appropriate HTTP',
)
async def create_survey_construct(
    new_construct: ConstructBaseSchema,
    service: Annotated[SurveyConstructService, Depends(construct_service)],
    _: Annotated[Auth0UserSchema, Depends(require_permissions('create:constructs', 'admin:all'))],
):
    await service.create_survey_construct(new_construct)

    return {'message': 'Survey construct created.'}


@router.delete('/{construct_id}', status_code=204)
async def delete_construct(
    construct_id: uuid.UUID,
    service: Annotated[SurveyConstructService, Depends(construct_service)],
    user: Annotated[Auth0UserSchema, Depends(get_auth0_authenticated_user)],
):
    is_super_admin = 'admin:all' in user.permissions
    if not is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='You do not have permissions to perform that action.'
        )
    await service.delete_survey_construct(construct_id)

    return {'message': 'Survey construct deleted.'}


@router.get('/{construct_id}/items', response_model=list[OrderedTextListItem])
async def get_construct_items(
    construct_id: uuid.UUID,
    item_service: Annotated[ConstructItemService, Depends(item_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:items', 'admin:all'))],
):
    items = await item_service.get_item_by_construct_id(construct_id)

    return items


@router.post('/{construct_id}/items', status_code=status.HTTP_201_CREATED)
async def create_construct_item(
    construct_id: uuid.UUID,
    new_item: ConstructItemBaseSchema,
    item_service: Annotated[ConstructItemService, Depends(item_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:items', 'admin:all'))],
):
    await item_service.create_construct_item(construct_id, new_item)

    return {'message': 'Construct item created.'}


@router.patch('/{construct_id}/items/reorder', status_code=204)
async def update_scale_levels_order(
    construct_id: uuid.UUID,
    service: Annotated[SurveyConstructService, Depends(construct_service)],
    payload: list[ReorderPayloadSchema],
):
    levels_map = {item.id: item.order_position for item in payload}
    await service.reorder_items(construct_id, levels_map)
