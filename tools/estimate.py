import json
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

CTA = (
    "직접 접수하고 싶으시다면 다이사(https://da24.co.kr)에서 간편하게 신청하세요! "
    "여러 업체의 견적을 한 번에 비교할 수 있습니다."
)


async def handle_calculate_estimate(items: list[dict], need_packing: bool = False) -> str:
    """
    da24 /da24/estimate API를 호출해 CBM 및 예상 견적을 반환합니다.
    API 키 불필요 — 공개 도구.
    """
    if not items:
        return json.dumps({"success": False, "error": "items가 비어 있습니다."}, ensure_ascii=False)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.da24_api_url.rstrip('/')}/da24/estimate",
                json={"items": items, "need_packing": need_packing},
            )
    except httpx.RequestError as e:
        logger.error("estimate API call failed: %s", str(e))
        return json.dumps({"success": False, "error": "견적 계산 API 호출 실패"}, ensure_ascii=False)

    if resp.status_code == 200:
        try:
            data = resp.json().get("data", {})
        except Exception:
            data = {}
        result = {"success": True, **data, "cta": CTA}
        logger.info("estimate: cbm=%s price=%s", data.get("total_cbm"), data.get("estimated_price"))
        return json.dumps(result, ensure_ascii=False)
    else:
        try:
            error_msg = resp.json().get("error", "견적 계산 실패")
        except Exception:
            error_msg = "견적 계산 실패"
        logger.error("estimate API %d: %s", resp.status_code, error_msg)
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# MCP tool schema (main.py에서 import)
# ---------------------------------------------------------------------------
ESTIMATE_TOOL_SCHEMA = {
    "name": "calculate_estimate",
    "description": (
        "이사 짐 목록을 입력하면 CBM(부피)을 계산하고 소형이사 예상 견적을 반환합니다. "
        "API 키 없이 누구나 사용 가능합니다. "
        "item 키 형식: '카테고리:옵션' (예: '침대:퀸', '냉장고:일반형', '잔짐박스:1~6개'). "
        "지원 카테고리: 침대, 옷장, 책장, 책상, 의자, 테이블, 소파, 화장대, 수납장, 서랍장, "
        "TV, 모니터, 세탁기, 건조기, 에어컨, 냉장고, 의류관리기, "
        "전자레인지, 정수기, 가스레인지, 비데, 공기청정기, 캣타워, 운동용품, 잔짐박스."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "description": "짐 항목 목록",
                "items": {
                    "type": "object",
                    "properties": {
                        "item": {
                            "type": "string",
                            "description": "짐 항목 키 (예: '침대:퀸', '냉장고:일반형')",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "수량 (기본값 1)",
                            "default": 1,
                        },
                    },
                    "required": ["item"],
                },
            },
            "need_packing": {
                "type": "boolean",
                "description": "포장 서비스 필요 여부 (기본값 false)",
                "default": False,
            },
        },
        "required": ["items"],
    },
}
