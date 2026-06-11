import uuid

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.auth import create_access_token, hash_password, verify_password
from core.database import get_db
from core.exceptions import AppException
from main import app

client = TestClient(app)


# --- Unit tests for auth utilities ---


def test_hash_and_verify_password():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_token():
    from core.auth import decode_access_token

    token = create_access_token(
        user_id="user-1", org_id="org-1", org_role="operator"
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["orgId"] == "org-1"
    assert payload["orgRole"] == "operator"


# --- Integration tests for /auth/login ---


def _make_mock_user(user_id=None, email="test@example.com", password="secret123"):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = email
    user.password_hash = hash_password(password)
    return user


def _make_mock_membership(user_id, org_id=None, org_role="operator"):
    m = MagicMock()
    m.user_id = user_id
    m.organization_id = org_id or uuid.uuid4()
    m.org_role = org_role
    return m


def _override_db(mock_db):
    def _get_db_override():
        yield mock_db
    app.dependency_overrides[get_db] = _get_db_override


def test_login_success():
    user = _make_mock_user()
    membership = _make_mock_membership(user.id)

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [user, membership]
    _override_db(mock_db)

    try:
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "secret123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "accessToken" in body["data"]
        assert body["data"]["tokenType"] == "bearer"
    finally:
        app.dependency_overrides.clear()


def test_login_wrong_password():
    user = _make_mock_user()

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = user
    _override_db(mock_db)

    try:
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    finally:
        app.dependency_overrides.clear()


def test_login_user_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    _override_db(mock_db)

    try:
        response = client.post(
            "/auth/login",
            json={"email": "noone@example.com", "password": "secret123"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


# --- Tests for auth dependencies ---


def test_role_guard():
    from core.deps import RoleGuard

    admin_guard = RoleGuard(["admin"])

    # Valid role
    result = admin_guard({"orgRole": "admin"})
    assert result["orgRole"] == "admin"

    # Invalid role
    with pytest.raises(AppException) as exc:
        admin_guard({"orgRole": "analyst"})
    assert exc.value.status_code == 403
