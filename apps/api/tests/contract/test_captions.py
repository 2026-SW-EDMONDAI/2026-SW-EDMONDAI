"""Contract tests for caption API (M2-2)."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.auth import create_access_token
from core.database import get_db
from main import app
from models.base import Base
from models.core import Organization, User, Video, VideoStatus
from models.video import CaptionCue, CaptionTrack, VideoSignalConfig  # noqa: F401
from models.segment import SegmentSet, Segment  # noqa: F401

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
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
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def base_data(db):
    org = Organization(id=uuid.uuid4(), name="Cap Org", slug="cap-org")
    user = User(id=uuid.uuid4(), email="u@cap.com", name="U", password_hash="h", role="operator")
    db.add_all([org, user])
    db.flush()
    video = Video(
        id=uuid.uuid4(),
        organization_id=org.id,
        title="Caption Test",
        status=VideoStatus.analyzed,
        source_type="upload",
        uploaded_by=user.id,
    )
    db.add(video)
    db.flush()
    track = CaptionTrack(
        id=uuid.uuid4(), video_id=video.id, language_code="ko", source="uploaded", is_default=True
    )
    db.add(track)
    db.flush()
    cues = [
        CaptionCue(id=uuid.uuid4(), caption_track_id=track.id, seq_no=i, start_ms=i * 4000, end_ms=(i + 1) * 4000, text=f"Cue {i}")
        for i in range(1, 4)
    ]
    db.add_all(cues)
    db.commit()
    token = create_access_token({"sub": str(user.id), "orgId": str(org.id), "orgRole": "operator"})
    return org, video, token


def test_get_caption_cues(client, base_data):
    org, video, token = base_data
    response = client.get(
        f"/api/v1/orgs/{org.id}/videos/{video.id}/captions/cues",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3
    assert data[0]["seqNo"] == 1
    assert data[0]["text"] == "Cue 1"


def test_get_caption_cues_with_range(client, base_data):
    org, video, token = base_data
    response = client.get(
        f"/api/v1/orgs/{org.id}/videos/{video.id}/captions/cues?startMs=4000&endMs=8000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(c["endMs"] >= 4000 and c["startMs"] <= 8000 for c in data)


def test_get_caption_cues_no_track_returns_empty(client, db, base_data):
    org, _, token = base_data
    # New video with no tracks
    from models.core import User
    user = db.get(User, db.query(User).first().id)
    new_video = Video(
        id=uuid.uuid4(),
        organization_id=org.id,
        title="No Track",
        status=VideoStatus.uploaded,
        source_type="upload",
        uploaded_by=user.id,
    )
    db.add(new_video)
    db.commit()

    response = client.get(
        f"/api/v1/orgs/{org.id}/videos/{new_video.id}/captions/cues",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"] == []
