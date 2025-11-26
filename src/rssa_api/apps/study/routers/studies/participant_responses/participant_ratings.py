"""Participant Ratings Router.

Handles endpoints related to participant content ratings.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import validate_study_participant
from rssa_api.data.schemas.participant_response_schemas import (
    ParticipantContentRatingPayload,
    RatedItemSchema,
)
from rssa_api.data.services import ParticipantResponseServiceDep, ResponseType
from rssa_api.data.services.participant_responses.response_service import ParticipantResponseService

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
    service: ParticipantResponseServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Create a new content rating for a study participant.

    Args:
        rating: The content rating data to be created.
        service: The participant response service.
        id_token: The validated study and participant IDs.

    Returns:
        The created content rating.
    """
    content_rating = await service.create_response(id_token['sid'], id_token['pid'], rating)

    return content_rating


@ratings_router.patch(
    '/{rating_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def update_content_rating(
    rating_id: uuid.UUID,
    item_rating: RatedItemSchema,
    service: ParticipantResponseServiceDep,
    _: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Update an existing content rating for a study participant.

    Args:
        rating_id: The ID of the content rating to be updated.
        item_rating: The updated content rating data.
        service: The participant response service.
        _: The validated study and participant IDs.

    Raises:
        HTTPException: If there is a version conflict during the update.
    """
    client_version = item_rating.version
    update_successful = await service.update_response(
        ResponseType.CONTENT_RATING, rating_id, item_rating.model_dump(exclude={'version'}), client_version
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
    page_id: uuid.UUID,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
    service: ParticipantResponseServiceDep,
):
    """Retrieve all content ratings for a study participant.

    Args:
        id_token: The validated study and participant IDs.
        service: The participant response service.

    Returns:
        A list of content ratings for the participant.
    """
    ratings = await service.get_response_for_page(
        ResponseType.CONTENT_RATING, id_token['sid'], id_token['pid'], page_id
    )
    return ratings
