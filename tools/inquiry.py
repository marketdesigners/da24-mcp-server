import json
import logging
import httpx
from config import settings
from db.database import get_connection, release_connection
from db.models import ApiKeyRepository

logger = logging.getLogger(__name__)


MOVING_TYPE_MAP = {
    "가정이사": "가정",
    "원룸이사": "원룸",
    "사무실이사": "사무실",
    "보관이사": "가정",
    "용달이사": "원룸",
}


def split_tel(tel: str) -> tuple[str, str, str]:
    parts = tel.replace("-", "").replace(" ", "")
    if len(parts) == 11:  # 010-XXXX-XXXX
        return parts[0:3], parts[3:7], parts[7:11]
    elif len(parts) == 10:  # 02-XXXX-XXXX
        return parts[0:2], parts[2:6], parts[6:10]
    return parts, "", ""


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
    mapped_moving_type = MOVING_TYPE_MAP.get(moving_type, moving_type)
    phone1, phone2, phone3 = split_tel(tel)
    return {
        "name": name,
        "phone1": phone1,
        "phone2": phone2,
        "phone3": phone3,
        "moving_type": mapped_moving_type,
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
    sido: str,
    gugun: str,
    sido2: str,
    gugun2: str,
    email: str = "",
    memo: str = "",
    mkt_agree: bool = False,
) -> str:
    # 1. 필수 필드 검증
    missing = [f for f, v in [("sido", sido), ("gugun", gugun), ("sido2", sido2), ("gugun2", gugun2)] if not v]
    if missing:
        return json.dumps({"success": False, "error": f"필수 항목 누락: {', '.join(missing)}"})

    # 2. API 키 검증
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
                f"{settings.da24_api_url.rstrip('/')}/da24/inquiry",
                json=payload,
            )
    except httpx.RequestError as e:
        logger.error("da24 API call failed: %s", str(e))
        return json.dumps({"success": False, "error": "da24 API 호출 실패"})

    if resp.status_code == 201:
        try:
            inquiry_id = resp.json().get("idx", "")
        except Exception:
            inquiry_id = ""
        # 3. 사용량 업데이트
        conn2 = get_connection()
        try:
            ApiKeyRepository(conn2).update_usage(api_key)
        finally:
            release_connection(conn2)
        logger.info("Inquiry created: %s by %s", inquiry_id, key_info["name"])
        return json.dumps({"success": True, "inquiry_id": inquiry_id})
    elif resp.status_code == 400:
        try:
            error_msg = resp.json().get("error", "알 수 없는 오류")
        except Exception:
            error_msg = "알 수 없는 오류"
        logger.error("da24 API 400: %s", error_msg)
        return json.dumps({"success": False, "error": f"접수 실패: {error_msg}"})
    else:
        logger.error("da24 API %d error", resp.status_code)
        return json.dumps({"success": False, "error": "서버 오류"})
