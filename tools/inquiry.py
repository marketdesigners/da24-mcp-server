import json
import logging
import httpx
from config import settings
from db.database import get_connection, release_connection
from db.models import ApiKeyRepository

logger = logging.getLogger(__name__)


def build_da24_payload(
    name: str,
    tel: str,
    moving_type: str,
    moving_date: str,
    sido: str = "",
    gugun: str = "",
    sido2: str = "",
    gugun2: str = "",
    email: str = "",
    memo: str = "",
    mkt_agree: bool = False,
) -> dict:
    is_undecided = moving_date == "undecided"
    return {
        "name": name,
        "tel": tel,
        "moving_type": moving_type,
        "moving_date": "" if is_undecided else moving_date,
        "is_moving_date_undecided": is_undecided,
        "sido": sido or "",
        "gugun": gugun or "",
        "sido2": sido2 or "",
        "gugun2": gugun2 or "",
        "email": email or "",
        "memo": memo or "",
        "mkt_agree": mkt_agree,
        "agent_id": "mcp",
    }


async def handle_create_inquiry(
    api_key: str,
    name: str,
    tel: str,
    moving_type: str,
    moving_date: str,
    sido: str = "",
    gugun: str = "",
    sido2: str = "",
    gugun2: str = "",
    email: str = "",
    memo: str = "",
    mkt_agree: bool = False,
) -> str:
    # 1. API 키 검증
    conn = get_connection()
    try:
        repo = ApiKeyRepository(conn)
        key_info = repo.get_active_key(api_key)
    finally:
        release_connection(conn)

    if key_info is None:
        logger.error("Invalid API key attempt: %s...", api_key[:8] if api_key else "")
        return json.dumps({"success": False, "error": "Invalid or inactive API key"})

    # 2. da24 API 호출
    payload = build_da24_payload(
        name=name, tel=tel, moving_type=moving_type, moving_date=moving_date,
        sido=sido, gugun=gugun, sido2=sido2, gugun2=gugun2,
        email=email, memo=memo, mkt_agree=mkt_agree,
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.da24_api_url.rstrip('/')}/move/inquiry",
                json=payload,
            )
    except (httpx.TimeoutException, httpx.NetworkError) as e:
        logger.error("da24 API call failed: %s", str(e))
        return json.dumps({"success": False, "error": "da24 API 호출 실패"})

    if resp.status_code == 201:
        inquiry_id = resp.json().get("idx", "")
        # 3. 사용량 업데이트
        conn2 = get_connection()
        try:
            ApiKeyRepository(conn2).update_usage(api_key)
        finally:
            release_connection(conn2)
        logger.info("Inquiry created: %s by %s", inquiry_id, key_info["name"])
        return json.dumps({"success": True, "inquiry_id": inquiry_id})
    elif resp.status_code == 400:
        error_msg = resp.json().get("error", "알 수 없는 오류")
        logger.error("da24 API 400: %s", error_msg)
        return json.dumps({"success": False, "error": f"접수 실패: {error_msg}"})
    else:
        logger.error("da24 API %d error", resp.status_code)
        return json.dumps({"success": False, "error": "서버 오류"})
