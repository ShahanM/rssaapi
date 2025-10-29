import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.schemas.participant_response_schemas import (
    ParticipantContentRatingPayload,
    RatedItemSchema,
)
from rssa_api.data.services.response_service import ParticipantResponseService
from rssa_api.data.services.rssa_dependencies import get_response_service as response_service

ratings_router = APIRouter(
    prefix='/ratings',
    tags=['Participant responses - ratings'],
)


@ratings_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=RatedItemSchema,
    summary='',
    description='',
    response_description='',
)
async def create_content_Rating(
    rating: ParticipantContentRatingPayload,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    content_rating = await service.create_content_rating(id_token['sid'], id_token['pid'], rating)

    return content_rating


@ratings_router.patch(
    '/{rating_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary='',
    description='',
    response_description='',
)
async def update_content_rating(
    rating_id: uuid.UUID,
    item_rating: RatedItemSchema,
    service: Annotated[ParticipantResponseService, Depends(response_service)],
    _: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    client_version = item_rating.version
    update_successful = await service.update_content_rating(
        rating_id, item_rating.model_dump(exclude={'version'}), client_version
    )

    if not update_successful:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Resource version mismatch. Data was updated by another process',
        )


@ratings_router.get(
    '/',  # FIXME: This should be page_id but currently we do not support pages for non-survey steps
    response_model=list[Any],
    summary='',
    description='',
    response_description='',
)
async def get_user_ratings(
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
    service: Annotated[ParticipantResponseService, Depends(response_service)],
):
    print(id_token)
    ratings = await service.get_ratings_for_participants(id_token['sid'], id_token['pid'])
    print(id_token)
    return ratings
