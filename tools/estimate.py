import json
import logging
from tools.cbm_data import CBM_TABLE, PRICE_TABLE, CBM_THRESHOLD_SMALL, CBM_THRESHOLD_FAMILY

logger = logging.getLogger(__name__)


def calculate_cbm(items: list[dict]) -> tuple[float, list[str]]:
    """
    items: [{"item": "침대:퀸", "quantity": 1}, ...]
    Returns (total_cbm, unknown_items)
    """
    total = 0.0
    unknown = []
    for entry in items:
        key = entry.get("item", "").strip()
        qty = int(entry.get("quantity", 1))
        cbm = CBM_TABLE.get(key)
        if cbm is None:
            unknown.append(key)
        else:
            total += cbm * qty
    return round(total, 2), unknown


def handle_calculate_estimate(items: list[dict], need_packing: bool = False) -> str:
    """
    짐 목록을 받아 CBM 합산 후 소형이사 예상 견적을 반환합니다.
    API 키 불필요 — 공개 도구.
    """
    if not items:
        return json.dumps({"success": False, "error": "items가 비어 있습니다."}, ensure_ascii=False)

    total_cbm, unknown = calculate_cbm(items)

    # 알 수 없는 항목이 있어도 결과는 반환하되 경고 포함
    price = PRICE_TABLE.get((total_cbm > CBM_THRESHOLD_SMALL, need_packing))

    recommend_family = total_cbm > CBM_THRESHOLD_FAMILY

    result: dict = {
        "success": True,
        "total_cbm": total_cbm,
        "estimated_price": price,
        "need_packing": need_packing,
        "recommend_family_moving": recommend_family,
    }
    if recommend_family:
        result["message"] = (
            f"짐량({total_cbm} CBM)이 {CBM_THRESHOLD_FAMILY} CBM을 초과하여 "
            "가정이사를 권장합니다. 소형이사 견적은 참고용입니다."
        )
    if unknown:
        result["unknown_items"] = unknown
        result["warning"] = "인식되지 않은 항목은 CBM 계산에서 제외되었습니다."

    result["cta"] = (
        "직접 접수하고 싶으시다면 다이사(https://da24.co.kr)에서 간편하게 신청하세요! "
        "여러 업체의 견적을 한 번에 비교할 수 있습니다."
    )

    logger.info("estimate: cbm=%.2f price=%s packing=%s", total_cbm, price, need_packing)
    return json.dumps(result, ensure_ascii=False)


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
