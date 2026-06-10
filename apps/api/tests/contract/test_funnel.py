"""Contract tests for funnel/timeseries API (M3-8)."""
import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.auth import create_access_token
from core.database import get_db
from main import app
from models.analytics import SegmentMetricSnapshot, VideoMetricSnapshot
from models.base import Base
from models.core import Organization, User, Video, VideoStatus
from models.segment import Segment, SegmentSet, SegmentSetStatus
from models.video import VideoAsset, VideoSignalConfig  # noqa: F401

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'segmentflow')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'segmentflow_dev')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'segmentflow_test')}"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded(db):
    """Seed an org + video + segment_set with 2 segments + snapshots."""
    org = Organization(id=uuid.uuid4(), name="Org", slug="org")
    user = User(
        id=uuid.uuid4(),
        email="u@test.com",
        name="U",
        password_hash="x",
        role="analyst",
    )
    db.add_all([org, user])
    db.flush()

    video = Video(
        id=uuid.uuid4(),
        organization_id=org.id,
        title="V",
        status=VideoStatus.analyzed,
        source_type="upload",
        uploaded_by=user.id,
    )
    db.add(video)
    db.flush()

    seg_set = SegmentSet(
        id=uuid.uuid4(),
        video_id=video.id,
        version_no=1,
        status=SegmentSetStatus.finalized,
        source="auto",
    )
    db.add(seg_set)
    db.flush()

    seg1 = Segment(
        id=uuid.uuid4(),
        segment_set_id=seg_set.id,
        seq_no=1,
        start_ms=0,
        end_ms=120_000,
        title="Intro",
        source_type="auto",
    )
    seg2 = Segment(
        id=uuid.uuid4(),
        segment_set_id=seg_set.id,
        seq_no=2,
        start_ms=120_000,
        end_ms=240_000,
        title="Core",
        source_type="auto",
    )
    db.add_all([seg1, seg2])
    db.flush()

    today = date(2026, 6, 11)
    snap1 = SegmentMetricSnapshot(
        id=uuid.uuid4(),
        video_id=video.id,
        segment_set_id=seg_set.id,
        segment_id=seg1.id,
        metric_date=today,
        cohort_type="all",
        placement_id=None,
        viewers_started=100,
        viewers_completed=92,
        completion_rate=Decimal("0.9200"),
        dropout_rate=Decimal("0.0800"),
        rewatch_rate=Decimal("0.05"),
        next_transition_rate=Decimal("0.89"),
        avg_pause_count=Decimal("1.20"),
        avg_seek_back_count=Decimal("0.30"),
        avg_speed_change_count=Decimal("0.10"),
        explicit_response_rate=Decimal("0.30"),
        confidence_positive_rate=Decimal("0.70"),
        confidence_unsure_rate=Decimal("0.20"),
        confidence_review_again_rate=Decimal("0.10"),
        learning_stability_score=Decimal("0.820"),
        risk_flags=[],
    )
    snap2 = SegmentMetricSnapshot(
        id=uuid.uuid4(),
        video_id=video.id,
        segment_set_id=seg_set.id,
        segment_id=seg2.id,
        metric_date=today,
        cohort_type="all",
        placement_id=None,
        viewers_started=92,
        viewers_completed=60,
        completion_rate=Decimal("0.6522"),
        dropout_rate=Decimal("0.3478"),
        rewatch_rate=Decimal("0.27"),
        next_transition_rate=Decimal("0.54"),
        avg_pause_count=Decimal("2.80"),
        avg_seek_back_count=Decimal("1.90"),
        avg_speed_change_count=Decimal("0.40"),
        explicit_response_rate=Decimal("0.12"),
        confidence_positive_rate=Decimal("0.43"),
        confidence_unsure_rate=Decimal("0.34"),
        confidence_review_again_rate=Decimal("0.23"),
        learning_stability_score=Decimal("0.420"),
        risk_flags=["dropout_spike", "rewatch_spike", "low_explicit_signal"],
    )
    video_snap = VideoMetricSnapshot(
        id=uuid.uuid4(),
        video_id=video.id,
        metric_date=today,
        cohort_type="all",
        placement_id=None,
        total_viewers=100,
        completion_rate=Decimal("0.7800"),
        avg_watch_rate=Decimal("0"),
        avg_watch_time_sec=Decimal("0"),
        next_transition_rate=Decimal("0.72"),
        explicit_response_rate=Decimal("0.21"),
    )
    db.add_all([snap1, snap2, video_snap])
    db.commit()
    return org, user, video, seg_set, [seg1, seg2], today


