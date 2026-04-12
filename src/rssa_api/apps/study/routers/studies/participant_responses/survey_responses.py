"""Router for survey responses."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from rssa_api.auth.authorization import get_current_participant, validate_api_key, validate_study_participant
from rssa_api.data.schemas.base_schemas import DBMixin
from rssa_api.data.schemas.participant_response_schemas import (
    ParticipantAttentionCheckResponseCreate,
    ParticipantSurveyResponseCreate,
    ParticipantSurveyResponseRead,
    UnifiedItemResponsePayload,
)
from rssa_api.data.services import ResponseType
from rssa_api.data.services.dependencies import ParticipantResponseServiceDep, SurveyItemServiceDep

survey_router = APIRouter(
    prefix='/survey',
    tags=['Participant responses - survey items'],
    dependencies=[Depends(validate_api_key), Depends(get_current_participant)],
)


@survey_router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=ParticipantSurveyResponseRead,
    summary='',
    description='',
    response_description='',
)
async def create_survey_item_response(
    unified_payload: UnifiedItemResponsePayload,
    service: ParticipantResponseServiceDep,
    item_service: SurveyItemServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Create a survey item response.

    Args:
        unified_payload: Protocol schema.
        service: Service for response operations.
        item_service: Service for the survey items.
        id_token: Validated participant token.

    Returns:
        Created response.
    """
    standard_item = await item_service.get(unified_payload.item_id, DBMixin)

    if standard_item:
        survey_create_payload = ParticipantSurveyResponseCreate(
            study_step_id=unified_payload.study_step_id,
            study_step_page_id=unified_payload.study_step_page_id,
            context_tag=unified_payload.context_tag,
            survey_construct_id=unified_payload.parent_id,
            survey_item_id=unified_payload.item_id,
            survey_scale_id=unified_payload.survey_scale_id,
            survey_scale_level_id=unified_payload.survey_scale_level_id,
        )
        return await service.create_response(survey_create_payload, id_token['sty'], id_token['sub'])

    ac_create_payload = ParticipantAttentionCheckResponseCreate(
        study_step_id=unified_payload.study_step_id,
        study_step_page_id=unified_payload.study_step_page_id,
        context_tag=unified_payload.context_tag,
        study_attention_check_id=unified_payload.item_id,
        survey_scale_id=unified_payload.survey_scale_id,
        responded_survey_scale_level_id=unified_payload.survey_scale_level_id,
    )

    saved_ac_response = await service.create_response(ac_create_payload, id_token['sty'], id_token['sub'])

    spoofed_return = ParticipantSurveyResponseRead(
        id=saved_ac_response.id,
        study_step_id=saved_ac_response.study_step_id,
        study_step_page_id=saved_ac_response.study_step_page_id,
        context_tag=saved_ac_response.context_tag,
        version=saved_ac_response.version,
        survey_construct_id=unified_payload.parent_id or uuid.uuid4(),  # Failsafe for Pydantic
        survey_item_id=saved_ac_response.study_attention_check_id,  # Mapped for React
        survey_scale_id=saved_ac_response.survey_scale_id,
        survey_scale_level_id=saved_ac_response.responded_survey_scale_level_id,  # Mapped for React
    )

    return spoofed_return


@survey_router.patch(
    '/{response_item_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary='',
    description='',
    response_description='',
)
async def update_survey_item_response(
    response_item_id: uuid.UUID,
    unified_payload: UnifiedItemResponsePayload,
    service: ParticipantResponseServiceDep,
    item_service: SurveyItemServiceDep,
    _: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Update a survey item response.

    Args:
        response_item_id: UUID of the response to update.
        unified_payload: Update data.
        service: Service for response operations.
        item_service: Service for the survey items.
        _: Validated participant token (unused).

    Returns:
        Status message.
    """
    standard_item = await item_service.get(unified_payload.item_id)

    if standard_item:
        response_type = ResponseType.SURVEY_ITEM
        update_dict = {'survey_scale_level_id': unified_payload.survey_scale_level_id}
    else:
        response_type = ResponseType.ATTENTION_CHECK
        update_dict = {'responded_survey_scale_level_id': unified_payload.survey_scale_level_id}

    update_successful = await service.update_response(
        response_type, response_item_id, update_dict, unified_payload.version
    )

    if not update_successful:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Resource version mismatch. Data was updated by another process',
        )
    if not update_successful:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Resource version mismatch. Data was updated by another process',
        )


@survey_router.get(
    '/{survey_page_id}',
    status_code=status.HTTP_200_OK,
    response_model=list[ParticipantSurveyResponseRead],
    summary='',
    description='',
    response_description='',
)
async def get_survey_item_response(
    survey_page_id: uuid.UUID,
    service: ParticipantResponseServiceDep,
    id_token: Annotated[dict[str, uuid.UUID], Depends(validate_study_participant)],
):
    """Get survey responses for a page.

    Args:
        survey_page_id: UUID of the page.
        service: Service for response operations.
        id_token: Validated participant token.

    Returns:
        List of responses.
    """
    standard_responses = await service.get_response_for_page(
        ResponseType.SURVEY_ITEM, id_token['sty'], id_token['sub'], survey_page_id
    )
    ac_responses = await service.get_response_for_page(
        ResponseType.ATTENTION_CHECK, id_token['sty'], id_token['sub'], survey_page_id
    )

    combined_responses = list(standard_responses)

    for ac in ac_responses:
        if ac.responded_survey_scale_level_id:
            spoofed_ac = ParticipantSurveyResponseRead(
                id=ac.id,
                study_step_id=ac.study_step_id,
                study_step_page_id=ac.study_step_page_id,
                context_tag=ac.context_tag,
                version=ac.version,
                survey_construct_id=uuid.uuid4(),
                survey_item_id=ac.study_attention_check_id,
                survey_scale_id=ac.survey_scale_id,
                survey_scale_level_id=ac.responded_survey_scale_level_id,
            )
            combined_responses.append(spoofed_ac)

    return combined_responses
