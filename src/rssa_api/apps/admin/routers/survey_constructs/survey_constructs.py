"""Router for managing survey constructs in the admin API."""

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import OrderedTextListItem, PreviewSchema, ReorderPayloadSchema, SortDir
from rssa_api.data.schemas.survey_components import (
    PaginatedConstructResponse,
    SurveyConstructCreate,
    SurveyConstructRead,
    SurveyItemCreate,
)
from rssa_api.data.services.dependencies import SurveyConstructServiceDep, SurveyItemServiceDep

from ...docs import ADMIN_SURVEY_CONSTRUCTS_TAG

router = APIRouter(
    prefix='/constructs',
    tags=[ADMIN_SURVEY_CONSTRUCTS_TAG],
    dependencies=[Depends(get_auth0_authenticated_user)],
)


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
    service: SurveyConstructServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:constructs', 'admin:all'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: str | None = Query(None, description='The field to sort by.'),
    sort_dir: SortDir | None = Query(None, description='The direction to sort (asc or desc)'),
    search: str | None = Query(None, description='A search term to filter results by name or dscription'),
) -> PaginatedConstructResponse:
    """Get a paginated list of survey constructs.

    Args:
        service: The survey construct service.
        _: Auth check.
        page_index: The page number (0-indexed).
        page_size: Items per page.
        sort_by: Field to sort by.
        sort_dir: Sort direction.
        search: Search term.

    Returns:
        Paginated list of constructs.
    """
    offset = page_index * page_size
    total_items = await service.count(search=search)
    constructs_from_db = await service.get_paged_list(
        limit=page_size,
        offset=offset,
        schema=PreviewSchema,
        sort_by=sort_by,
        sort_dir=sort_dir.value if sort_dir else None,
        search=search,
    )
    page_count = math.ceil(total_items / float(page_size)) if total_items > 0 else 1

    return PaginatedConstructResponse(rows=constructs_from_db, page_count=page_count)


@router.get(
    '/{construct_id}',
    response_model=SurveyConstructRead,
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
    service: SurveyConstructServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:constructs', 'admin:all'))],
) -> SurveyConstructRead:
    """Get details of a survey construct.

    Args:
        construct_id: The UUID of the construct.
        service: The survey construct service.
        _: Auth check.

    Raises:
        HTTPException: If construct is not found.

    Returns:
        The construct details.
    """
    construct = await service.get_detailed(construct_id)

    if not construct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Survey construct with ID {construct_id} not found.'
        )

    # logger.info(f'Retrieved construct details for ID {construct_id}: {construct}')

    return construct


@router.get(
    '/{construct_id}/summary',
    response_model=SurveyConstructRead,
    summary='Get a construct instance with its top level fields.',
    description="""
    """,
    response_description='',
)
async def get_construct_summary(
    construct_id: uuid.UUID,
    service: SurveyConstructServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:constructs', 'admin:all'))],
) -> SurveyConstructRead:
    """Get a summary of a survey construct.

    Args:
        construct_id: The UUID of the construct.
        service: The survey construct service.
        _: Auth check.

    Raises:
        HTTPException: If construct is not found.

    Returns:
        The construct summary.
    """
    construct_summary = await service.get_detailed(construct_id)

    if not construct_summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Survey construct not found.')

    # logger.info(f'Retrieved construct summary for ID {construct_id}: {construct_summary}')

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
    new_construct: SurveyConstructCreate,
    service: SurveyConstructServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('create:constructs', 'admin:all'))],
) -> dict[str, str]:
    """Create a new survey construct.

    Args:
        new_construct: Data for the new construct.
        service: The survey construct service.
        _: Auth check.

    Returns:
        A success message.
    """
    await service.create(new_construct)

    return {'message': 'Survey construct created.'}


@router.patch(
    '/{construct_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Update a survey construct instance.',
    description="""
    Updates an existing survey construct with the provided fields.
    """,
    response_description='HTTP 204 NO CONTENT on success.',
)
async def update_survey_construct(
    construct_id: uuid.UUID,
    payload: dict[str, str],
    service: SurveyConstructServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('update:constructs', 'admin:all'))],
) -> None:
    """Update a survey construct.

    Args:
        construct_id: The UUID of the construct.
        payload: Fields to update.
        service: The survey construct service.
        _: Auth check.

    Returns:
        Empty dictionary on success.
    """
    await service.update(construct_id, payload)


@router.delete(
    '/{construct_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete a survey construct instance.',
    description="""
    Deletes a survey construct by its ID.
    """,
    response_description='HTTP 204 NO CONTENT on success.',
)
async def delete_construct(
    construct_id: uuid.UUID,
    service: SurveyConstructServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('delete:constructs', 'admin:all'))],
) -> None:
    """Delete a survey construct.

    Args:
        construct_id: The UUID of the construct.
        service: The survey construct service.
        _: Auth check.

    Returns:
        Empty dictionary on success.
    """
    await service.delete(construct_id)


@router.get('/{construct_id}/items', response_model=list[OrderedTextListItem])
async def get_construct_items(
    construct_id: uuid.UUID,
    item_service: SurveyItemServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('read:constructs', 'admin:all'))],
) -> list[OrderedTextListItem]:
    """Get items for a survey construct.

    Args:
        construct_id: The UUID of the construct.
        item_service: The survey item service.
        user: Auth check.

    Returns:
        A list of ordered items.
    """
    items = await item_service.get_items_for_owner_as_ordered_list(construct_id)

    return items


@router.post('/{construct_id}/items', status_code=status.HTTP_201_CREATED)
async def create_construct_item(
    construct_id: uuid.UUID,
    new_item: SurveyItemCreate,
    item_service: SurveyItemServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:items', 'admin:all'))],
) -> dict[str, str]:
    """Create a new item for a survey construct.

    Args:
        construct_id: The UUID of the construct.
        new_item: The data for the new item.
        item_service: The survey item service.
        user: Auth check.

    Returns:
        A success message.
    """
    await item_service.create_for_owner(construct_id, new_item)

    return {'message': 'Construct item created.'}


@router.patch('/{construct_id}/items/reorder', status_code=204)
async def update_scale_levels_order(
    construct_id: uuid.UUID,
    service: SurveyItemServiceDep,
    payload: list[ReorderPayloadSchema],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('update:items', 'admin:all'))],
) -> None:
    """Update the order of items within a construct.

    Args:
        construct_id: The UUID of the construct.
        service: The survey item service.
        payload: List of item IDs and their new positions.
        user: Auth check.

    Returns:
        Empty dictionary on success.
    """
    levels_map = {item.id: item.order_position for item in payload}
    await service.reorder_items(construct_id, levels_map)
