# rest/api.py
import json
import logging

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from tools.estimate import handle_calculate_estimate
from tools.inquiry import handle_create_inquiry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rest", tags=["REST API"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ---------- Request models ----------

class EstimateItem(BaseModel):
    item: str
    quantity: int = 1


class EstimateRequest(BaseModel):
    items: list[EstimateItem]
    need_packing: bool = False


class InquiryRequest(BaseModel):
    name: str
    tel: str
    moving_type: str
    moving_date: str
    sido: str
    gugun: str
    sido2: str
    gugun2: str
    email: str = ""
    memo: str = ""
    mkt_agree: bool = False


# ---------- Endpoints ----------

@router.post("/estimate", summary="이사 견적 계산 (인증 불필요)")
async def estimate(body: EstimateRequest):
    raw = await handle_calculate_estimate(
        items=[i.model_dump() for i in body.items],
        need_packing=body.need_packing,
    )
    return JSONResponse(content=json.loads(raw))


@router.post("/inquiry", summary="이사 접수 (X-API-Key 필요)")
async def inquiry(
    body: InquiryRequest,
    api_key: str = Security(api_key_header),
):
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-Key header missing")
    raw = await handle_create_inquiry(
        api_key=api_key,
        name=body.name,
        tel=body.tel,
        moving_type=body.moving_type,
        moving_date=body.moving_date,
        sido=body.sido,
        gugun=body.gugun,
        sido2=body.sido2,
        gugun2=body.gugun2,
        email=body.email,
        memo=body.memo,
        mkt_agree=body.mkt_agree,
    )
    return JSONResponse(content=json.loads(raw))
