import json
import pytest
from tools.estimate import calculate_cbm, handle_calculate_estimate
from tools.cbm_data import CBM_TABLE


def test_calculate_cbm_single_item():
    total, unknown = calculate_cbm([{"item": "침대:퀸", "quantity": 1}])
    assert total == 2.46
    assert unknown == []


def test_calculate_cbm_multiple_items():
    items = [
        {"item": "침대:퀸", "quantity": 1},       # 2.46
        {"item": "냉장고:일반형", "quantity": 1},  # 0.83
        {"item": "잔짐박스:1~6개", "quantity": 1}, # 0.72
    ]
    total, unknown = calculate_cbm(items)
    assert total == round(2.46 + 0.83 + 0.72, 2)
    assert unknown == []


def test_calculate_cbm_quantity():
    items = [{"item": "의자:등받이", "quantity": 3}]  # 0.48 * 3
    total, unknown = calculate_cbm(items)
    assert total == round(0.48 * 3, 2)
    assert unknown == []


def test_calculate_cbm_unknown_item():
    items = [{"item": "피아노:그랜드", "quantity": 1}]
    total, unknown = calculate_cbm(items)
    assert total == 0.0
    assert "피아노:그랜드" in unknown


def test_handle_calculate_estimate_small_no_packing():
    # CBM 소형(≤7.5) + 포장없음 → 300,000
    items = [{"item": "침대:싱글(프레임없음)", "quantity": 1}]  # 0.6 CBM
    result = json.loads(handle_calculate_estimate(items, need_packing=False))
    assert result["success"] is True
    assert result["estimated_price"] == 300_000
    assert result["recommend_family_moving"] is False
    assert "da24.co.kr" in result["cta"]


def test_handle_calculate_estimate_small_with_packing():
    # CBM 소형(≤7.5) + 포장있음 → 400,000
    items = [{"item": "침대:싱글(프레임없음)", "quantity": 1}]
    result = json.loads(handle_calculate_estimate(items, need_packing=True))
    assert result["estimated_price"] == 400_000


def test_handle_calculate_estimate_large_no_packing():
    # CBM 대형(>7.5) + 포장없음 → 500,000
    # 잔짐박스:36~41개 = 7.02, 냉장고:일반형 = 0.83 → 7.85
    items = [
        {"item": "잔짐박스:36~41개", "quantity": 1},  # 7.02
        {"item": "냉장고:일반형", "quantity": 1},      # 0.83
    ]
    result = json.loads(handle_calculate_estimate(items, need_packing=False))
    assert result["total_cbm"] == round(7.02 + 0.83, 2)
    assert result["estimated_price"] == 500_000


def test_handle_calculate_estimate_large_with_packing():
    # CBM 대형(>7.5) + 포장있음 → 600,000
    items = [
        {"item": "잔짐박스:36~41개", "quantity": 1},
        {"item": "냉장고:일반형", "quantity": 1},
    ]
    result = json.loads(handle_calculate_estimate(items, need_packing=True))
    assert result["estimated_price"] == 600_000


def test_handle_calculate_estimate_recommend_family():
    # CBM > 15 → 가정이사 권장 메시지
    items = [{"item": "잔짐박스:56~61개", "quantity": 1}]  # 10.62
    items += [{"item": "옷장:200cm초과", "quantity": 2}]   # 3.07 * 2 = 6.14
    # total = 10.62 + 6.14 = 16.76
    result = json.loads(handle_calculate_estimate(items))
    assert result["recommend_family_moving"] is True
    assert "message" in result


def test_handle_calculate_estimate_empty_items():
    result = json.loads(handle_calculate_estimate([]))
    assert result["success"] is False


def test_handle_calculate_estimate_unknown_item_warning():
    items = [
        {"item": "냉장고:일반형", "quantity": 1},
        {"item": "피아노:업라이트", "quantity": 1},
    ]
    result = json.loads(handle_calculate_estimate(items))
    assert result["success"] is True
    assert "unknown_items" in result
    assert "피아노:업라이트" in result["unknown_items"]
    assert "warning" in result


def test_cbm_table_has_expected_keys():
    required = ["침대:퀸", "냉장고:일반형", "세탁기:드럼15kg이하", "잔짐박스:1~6개", "소파:3~4인용"]
    for key in required:
        assert key in CBM_TABLE, f"Missing key: {key}"
