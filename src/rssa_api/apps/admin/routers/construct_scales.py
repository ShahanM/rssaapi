import math
import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from rssa_api.auth.security import get_auth0_authenticated_user, require_permissions
from rssa_api.data.schemas import Auth0UserSchema
from rssa_api.data.schemas.base_schemas import PreviewSchema, ReorderPayloadSchema, SortDir
from rssa_api.data.schemas.survey_constructs import (
    ConstructScaleBaseSchema,
    ConstructScaleSchema,
    ScaleLevelBaseSchema,
    ScaleLevelSchema,
)
from rssa_api.data.services import ConstructScaleService, ScaleLevelService
from rssa_api.data.services.survey_dependencies import get_construct_scale_service as scales_service
from rssa_api.data.services.survey_dependencies import get_scale_level_service as level_service

from ..docs import ADMIN_CONSTRUCT_SCALES_TAG

router = APIRouter(
    prefix='/scales',
    tags=[ADMIN_CONSTRUCT_SCALES_TAG],
    dependencies=[
        Depends(scales_service),
        Depends(require_permissions('read:construct_scales')),
        Depends(get_auth0_authenticated_user),
    ],
)


class PaginatedConstructResponse(BaseModel):
    rows: list[PreviewSchema]
    page_count: int

    class Config:
        from_attribute = True


@router.get(
    '/',
    response_model=PaginatedConstructResponse,
    summary='',
    description="""
	""",
    response_description='',
)
async def get_construct_scales(
    service: Annotated[ConstructScaleService, Depends(scales_service)],
    _: Annotated[Auth0UserSchema, Depends(require_permissions('read:scales', 'admin:all'))],
    page_index: int = Query(0, ge=0, description='The page number to retrieve (0-indexed)'),
    page_size: int = Query(10, ge=1, le=100, description='The number of items per page'),
    sort_by: Optional[str] = Query(None, description='The field to sort by.'),
    sort_dir: Optional[SortDir] = Query(None, description='The direction to sort (asc or desc)'),
    search: Optional[str] = Query(None, description='A search term to filter results by name or description'),
):
    offset = page_index * page_size
    total_items = await service.count_scales(search=search)
    constructs_from_db = await service.get_construct_scales(
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sort_dir.value if sort_dir else None,
        search=search,
    )
    page_count = math.ceil(total_items / page_size) if total_items > 0 else 1

    return PaginatedConstructResponse(rows=constructs_from_db, page_count=page_count)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_construct_scale(
    create_scale: ConstructScaleBaseSchema,
    service: Annotated[ConstructScaleService, Depends(scales_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('create:construct_scales', 'admin:all'))],
):
    await service.create_construct_scale(create_scale, created_by=user.sub)

    return {'message': 'Construct Scale created'}


@router.get('/{scale_id}', response_model=ConstructScaleSchema)
async def get_construct_scale_detail(
    service: Annotated[ConstructScaleService, Depends(scales_service)],
    scale_id: uuid.UUID,
):
    scale_in_db = await service.get_construct_scale_detail(scale_id)
    if not scale_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Construct scale not found.')

    return ConstructScaleSchema.model_validate(scale_in_db)


@router.get('/{scale_id}/summary', response_model=ConstructScaleSchema)
async def get_construct_scale(
    service: Annotated[ConstructScaleService, Depends(scales_service)],
    scale_id: uuid.UUID,
):
    scale_in_db = await service.get_construct_scale(scale_id)
    if not scale_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Construct scale not found.')

    return ConstructScaleSchema.model_validate(scale_in_db)


@router.delete('/{scale_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_construct_scale(
    service: Annotated[ConstructScaleService, Depends(scales_service)],
    scale_id: uuid.UUID,
    user: Annotated[Auth0UserSchema, Depends(require_permissions('delete:construct_scale', 'admin:all'))],
):
    await service.repo.delete(scale_id)

    return {}


@router.get('/{scale_id}/levels', response_model=list[ScaleLevelSchema])
async def get_scale_levels(
    scale_id: uuid.UUID,
    service: Annotated[ConstructScaleService, Depends(scales_service)],
):
    levels_in_db = await service.get_scale_levels(scale_id)
    if not levels_in_db:
        return []
    converted = [ScaleLevelSchema.model_validate(c) for c in levels_in_db]

    return converted


@router.post('/{scale_id}', response_model=ScaleLevelSchema)
async def create_scale_level(
    scale_id: uuid.UUID,
    new_level: ScaleLevelBaseSchema,
    service: Annotated[ScaleLevelService, Depends(level_service)],
    user: Annotated[Auth0UserSchema, Depends(require_permissions('admin:all', 'create:levels'))],
):
    if scale_id != new_level.scale_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='There was an error due to scale mismatch.')
    new_scale_in_db = await service.create_scale_level(scale_id, new_level)

    return ScaleLevelSchema.model_validate(new_scale_in_db)


@router.put('/{scale_id}/levels/order', status_code=status.HTTP_204_NO_CONTENT)
async def update_scale_levels_order(
    scale_id: uuid.UUID,
    service: Annotated[ConstructScaleService, Depends(scales_service)],
    payload: list[ReorderPayloadSchema],
):
    levels_map = {level.id: level.order_position for level in payload}
    await service.reorder_scale_levels(scale_id, levels_map)

    return {}
