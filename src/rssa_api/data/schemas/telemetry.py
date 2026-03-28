"""Schemas for Telemetry."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TrafficPayload(BaseModel):
    study_id: str
    session_data: str
    timestamp: datetime


class TelemetryEventSchema(BaseModel):
    event_type: str
    item_id: str | None
    event_data: dict[str, Any] = Field(default_factory=dict)
    client_timestamp: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TelemetryBatchPayload(BaseModel):
    """The batch payload sent by the React useTelemetryBatcher hook."""

    events: list[TelemetryEventSchema]
