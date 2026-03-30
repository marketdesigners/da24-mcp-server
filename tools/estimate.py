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
        result = {"success": True, **{k: v for k, v in data.items() if k != "total_cbm"}, "cta": CTA}
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
        "이사 짐 목록을 입력하면 짐 부피를 계산하고 소형이사 예상 견적을 반환합니다. "
        "API 키 없이 누구나 사용 가능합니다. "
        "item 키 형식: '카테고리:옵션' — 반드시 아래 정확한 옵션명을 사용해야 합니다. "
        "사용자가 정확한 옵션을 모르면 먼저 옵션을 확인해서 정확한 값으로 변환 후 호출하세요. "
        "침대: 싱글|슈퍼싱글|더블|퀸|킹|싱글(프레임없음)|슈퍼싱글(프레임없음)|더블(프레임없음)|퀸(프레임없음)|킹(프레임없음). "
        "옷장: 100cm미만|100~150cm|150~200cm|200cm초과. "
        "소파: 1~2인용|3~4인용. "
        "세탁기: 통돌이15kg이하|통돌이15kg초과|드럼15kg이하|드럼15kg초과. "
        "냉장고: 미니|일반형|양문형. "
        "에어컨: 스탠드형|벽걸이형. "
        "건조기: 15kg이하|15kg초과. "
        "잔짐박스: 1~6개|6~11개|11~16개|16~21개|21~26개|26~31개|31~36개|36~41개|41~46개|46~51개|51~56개|56~61개. "
        "그 외 카테고리(TV, 모니터, 의자, 화장대, 수납장, 서랍장, 의류관리기, 전자레인지, 정수기, 가스레인지, 비데, 공기청정기, 캣타워, 운동용품)는 옵션 '일반'을 사용하세요. "
        "책장은 '너비(cm)_높이(cm)' 형식: 너비50미만|50~100|100~150|150~200|200초과, 높이50미만|50~100|100~150|150~200|200초과. "
        "책상/테이블: 사각1~2인용|사각3~4인용|원형1~2인용|원형3~4인용. "
        "책상 추가옵션: 독서실1~2인용|독서실3~4인용."
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
