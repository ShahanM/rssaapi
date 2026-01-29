"""Router for managing survey scales in the admin API."""

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import PreviewSchema, ReorderPayloadSchema, SortDir
from rssa_api.data.schemas.survey_components import (
    PaginatedConstructResponse,
    SurveyScaleCreate,
    SurveyScaleLevelCreate,
    SurveyScaleLevelRead,
    SurveyScaleRead,
)
from rssa_api.data.services.dependencies import SurveyScaleLevelServiceDep, SurveyScaleServiceDep

from ...docs import ADMIN_CONSTRUCT_SCALES_TAG

router = APIRouter(
    prefix='/scales',
    tags=[ADMIN_CONSTRUCT_SCALES_TAG],
    dependencies=[
        Depends(require_permissions('read:scales', 'admin:all')),
        Depends(get_auth0_authenticated_user),
    ],
)


@router.get(
    '/',
    response_model=PaginatedConstructResponse,
    summary='Get a paginated list of survey scales.',
    description="""
    Retrieves a paginated list of all survey scales.
    Supports sorting and searching.
    """,
    response_description='A paginated response containing survey scales.',
)
async def get_construct_scales(
    service: SurveyScaleServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:scales', 'admin:all'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: str | None = Query(None, description='The field to sort by.'),
    sort_dir: SortDir | None = Query(None, description='The direction to sort (asc or desc)'),
    search: str | None = Query(None, description='A search term to filter results by name or description'),
) -> PaginatedConstructResponse:
    """Get a paginated list of survey scales.

    Args:
        service: The survey scale service.
        _: Authorization check.
        page_index: The page number (0-indexed).
        page_size: Items per page.
        sort_by: Field to sort by.
        sort_dir: Sort direction.
        search: Search term.

    Returns:
        Paginated list of scales.
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
    page_count = math.ceil(total_items / page_size) if total_items > 0 else 1

    return PaginatedConstructResponse(rows=constructs_from_db, page_count=page_count)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_construct_scale(
    create_scale: SurveyScaleCreate,
    service: SurveyScaleServiceDep,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:scales', 'admin:all'))],
) -> dict[str, str]:
    """Create a new survey scale.

    Args:
        create_scale: Data for the new scale.
        service: The survey scale service.
        user: The authenticated user.

    Returns:
        Status message.
    """
    await service.create(create_scale)

    return {'message': 'Construct Scale created'}


@router.get('/{scale_id}', response_model=SurveyScaleRead)
async def get_construct_scale_detail(
    service: SurveyScaleServiceDep,
    scale_id: uuid.UUID,
) -> SurveyScaleRead:
    """Get details of a survey scale.

    Args:
        service: The survey scale service.
        scale_id: The UUID of the scale.

    Raises:
        HTTPException: If scale is not found.

    Returns:
        The scale details.
    """
    scale_in_db = await service.get_detailed(scale_id)
    if not scale_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Construct scale not found.')

    return SurveyScaleRead.model_validate(scale_in_db)


@router.get('/{scale_id}/summary', response_model=SurveyScaleRead)
async def get_construct_scale(
    service: SurveyScaleServiceDep,
    scale_id: uuid.UUID,
) -> SurveyScaleRead:
    """Get a summary of a survey scale.

    Args:
        service: The survey scale service.
        scale_id: The UUID of the scale.

    Raises:
        HTTPException: If scale is not found.

    Returns:
        The scale summary.
    """
    scale_in_db = await service.get_detailed(scale_id)
    if not scale_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Construct scale not found.')

    return SurveyScaleRead.model_validate(scale_in_db)


@router.patch('/{scale_id}', status_code=status.HTTP_204_NO_CONTENT)
async def update_survey_scale(
    scale_id: uuid.UUID,
    payload: dict[str, str],
    service: SurveyScaleServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('update:scales', 'admin:all'))],
) -> dict[str, str]:
    """Update a survey scale.

    Args:
        scale_id: The UUID of the scale to update.
        payload: Fields to update.
        service: The survey scale service.
        _: Authorization check.

    Returns:
        Empty dictionary on success.
    """
    await service.update(scale_id, payload)

    return {}


@router.delete('/{scale_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_construct_scale(
    service: SurveyScaleServiceDep,
    scale_id: uuid.UUID,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:scales', 'admin:all'))],
) -> dict[str, str]:
    """Delete a survey scale.

    Args:
        service: The survey scale service.
        scale_id: The UUID of the scale to delete.
        user: The authenticated user.

    Returns:
        Empty dictionary on success.
    """
    await service.repo.delete(scale_id)

    return {}


@router.get('/{scale_id}/levels', response_model=list[SurveyScaleLevelRead])
async def get_scale_levels(
    scale_id: uuid.UUID,
    service: SurveyScaleLevelServiceDep,
) -> list[SurveyScaleLevelRead]:
    """Get levels associated with a survey scale.

    Args:
        scale_id: The UUID of the scale.
        service: The scale level service.

    Returns:
        A list of ordered scale levels.
    """
    levels_in_db = await service.get_items_for_owner_as_ordered_list(scale_id)
    if not levels_in_db:
        return []
    converted = [SurveyScaleLevelRead.model_validate(c) for c in levels_in_db]

    return converted


@router.post('/{scale_id}/levels', response_model=SurveyScaleLevelRead)
async def create_scale_level(
    scale_id: uuid.UUID,
    new_level: SurveyScaleLevelCreate,
    service: SurveyScaleLevelServiceDep,
    _: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'create:levels'))],
) -> SurveyScaleLevelRead:
    """Create a new level for a survey scale.

    Args:
        scale_id: The UUID of the scale.
        new_level: Data for the new level.
        service: The scale level service.
        _: Authorization check.

    Raises:
        HTTPException: If scale_id in URL does not match payload.

    Returns:
        The created scale level.
    """
    if scale_id != new_level.survey_scale_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='There was an error due to scale mismatch.')
    new_scale_in_db = await service.create_for_owner(scale_id, new_level)

    return SurveyScaleLevelRead.model_validate(new_scale_in_db)


@router.put('/{scale_id}/levels/order', status_code=status.HTTP_204_NO_CONTENT)
async def update_scale_levels_order(
    scale_id: uuid.UUID,
    service: SurveyScaleLevelServiceDep,
    payload: list[ReorderPayloadSchema],
) -> dict[str, str]:
    """Reorder levels within a survey scale.

    Args:
        scale_id: The UUID of the scale.
        service: The scale level service.
        payload: List of level IDs and new positions.

    Returns:
        Empty dictionary on success.
    """
    levels_map = {level.id: level.order_position for level in payload}
    await service.reorder_items(scale_id, levels_map)

    return {}
