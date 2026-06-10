"""Contract tests for player event collection API (M3-3)."""
import os
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.database import get_db
from core.player_auth import create_player_token
from main import app
from models.analytics import LearningEvent  # noqa: F401
from models.base import Base
from models.core import Organization, User, Video, VideoStatus
from models.segment import Segment, SegmentSet  # noqa: F401
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
def org_user_video(db):
    org = Organization(id=uuid.uuid4(), name="Org", slug="org")
    user = User(
        id=uuid.uuid4(),
        email="u@test.com",
        name="U",
        password_hash="x",
        role="operator",
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
    db.commit()
    return org, user, video


@pytest.fixture
def player_token(org_user_video):
    org, _user, video = org_user_video
    return create_player_token(str(org.id), str(video.id), "anon_test_001")


def _evt(client_event_id: str, segment_id=None, signal="implicit", etype="segment_start"):
    return {
        "clientEventId": client_event_id,
        "signalMode": signal,
        "eventType": etype,
        "segmentId": str(segment_id) if segment_id else None,
        "positionMs": 0,
        "occurredAt": datetime.now(timezone.utc).isoformat(),
    }


class TestEventBatchAuth:
    def test_missing_token_returns_401(self, client, org_user_video):
        org, _, video = org_user_video
        response = client.post(
            "/player/events/batch",
            json={
                "organizationId": str(org.id),
                "videoId": str(video.id),
                "events": [_evt("evt-1")],
            },
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "PLAYER_TOKEN_INVALID"

    def test_invalid_token_returns_401(self, client, org_user_video):
        org, _, video = org_user_video
        response = client.post(
            "/player/events/batch",
            headers={"X-Player-Token": "not.a.jwt"},
            json={
                "organizationId": str(org.id),
                "videoId": str(video.id),
                "events": [_evt("evt-1")],
            },
        )
        assert response.status_code == 401

    def test_token_video_mismatch_returns_403(
        self, client, org_user_video, player_token
    ):
        org, _, _ = org_user_video
        other_video = uuid.uuid4()
        response = client.post(
            "/player/events/batch",
            headers={"X-Player-Token": player_token},
            json={
                "organizationId": str(org.id),
                "videoId": str(other_video),
                "events": [_evt("evt-1")],
            },
        )
        assert response.status_code == 403


class TestEventBatchIngestion:
    def test_accepts_valid_batch(self, client, db, org_user_video, player_token):
        org, _, video = org_user_video
        response = client.post(
            "/player/events/batch",
            headers={"X-Player-Token": player_token},
            json={
                "organizationId": str(org.id),
                "videoId": str(video.id),
                "anonymousUserKey": "anon_test_001",
                "events": [
                    _evt("evt-1"),
                    _evt("evt-2", etype="pause"),
                    {
                        "clientEventId": "evt-3",
                        "signalMode": "explicit",
                        "eventType": "confidence_check_submit",
                        "eventValue": "understood",
                        "occurredAt": datetime.now(timezone.utc).isoformat(),
                    },
                ],
            },
        )
        assert response.status_code == 202
        body = response.json()["data"]
        assert body["accepted"] == 3
        assert body["rejected"] == 0
        assert body["duplicates"] == 0
        assert body["learnerSessionId"] is not None

        rows = db.scalars(select(LearningEvent)).all()
        assert len(rows) == 3

    def test_duplicate_client_event_id_is_idempotent(
        self, client, db, org_user_video, player_token
    ):
        org, _, video = org_user_video
        payload = {
            "organizationId": str(org.id),
            "videoId": str(video.id),
            "anonymousUserKey": "anon_dup",
            "events": [_evt("evt-dup")],
        }
        first = client.post(
            "/player/events/batch",
            headers={"X-Player-Token": player_token},
            json=payload,
        )
        assert first.status_code == 202
        session_id = first.json()["data"]["learnerSessionId"]

        payload["learnerSessionId"] = session_id
        second = client.post(
            "/player/events/batch",
            headers={"X-Player-Token": player_token},
            json=payload,
        )
        assert second.status_code == 202
        body = second.json()["data"]
        assert body["accepted"] == 0
        assert body["duplicates"] == 1

        rows = db.scalars(select(LearningEvent)).all()
        assert len(rows) == 1

    def test_invalid_event_type_returns_422(
        self, client, org_user_video, player_token
    ):
        org, _, video = org_user_video
        response = client.post(
            "/player/events/batch",
            headers={"X-Player-Token": player_token},
            json={
                "organizationId": str(org.id),
                "videoId": str(video.id),
                "events": [
                    {
                        "clientEventId": "evt-bad",
                        "signalMode": "implicit",
                        "eventType": "not_a_real_event",
                        "occurredAt": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            },
        )
        assert response.status_code == 422
