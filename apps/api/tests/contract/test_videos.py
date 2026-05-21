"""Contract tests for video management API (M2-2)."""
import io
import os
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.auth import create_access_token
from core.database import get_db
from main import app
from models.base import Base
from models.core import Organization, User, VideoStatus  # noqa: F401
from models.video import VideoAsset, VideoSignalConfig  # noqa: F401
from models.segment import SegmentSet, Segment  # noqa: F401

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
def org_and_user(db):
    org = Organization(id=uuid.uuid4(), name="Test Org", slug="test-org")
    user = User(
        id=uuid.uuid4(),
        email="op@test.com",
        name="Operator",
        password_hash="hashed",
        role="operator",
    )
    db.add(org)
    db.add(user)
    db.commit()
    return org, user


@pytest.fixture
def operator_token(org_and_user):
    org, user = org_and_user
    return create_access_token(str(user.id), str(org.id), "operator")


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestVideoList:
    def test_list_videos_empty(self, client, org_and_user, operator_token):
        org, _ = org_and_user
        response = client.get(
            f"/api/v1/orgs/{org.id}/videos",
            headers=auth_headers(operator_token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"] == []
        assert body["meta"]["total"] == 0

    def test_list_videos_unauthorized(self, client, org_and_user):
        org, _ = org_and_user
        response = client.get(f"/api/v1/orgs/{org.id}/videos")
        assert response.status_code == 401


class TestVideoCreate:
    def test_create_video_success(self, client, org_and_user, operator_token):
        org, _ = org_and_user
        with patch("services.video_service.VideoService._save_file", return_value="/tmp/test.mp4"):
            response = client.post(
                f"/api/v1/orgs/{org.id}/videos",
                headers=auth_headers(operator_token),
                data={
                    "title": "Test Video",
                    "description": "A test video",
                    "sourceType": "upload",
                    "confidenceCheckEnabled": "true",
                },
                files={"videoFile": ("test.mp4", io.BytesIO(b"fake"), "video/mp4")},
            )
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["video"]["title"] == "Test Video"
        assert body["data"]["video"]["status"] == "uploaded"
        assert body["data"]["signalConfig"]["confidenceCheckEnabled"] is True

    def test_create_video_wrong_org(self, client, operator_token):
        wrong_org = uuid.uuid4()
        response = client.post(
            f"/api/v1/orgs/{wrong_org}/videos",
            headers=auth_headers(operator_token),
            data={"title": "X", "sourceType": "upload"},
        )
        assert response.status_code == 403


class TestVideoDetail:
    def test_get_video_not_found(self, client, org_and_user, operator_token):
        org, _ = org_and_user
        response = client.get(
            f"/api/v1/orgs/{org.id}/videos/{uuid.uuid4()}",
            headers=auth_headers(operator_token),
        )
        assert response.status_code == 404

    def test_update_video(self, client, db, org_and_user, operator_token):
        from models.core import Video
        org, user = org_and_user
        video = Video(
            id=uuid.uuid4(),
            organization_id=org.id,
            title="Old Title",
            status=VideoStatus.uploaded,
            source_type="upload",
            uploaded_by=user.id,
        )
        db.add(video)
        db.commit()

        response = client.patch(
            f"/api/v1/orgs/{org.id}/videos/{video.id}",
            headers=auth_headers(operator_token),
            json={"title": "New Title"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "New Title"


class TestVideoAnalyze:
    def test_trigger_analyze(self, client, db, org_and_user, operator_token):
        from models.core import Video
        org, user = org_and_user
        video = Video(
            id=uuid.uuid4(),
            organization_id=org.id,
            title="Analyze Me",
            status=VideoStatus.uploaded,
            source_type="upload",
            uploaded_by=user.id,
        )
        db.add(video)
        db.commit()

        with patch("services.video_service.publish_analyze_video", side_effect=ImportError):
            response = client.post(
                f"/api/v1/orgs/{org.id}/videos/{video.id}/analyze",
                headers=auth_headers(operator_token),
                json={"regenerateSegments": True},
            )
        assert response.status_code == 202
        assert response.json()["data"]["status"] == "processing"


class TestSignalConfig:
    def test_get_signal_config(self, client, db, org_and_user, operator_token):
        from models.core import Video
        org, user = org_and_user
        video = Video(
            id=uuid.uuid4(),
            organization_id=org.id,
            title="SigConf Video",
            status=VideoStatus.uploaded,
            source_type="upload",
            uploaded_by=user.id,
        )
        db.add(video)
        db.flush()
        config = VideoSignalConfig(
            id=uuid.uuid4(),
            video_id=video.id,
            confidence_check_enabled=True,
            quiz_enabled=False,
            concept_select_enabled=False,
            summary_enabled=False,
        )
        db.add(config)
        db.commit()

        response = client.get(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/signal-config",
            headers=auth_headers(operator_token),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["confidenceCheckEnabled"] is True

    def test_update_signal_config(self, client, db, org_and_user, operator_token):
        from models.core import Video
        org, user = org_and_user
        video = Video(
            id=uuid.uuid4(),
            organization_id=org.id,
            title="SigConf Video 2",
            status=VideoStatus.uploaded,
            source_type="upload",
            uploaded_by=user.id,
        )
        db.add(video)
        db.flush()
        config = VideoSignalConfig(
            id=uuid.uuid4(),
            video_id=video.id,
            confidence_check_enabled=False,
            quiz_enabled=False,
            concept_select_enabled=False,
            summary_enabled=False,
        )
        db.add(config)
        db.commit()

        response = client.patch(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/signal-config",
            headers=auth_headers(operator_token),
            json={"quizEnabled": True},
        )
        assert response.status_code == 200
        assert response.json()["data"]["quizEnabled"] is True
