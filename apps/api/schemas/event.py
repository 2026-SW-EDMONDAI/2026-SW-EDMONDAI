import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from models.analytics import EventType, SignalMode


class EventItem(BaseModel):
    clientEventId: str = Field(..., min_length=1, max_length=80)
    signalMode: SignalMode
    eventType: EventType
    segmentId: uuid.UUID | None = None
    positionMs: int | None = Field(default=None, ge=0)
    eventValue: str | None = Field(default=None, max_length=100)
    payload: dict | None = None
    occurredAt: datetime


class EventBatchRequest(BaseModel):
    organizationId: uuid.UUID
    videoId: uuid.UUID
    segmentSetId: uuid.UUID | None = None
    learnerSessionId: uuid.UUID | None = None
    anonymousUserKey: str | None = Field(default=None, max_length=128)
    devicePlatform: str | None = Field(default=None, max_length=30)
    deviceType: str | None = Field(default=None, max_length=30)
    countryCode: str | None = Field(default=None, max_length=5)
    events: list[EventItem] = Field(..., min_length=1, max_length=200)


class EventBatchResponse(BaseModel):
    accepted: int
    rejected: int
    learnerSessionId: uuid.UUID
    duplicates: int = 0
