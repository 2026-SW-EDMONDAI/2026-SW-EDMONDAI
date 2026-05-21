"""Contract tests for segment version management API (M2-3)."""
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
from models.segment import Segment, SegmentSet, SegmentSetStatus
from models.video import VideoSignalConfig  # noqa: F401

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
    org = Organization(id=uuid.uuid4(), name="Seg Org", slug="seg-org")
    user = User(id=uuid.uuid4(), email="u@seg.com", name="U", password_hash="h", role="operator")
    db.add_all([org, user])
    db.flush()
    video = Video(
        id=uuid.uuid4(),
        organization_id=org.id,
        title="Segment Video",
        status=VideoStatus.analyzed,
        source_type="upload",
        uploaded_by=user.id,
    )
    db.add(video)
    db.flush()
    ss = SegmentSet(
        id=uuid.uuid4(),
        video_id=video.id,
        version_no=1,
        status=SegmentSetStatus.draft,
        source="auto",
    )
    db.add(ss)
    db.flush()
    segs = [
        Segment(
            id=uuid.uuid4(),
            segment_set_id=ss.id,
            seq_no=i,
            start_ms=(i - 1) * 60000,
            end_ms=i * 60000,
            title=f"Segment {i}",
            source_type="auto",
        )
        for i in range(1, 4)
    ]
    db.add_all(segs)
    db.commit()
    token = create_access_token({"sub": str(user.id), "orgId": str(org.id), "orgRole": "operator"})
    return org, video, ss, segs, token


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- SegmentSet tests ----------

class TestSegmentSetList:
    def test_list_sets(self, client, base_data):
        org, video, ss, _, token = base_data
        resp = client.get(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/segment-sets",
            headers=headers(token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_get_latest_set(self, client, base_data):
        org, video, ss, _, token = base_data
        resp = client.get(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/segment-sets/latest",
            headers=headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["versionNo"] == 1


class TestSegmentSetClone:
    def test_clone_creates_new_draft(self, client, base_data):
        org, video, ss, _, token = base_data
        resp = client.post(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/segment-sets/{ss.id}/clone",
            headers=headers(token),
            json={"notes": "clone test"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["versionNo"] == 2
        assert data["status"] == "draft"


class TestSegmentSetFinalize:
    def test_finalize_draft(self, client, base_data):
        org, video, ss, _, token = base_data
        resp = client.post(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/segment-sets/{ss.id}/finalize",
            headers=headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "finalized"

    def test_finalize_already_finalized_returns_409(self, client, db, base_data):
        org, video, ss, _, token = base_data
        ss.status = SegmentSetStatus.finalized
        db.commit()

        resp = client.post(
            f"/api/v1/orgs/{org.id}/videos/{video.id}/segment-sets/{ss.id}/finalize",
            headers=headers(token),
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "SEGMENT_SET_NOT_DRAFT"


# ---------- Segment tests ----------

class TestSegmentList:
    def test_list_segments(self, client, base_data):
        org, _, ss, segs, token = base_data
        resp = client.get(
            f"/api/v1/orgs/{org.id}/segment-sets/{ss.id}/segments",
            headers=headers(token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 3


class TestSegmentUpdate:
    def test_update_segment(self, client, base_data):
        org, _, ss, segs, token = base_data
        seg = segs[0]
        resp = client.patch(
            f"/api/v1/orgs/{org.id}/segment-sets/{ss.id}/segments/{seg.id}",
            headers=headers(token),
            json={"title": "Updated Title", "topic": "math"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated Title"
        assert resp.json()["data"]["sourceType"] == "edited"

    def test_update_finalized_segment_returns_409(self, client, db, base_data):
        org, _, ss, segs, token = base_data
        ss.status = SegmentSetStatus.finalized
        db.commit()

        resp = client.patch(
            f"/api/v1/orgs/{org.id}/segment-sets/{ss.id}/segments/{segs[0].id}",
            headers=headers(token),
            json={"title": "Should Fail"},
        )
        assert resp.status_code == 409


class TestSegmentSplit:
    def test_split_segment(self, client, base_data):
        org, _, ss, segs, token = base_data
        seg = segs[0]  # 0 - 60000
        resp = client.post(
            f"/api/v1/orgs/{org.id}/segment-sets/{ss.id}/segments/{seg.id}/split",
            headers=headers(token),
            json={"splitAtMs": 30000},
        )
        assert resp.status_code == 201
        new_segs = resp.json()["data"]["newSegments"]
        assert len(new_segs) == 2
        assert new_segs[0]["endMs"] == 30000
        assert new_segs[1]["startMs"] == 30000

    def test_split_out_of_range_returns_422(self, client, base_data):
        org, _, ss, segs, token = base_data
        seg = segs[0]  # 0 - 60000
        resp = client.post(
            f"/api/v1/orgs/{org.id}/segment-sets/{ss.id}/segments/{seg.id}/split",
            headers=headers(token),
            json={"splitAtMs": 999999},
        )
        assert resp.status_code == 422


class TestSegmentMerge:
    def test_merge_contiguous(self, client, base_data):
        org, _, ss, segs, token = base_data
        resp = client.post(
            f"/api/v1/orgs/{org.id}/segment-sets/{ss.id}/segments/merge",
            headers=headers(token),
            json={"segmentIds": [str(segs[0].id), str(segs[1].id)]},
        )
        assert resp.status_code == 201
        merged = resp.json()["data"]["mergedSegment"]
        assert merged["startMs"] == 0
        assert merged["endMs"] == 120000

    def test_merge_non_contiguous_returns_422(self, client, base_data):
        org, _, ss, segs, token = base_data
        resp = client.post(
            f"/api/v1/orgs/{org.id}/segment-sets/{ss.id}/segments/merge",
            headers=headers(token),
            json={"segmentIds": [str(segs[0].id), str(segs[2].id)]},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "SEGMENT_MERGE_NOT_CONTIGUOUS"
