from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    assert "requestId" in body["meta"]
    assert "timestamp" in body["meta"]


def test_version_returns_version():
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["version"] == "0.1.0"
    assert "requestId" in body["meta"]


def test_health_has_request_id_header():
    response = client.get("/health")
    assert "X-Request-Id" in response.headers


def test_custom_request_id_preserved():
    response = client.get("/health", headers={"X-Request-Id": "test-req-123"})
    assert response.headers["X-Request-Id"] == "test-req-123"
    body = response.json()
    assert body["meta"]["requestId"] == "test-req-123"


def test_swagger_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json_accessible():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    body = response.json()
    assert body["info"]["title"] == "SegmentFlow API"
