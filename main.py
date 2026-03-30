"""
da24 MCP Server — main entry point.

Architecture:
- FastAPI app with admin router at /admin
- MCP StreamableHTTP transport at /mcp  (claude.ai Connector 등 최신 클라이언트)
- MCP SSE transport at /sse + /messages/ (Claude Code 등 레거시 클라이언트)
- X-API-Key header는 각 transport 연결 시 contextvars.ContextVar에 저장
"""

import contextvars
import logging
from contextlib import asynccontextmanager

import mcp.types as types
import uvicorn
from fastapi import FastAPI
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Mount, Route

import db.database

from admin.api import router as admin_router
from rest.api import router as rest_router
from config import settings
from tools.inquiry import handle_create_inquiry
from tools.estimate import handle_calculate_estimate, ESTIMATE_TOOL_SCHEMA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ContextVar: X-API-Key per connection
# ---------------------------------------------------------------------------
_api_key_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "_api_key_ctx", default=""
)

# ---------------------------------------------------------------------------
# Low-level MCP Server
# ---------------------------------------------------------------------------
mcp_server = Server("da24-mcp-server")


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(**ESTIMATE_TOOL_SCHEMA),
        types.Tool(
            name="create_inquiry",
            description=(
                "사용자가 요청한 이사 견적 문의를 da24 플랫폼에 접수합니다. "
                "필수: name, tel, moving_type, moving_date, sido, gugun, sido2, gugun2. "
                "moving_type: '가정이사'|'원룸이사'|'사무실이사'|'보관이사'|'용달이사'. "
                "moving_date: 'YYYY-MM-DD' 또는 'undecided'. "
                "주소가 동 단위로만 주어진 경우 sido/gugun을 최대한 유추하여 입력하세요."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "고객 이름"},
                    "tel": {"type": "string", "description": "연락처 (숫자, 하이픈 허용)"},
                    "moving_type": {
                        "type": "string",
                        "enum": ["가정이사", "원룸이사", "사무실이사", "보관이사", "용달이사"],
                        "description": "이사 유형",
                    },
                    "moving_date": {
                        "type": "string",
                        "description": "이사 날짜 (YYYY-MM-DD) 또는 'undecided'",
                    },
                    "sido": {"type": "string", "description": "출발지 시/도"},
                    "gugun": {"type": "string", "description": "출발지 구/군"},
                    "sido2": {"type": "string", "description": "도착지 시/도"},
                    "gugun2": {"type": "string", "description": "도착지 구/군"},
                    "email": {"type": "string", "description": "이메일 (선택)"},
                    "memo": {"type": "string", "description": "메모 (선택)"},
                    "mkt_agree": {
                        "type": "boolean",
                        "description": "마케팅 수신 동의 (기본 false)",
                    },
                },
                "required": ["name", "tel", "moving_type", "moving_date", "sido", "gugun", "sido2", "gugun2"],
            },
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "calculate_estimate":
        result = await handle_calculate_estimate(
            items=arguments.get("items", []),
            need_packing=arguments.get("need_packing", False),
        )
        return [types.TextContent(type="text", text=result)]

    if name != "create_inquiry":
        raise ValueError(f"Unknown tool: {name}")

    api_key = _api_key_ctx.get()
    if not api_key:
        return [
            types.TextContent(
                type="text",
                text='{"success": false, "error": "X-API-Key header missing"}',
            )
        ]

    result = await handle_create_inquiry(
        api_key=api_key,
        name=arguments["name"],
        tel=arguments["tel"],
        moving_type=arguments["moving_type"],
        moving_date=arguments["moving_date"],
        sido=arguments.get("sido", ""),
        gugun=arguments.get("gugun", ""),
        sido2=arguments.get("sido2", ""),
        gugun2=arguments.get("gugun2", ""),
        email=arguments.get("email", ""),
        memo=arguments.get("memo", ""),
        mkt_agree=arguments.get("mkt_agree", False),
    )
    return [types.TextContent(type="text", text=result)]


# ---------------------------------------------------------------------------
# StreamableHTTP transport (claude.ai Connector 등 최신 MCP 클라이언트)
# ---------------------------------------------------------------------------
session_manager = StreamableHTTPSessionManager(app=mcp_server)


async def handle_streamable_http(request: Request) -> Response:
    api_key = request.headers.get("x-api-key", "") or request.query_params.get("api_key", "")
    token = _api_key_ctx.set(api_key)
    try:
        await session_manager.handle_request(
            request.scope, request.receive, request._send  # type: ignore[attr-defined]
        )
    finally:
        _api_key_ctx.reset(token)
    return Response()


# ---------------------------------------------------------------------------
# SSE transport (Claude Code 등 레거시 MCP 클라이언트)
# ---------------------------------------------------------------------------
sse_transport = SseServerTransport("/messages/")


async def handle_sse(request: Request) -> Response:
    api_key = request.headers.get("x-api-key", "") or request.query_params.get("api_key", "")
    token = _api_key_ctx.set(api_key)
    try:
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send  # type: ignore[attr-defined]
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )
    finally:
        _api_key_ctx.reset(token)
    return Response()


# ---------------------------------------------------------------------------
# FastAPI app assembly
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app):
    db.database.init_pool()
    async with session_manager.run():
        yield


app = FastAPI(title="da24 MCP Server", lifespan=lifespan)

app.include_router(admin_router)
app.include_router(rest_router)


@app.get("/.well-known/openai-apps-challenge", include_in_schema=False)
async def openai_apps_challenge():
    return PlainTextResponse("EuIqsgSY0mkr7lShUfQJwyfORakTP-4_qPrW6z70x-o")

mcp_routes = [
    Route("/", endpoint=handle_streamable_http, methods=["GET", "POST"]),
    Route("/sse", endpoint=handle_sse, methods=["GET"]),
    Mount("/messages/", app=sse_transport.handle_post_message),
]

app.mount("/", app=Starlette(routes=mcp_routes))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.mcp_port)