@pytest.fixture
def analyst_token(seeded):
    org, user, *_ = seeded
    return create_access_token(str(user.id), str(org.id), "analyst")


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestVideoFunnel:
    def test_get_funnel_returns_segments_with_metrics(
        self, client, seeded, analyst_token
    ):
        org, _, video, seg_set, segments, _ = seeded
        response = client.get(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/funnel",
            params={"segmentSetId": str(seg_set.id)},
            headers=_auth(analyst_token),
        )
        assert response.status_code == 200
        body = response.json()["data"]

        assert body["videoSummary"]["completionRate"] == 0.78
        assert body["videoSummary"]["nextTransitionRate"] == 0.72
        assert len(body["segments"]) == 2

        seg1 = body["segments"][0]
        assert seg1["segment"]["seqNo"] == 1
        assert seg1["metrics"]["viewersStarted"] == 100
        assert seg1["metrics"]["completionRate"] == 0.92
        assert seg1["riskFlags"] == []

        seg2 = body["segments"][1]
        assert seg2["metrics"]["dropoutRate"] == 0.3478
        assert "dropout_spike" in seg2["riskFlags"]
        assert "low_explicit_signal" in seg2["riskFlags"]

    def test_get_funnel_unauthorized(self, client, seeded):
        org, _, video, seg_set, *_ = seeded
        response = client.get(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/funnel",
            params={"segmentSetId": str(seg_set.id)},
        )
        assert response.status_code == 401

    def test_get_funnel_video_not_found(self, client, seeded, analyst_token):
        org, _, _, seg_set, *_ = seeded
        response = client.get(
            f"/api/v1/orgs/{org.id}/videos/{uuid.uuid4()}/funnel",
            params={"segmentSetId": str(seg_set.id)},
            headers=_auth(analyst_token),
        )
        assert response.status_code == 404

    def test_get_funnel_returns_empty_segments_when_no_snapshots(
        self, client, seeded, analyst_token, db
    ):
        org, _, video, seg_set, segments, _ = seeded
        # Wipe snapshots
        from sqlalchemy import delete
        db.execute(delete(SegmentMetricSnapshot))
        db.execute(delete(VideoMetricSnapshot))
        db.commit()

        response = client.get(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/funnel",
            params={"segmentSetId": str(seg_set.id)},
            headers=_auth(analyst_token),
        )
        assert response.status_code == 200
        body = response.json()["data"]
        assert len(body["segments"]) == 2
        # All zeros, no risk flags
        assert body["segments"][0]["metrics"]["viewersStarted"] == 0
        assert body["segments"][0]["riskFlags"] == []


class TestSegmentTimeseries:
    def test_get_timeseries_returns_single_point(
        self, client, seeded, analyst_token
    ):
        org, _, _, _, segments, today = seeded
        response = client.get(
            f"/api/v1/orgs/{org.id}/segments/{segments[0].id}/metrics/timeseries",
            params={
                "dateFrom": today.isoformat(),
                "dateTo": today.isoformat(),
            },
            headers=_auth(analyst_token),
        )
        assert response.status_code == 200
        body = response.json()["data"]
        assert body["segmentId"] == str(segments[0].id)
        assert len(body["series"]) == 1
        assert body["series"][0]["completionRate"] == 0.92

    def test_get_timeseries_forbidden_for_other_org(
        self, client, seeded, analyst_token, db
    ):
        _, _, _, _, segments, today = seeded
        other_org = uuid.uuid4()
        response = client.get(
            f"/api/v1/orgs/{other_org}/segments/{segments[0].id}/metrics/timeseries",
            params={
                "dateFrom": today.isoformat(),
                "dateTo": today.isoformat(),
            },
            headers=_auth(analyst_token),
        )
        assert response.status_code == 403
