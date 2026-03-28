"""Telemetry service."""

import uuid

from rssa_storage.telemetrydb.models import ParticipantTelemetry
from rssa_storage.telemetrydb.repositories import TelemetryRepo

from rssa_api.data.schemas.telemetry import TelemetryBatchPayload


class TelemetryService:
    """Service to help record implicit behavior data."""

    def __init__(self, repository: TelemetryRepo):
        """Initialization code! Why do I need to document this?"""
        self.repository = repository

    async def process_batch(
        self, participant_id: uuid.UUID, session_id: uuid.UUID, study_id: uuid.UUID, payload: TelemetryBatchPayload
    ) -> None:
        """Transforms the batch payload into models and executes a bulk insert."""
        instances = [
            ParticipantTelemetry(
                participant_id=participant_id,
                session_id=session_id,
                study_id=study_id,
                event_type=event.event_type,
                item_id=event.item_id,
                event_data=event.event_data,
                client_timestamp=event.client_timestamp,
            )
            for event in payload.events
        ]

        await self.repository.create_all(instances)
