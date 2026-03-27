from unittest.mock import MagicMock, patch
import pytest
from db.models import ApiKeyRepository

@pytest.fixture
def mock_conn():
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=MagicMock())
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn

def test_get_active_key_returns_key(mock_conn):
    repo = ApiKeyRepository(mock_conn)
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = ("test-key", "Test Service", 1, 5)

    result = repo.get_active_key("test-key")

    assert result is not None
    assert result["key"] == "test-key"
    assert result["name"] == "Test Service"

def test_get_active_key_returns_none_for_missing(mock_conn):
    repo = ApiKeyRepository(mock_conn)
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = repo.get_active_key("nonexistent-key")
    assert result is None

def test_create_key_returns_dict(mock_conn):
    repo = ApiKeyRepository(mock_conn)
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = ("uuid-key", "My Service", "2026-03-27 00:00:00")

    result = repo.create_key("My Service")

    assert result["key"] == "uuid-key"
    assert result["name"] == "My Service"

def test_update_usage_increments_count(mock_conn):
    repo = ApiKeyRepository(mock_conn)
    # Should not raise
    repo.update_usage("test-key")
    mock_conn.commit.assert_called_once()

def test_set_active_status(mock_conn):
    repo = ApiKeyRepository(mock_conn)
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 1
    result = repo.set_active("test-key", False)
    assert result is True
    mock_conn.commit.assert_called_once()
