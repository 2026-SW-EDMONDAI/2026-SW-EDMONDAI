import uuid
from datetime import date

from pydantic import BaseModel


class SegmentMetrics(BaseModel):
    viewersStarted: int
    viewersCompleted: int
    completionRate: float
    dropoutRate: float
    rewatchRate: float
    nextTransitionRate: float
    avgPauseCount: float
    avgSeekBackCount: float
    avgSpeedChangeCount: float
    explicitResponseRate: float
    confidencePositiveRate: float | None = None
    confidenceUnsureRate: float | None = None
    confidenceReviewAgainRate: float | None = None
    learningStabilityScore: float | None = None


class SegmentInfo(BaseModel):
    id: uuid.UUID
    seqNo: int
    title: str
    startMs: int
    endMs: int


class SegmentFunnelEntry(BaseModel):
    segment: SegmentInfo
    metrics: SegmentMetrics
    riskFlags: list[str] = []


class VideoFunnelSummary(BaseModel):
    videoId: uuid.UUID
    segmentSetId: uuid.UUID
    metricDate: date
    completionRate: float
    nextTransitionRate: float | None = None
    explicitResponseRate: float | None = None


class FunnelResponse(BaseModel):
    videoSummary: VideoFunnelSummary
    segments: list[SegmentFunnelEntry]


class TimeseriesPoint(BaseModel):
    metricDate: date
    completionRate: float
    nextTransitionRate: float
    explicitResponseRate: float


class SegmentTimeseriesResponse(BaseModel):
    segmentId: uuid.UUID
    series: list[TimeseriesPoint]
