import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tools.inquiry import build_da24_payload, handle_create_inquiry

def test_build_payload_basic():
    payload = build_da24_payload(
        name="홍길동",
        tel="010-1234-5678",
        moving_type="가정이사",
        moving_date="2026-04-01",
    )
    assert payload["name"] == "홍길동"
    assert payload["tel"] == "010-1234-5678"
    assert payload["moving_type"] == "가정이사"
    assert payload["moving_date"] == "2026-04-01"
    assert payload["agent_id"] == "mcp"
    assert payload["is_moving_date_undecided"] is False

def test_build_payload_undecided_date():
    payload = build_da24_payload(
        name="홍길동",
        tel="010-1234-5678",
        moving_type="원룸이사",
        moving_date="undecided",
    )
    assert payload["moving_date"] == ""
    assert payload["is_moving_date_undecided"] is True

def test_build_payload_optional_fields_empty():
    payload = build_da24_payload(
        name="홍길동",
        tel="010-1234-5678",
        moving_type="사무실이사",
        moving_date="2026-04-01",
    )
    assert payload["sido"] == ""
    assert payload["gugun"] == ""
    assert payload["sido2"] == ""
    assert payload["gugun2"] == ""
    assert payload["email"] == ""
    assert payload["memo"] == ""
    assert payload["mkt_agree"] is False

@pytest.mark.asyncio
async def test_handle_create_inquiry_success():
    mock_conn = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_active_key.return_value = {"key": "k", "name": "Svc", "usage_count": 0}

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"idx": "enc-idx-123"}

    with patch("tools.inquiry.get_connection", return_value=mock_conn), \
         patch("tools.inquiry.release_connection"), \
         patch("tools.inquiry.ApiKeyRepository", return_value=mock_repo), \
         patch("tools.inquiry.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await handle_create_inquiry(
            api_key="valid-key",
            name="홍길동",
            tel="010-1234-5678",
            moving_type="가정이사",
            moving_date="2026-04-01",
        )

    data = json.loads(result)
    assert data["success"] is True
    assert data["inquiry_id"] == "enc-idx-123"

@pytest.mark.asyncio
async def test_handle_create_inquiry_invalid_key():
    mock_conn = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_active_key.return_value = None

    with patch("tools.inquiry.get_connection", return_value=mock_conn), \
         patch("tools.inquiry.release_connection"), \
         patch("tools.inquiry.ApiKeyRepository", return_value=mock_repo):
        result = await handle_create_inquiry(
            api_key="bad-key",
            name="홍길동",
            tel="010-1234-5678",
            moving_type="가정이사",
            moving_date="2026-04-01",
        )

    data = json.loads(result)
    assert data["success"] is False
    assert "Invalid" in data["error"]
