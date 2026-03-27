import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from admin.api import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

ADMIN_SECRET = "test-secret"

@pytest.fixture(autouse=True)
def mock_settings():
    with patch("admin.api.settings") as m:
        m.admin_secret = ADMIN_SECRET
        yield m

@pytest.fixture(autouse=True)
def mock_db():
    with patch("admin.api.get_connection") as mock_get, \
         patch("admin.api.release_connection"):
        mock_conn = MagicMock()
        mock_get.return_value = mock_conn
        yield mock_conn

def test_create_key_success(mock_db):
    mock_repo = MagicMock()
    mock_repo.create_key.return_value = {
        "key": "uuid-key", "name": "Test", "created_at": "2026-03-27"
    }
    with patch("admin.api.ApiKeyRepository", return_value=mock_repo):
        resp = client.post(
            "/admin/keys",
            json={"name": "Test"},
            headers={"X-Admin-Secret": ADMIN_SECRET},
        )
    assert resp.status_code == 201
    assert resp.json()["key"] == "uuid-key"

def test_create_key_unauthorized():
    resp = client.post("/admin/keys", json={"name": "Test"})
    assert resp.status_code == 401

def test_list_keys_success(mock_db):
    mock_repo = MagicMock()
    mock_repo.list_keys.return_value = []
    with patch("admin.api.ApiKeyRepository", return_value=mock_repo):
        resp = client.get("/admin/keys", headers={"X-Admin-Secret": ADMIN_SECRET})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_patch_key_success(mock_db):
    mock_repo = MagicMock()
    with patch("admin.api.ApiKeyRepository", return_value=mock_repo):
        resp = client.patch(
            "/admin/keys/uuid-key",
            json={"is_active": False},
            headers={"X-Admin-Secret": ADMIN_SECRET},
        )
    assert resp.status_code == 200

def test_delete_key_soft_deletes(mock_db):
    mock_repo = MagicMock()
    with patch("admin.api.ApiKeyRepository", return_value=mock_repo):
        resp = client.delete(
            "/admin/keys/uuid-key",
            headers={"X-Admin-Secret": ADMIN_SECRET},
        )
    assert resp.status_code == 200
    mock_repo.set_active.assert_called_once_with("uuid-key", False)
