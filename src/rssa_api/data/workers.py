# rssa_api/data/workers.py
import asyncio
import logging
from datetime import datetime

from rssa_storage.rssadb.models.study_participants import ParticipantRecommendationContext
from rssa_storage.rssadb.repositories.participant_responses import (
    ParticipantStudyInteractionResponse,
    ParticipantStudyInteractionResponseRepository,
)
from rssa_storage.rssadb.repositories.study_participants import ParticipantRecommendationContextRepository
from rssa_storage.shared import RepoQueryOptions

from rssa_api.core.queue import background_write_queue
from rssa_api.data.schemas.participant_response_schemas import DynamicPayload
from rssa_api.data.sources.rssadb import AsyncSessionLocal

log = logging.getLogger(__name__)


async def process_save_rec_context(session, payload: dict):
    repo = ParticipantRecommendationContextRepository(session)
    rec_ctx = ParticipantRecommendationContext(
        study_id=payload['study_id'],
        study_step_id=payload['step_id'],
        study_step_page_id=payload['step_page_id'],
        study_participant_id=payload['study_participant_id'],
        context_tag=payload['context_tag'],
        recommendations_json=payload['result_json'],
    )
    await repo.create(rec_ctx)


async def process_upsert_interaction(session, payload: dict):
    repo = ParticipantStudyInteractionResponseRepository(session)
    ctx_data = payload['context_data']
    step_id = ctx_data.get('step_id')

    if not step_id:
        return

    context_tag = ctx_data.get('tuning_tag', 'emotion_tuning')

    existing = await repo.find_one(
        RepoQueryOptions(
            filters={
                'study_participant_id': payload['study_participant_id'],
                'context_tag': context_tag,
                'study_step_id': step_id,
            }
        )
    )

    new_entry = {
        'timestamp': datetime.now().isoformat(),
        'emotion_input': ctx_data['emotion_input'],
    }

    if existing:
        current_payload = existing.payload_json
        history = current_payload.get('history', [])
        if not isinstance(history, list):
            history = []
        history.append(new_entry)
        await repo.update(existing.id, {'payload_json': {**current_payload, 'history': history}})
    else:
        new_payload = ParticipantStudyInteractionResponse(
            study_id=payload['study_id'],
            study_participant_id=payload['study_participant_id'],
            study_step_id=step_id,
            context_tag=context_tag,
            payload_json=DynamicPayload(extra={'history': [new_entry]}).model_dump(),
        )
        await repo.create(new_payload)


async def db_writer_worker():
    """Consumes commands and executes them using fresh DB sessions."""
    log.info('Background DB Writer Worker started.')
    while True:
        try:
            command = await background_write_queue.get()

            async with AsyncSessionLocal() as session:
                try:
                    if command.task_name == 'save_rec_context':
                        await process_save_rec_context(session, command.payload)
                    elif command.task_name == 'upsert_interaction':
                        await process_upsert_interaction(session, command.payload)
                    else:
                        log.warning(f'Unknown background task: {command.task_name}')

                    await session.commit()
                except Exception as e:
                    log.error(f"Error in background task '{command.task_name}': {e}")
                    await session.rollback()
                finally:
                    background_write_queue.task_done()

        except asyncio.CancelledError:
            log.info('Background DB Writer Worker shutting down.')
            break
