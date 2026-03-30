# tests/test_rest_api.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_rest_estimate_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "total_cbm": 4.02,
            "estimated_price": 300000,
            "need_packing": False,
            "recommend_family_moving": False,
        }
    }

    with patch("tools.estimate.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/rest/estimate",
                json={"items": [{"item": "침대:퀸", "quantity": 1}], "need_packing": False},
            )

    mock_client.post.assert_called_once()

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "total_cbm" not in data
    assert data["estimated_price"] == 300000
    assert isinstance(data.get("cta"), str)
    assert "da24.co.kr" in data["cta"]


@pytest.mark.asyncio
async def test_rest_estimate_empty_items():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/rest/estimate",
            json={"items": []},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "비어 있습니다" in data["error"]


@pytest.mark.asyncio
async def test_rest_inquiry_missing_api_key():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/rest/inquiry",
            json={
                "name": "홍길동",
                "tel": "010-1234-5678",
                "moving_type": "가정이사",
                "moving_date": "2026-05-10",
                "sido": "서울",
                "gugun": "강남구",
                "sido2": "경기",
                "gugun2": "성남시",
            },
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_rest_inquiry_invalid_api_key():
    with patch("tools.inquiry.get_connection"), \
         patch("tools.inquiry.release_connection"), \
         patch("tools.inquiry.ApiKeyRepository") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo.get_active_key.return_value = None
        mock_repo_cls.return_value = mock_repo

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/rest/inquiry",
                json={
                    "name": "홍길동",
                    "tel": "010-1234-5678",
                    "moving_type": "가정이사",
                    "moving_date": "2026-05-10",
                    "sido": "서울",
                    "gugun": "강남구",
                    "sido2": "경기",
                    "gugun2": "성남시",
                },
                headers={"X-API-Key": "invalid-key"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Invalid or inactive API key" in data["error"]


@pytest.mark.asyncio
async def test_rest_inquiry_success():
    mock_da24_resp = MagicMock()
    mock_da24_resp.status_code = 201
    mock_da24_resp.json.return_value = {"idx": "12345"}

    with patch("tools.inquiry.get_connection"), \
         patch("tools.inquiry.release_connection"), \
         patch("tools.inquiry.ApiKeyRepository") as mock_repo_cls, \
         patch("tools.inquiry.httpx.AsyncClient") as mock_client_cls:

        mock_repo = MagicMock()
        mock_repo.get_active_key.return_value = {"name": "test-partner"}
        mock_repo.update_usage.return_value = None
        mock_repo_cls.return_value = mock_repo

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_da24_resp)
        mock_client_cls.return_value = mock_client

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/rest/inquiry",
                json={
                    "name": "홍길동",
                    "tel": "010-1234-5678",
                    "moving_type": "가정이사",
                    "moving_date": "2026-05-10",
                    "sido": "서울",
                    "gugun": "강남구",
                    "sido2": "경기",
                    "gugun2": "성남시",
                },
                headers={"X-API-Key": "valid-key"},
            )

    mock_client.post.assert_called_once()

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["inquiry_id"] == "12345"
