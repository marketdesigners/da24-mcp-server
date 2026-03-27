import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from tools.estimate import handle_calculate_estimate


@pytest.mark.asyncio
async def test_handle_calculate_estimate_success():
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

        result = json.loads(await handle_calculate_estimate(
            items=[{"item": "침대:퀸", "quantity": 1}],
            need_packing=False,
        ))

    assert result["success"] is True
    assert result["total_cbm"] == 4.02
    assert result["estimated_price"] == 300000
    assert "da24.co.kr" in result["cta"]


@pytest.mark.asyncio
async def test_handle_calculate_estimate_recommend_family():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "total_cbm": 16.76,
            "estimated_price": 600000,
            "need_packing": False,
            "recommend_family_moving": True,
            "message": "짐량(16.76 CBM)이 15.0 CBM을 초과하여 가정이사를 권장합니다.",
        }
    }

    with patch("tools.estimate.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = json.loads(await handle_calculate_estimate(
            items=[{"item": "옷장:200cm초과", "quantity": 2}],
        ))

    assert result["success"] is True
    assert result["recommend_family_moving"] is True


@pytest.mark.asyncio
async def test_handle_calculate_estimate_empty_items():
    result = json.loads(await handle_calculate_estimate([]))
    assert result["success"] is False
    assert "비어 있습니다" in result["error"]


@pytest.mark.asyncio
async def test_handle_calculate_estimate_api_error():
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "잘못된 요청"}

    with patch("tools.estimate.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = json.loads(await handle_calculate_estimate(
            items=[{"item": "침대:퀸", "quantity": 1}],
        ))

    assert result["success"] is False


@pytest.mark.asyncio
async def test_handle_calculate_estimate_timeout():
    with patch("tools.estimate.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client_cls.return_value = mock_client

        result = json.loads(await handle_calculate_estimate(
            items=[{"item": "침대:퀸", "quantity": 1}],
        ))

    assert result["success"] is False
    assert "호출 실패" in result["error"]
