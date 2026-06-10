import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import OrgContext, require_analyst
from services.funnel_service import FunnelService

router = APIRouter(prefix="/api/v1/orgs/{orgId}", tags=["funnel"])


def _meta() -> dict:
    return {
        "requestId": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/videos/{videoId}/funnel", dependencies=[Depends(require_analyst)])
def get_video_funnel(
    orgId: OrgContext,
    videoId: uuid.UUID,
    segmentSetId: uuid.UUID = Query(...),
    metricDate: date | None = Query(None),
    cohortType: str = Query("all"),
    placementId: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    svc = FunnelService(db)
    data = svc.get_video_funnel(
        org_id=orgId,
        video_id=videoId,
        segment_set_id=segmentSetId,
        metric_date=metricDate,
        cohort_type=cohortType,
        placement_id=placementId,
    )
    return {"data": data, "meta": _meta()}


@router.get(
    "/segments/{segmentId}/metrics/timeseries",
    dependencies=[Depends(require_analyst)],
)
def get_segment_timeseries(
    orgId: OrgContext,
    segmentId: uuid.UUID,
    dateFrom: date = Query(...),
    dateTo: date = Query(...),
    cohortType: str = Query("all"),
    placementId: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
):
    svc = FunnelService(db)
    data = svc.get_segment_timeseries(
        org_id=orgId,
        segment_id=segmentId,
        date_from=dateFrom,
        date_to=dateTo,
        cohort_type=cohortType,
        placement_id=placementId,
    )
    return {"data": data, "meta": _meta()}
